"""Supervise a pinned llama.cpp worker on the router GPU pair."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from gpu_transport_health import require_host_staged
from inference_swap_guard import GPU_FREE_MIB, WorkerWatch, read_cgroup
from lifecycle_telemetry import LifecycleLog
from profile_catalog import budget_limit_string, host_ram_reserve_gib, require_host_capacity, worker_budget
from storage_policy import verify_storage

ROOT = Path(__file__).resolve().parents[1]


def read_private_key(path):
    if path.stat().st_mode & 0o077:
        raise RuntimeError('API key must be owner-only')
    key = path.read_text().strip()
    if not key:
        raise RuntimeError('API key must not be empty')
    return key


def native_placement_proof(path, context):
    log = path.read_text(errors='replace')
    return bool(re.search(r'n_ctx(?:_slot)?\s*=\s*' + str(context) + r'\b', log)) and all(
        re.search(r'CUDA' + str(i) + r'.*model buffer size', log) for i in (0, 1))


def verify_runtime_files(root, pins):
    for name, expected in [(pins['binary'], pins['binary_sha256']), *pins['runtime_files_sha256'].items()]:
        with (root / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                raise ValueError('Native runtime SHA-256 mismatch: ' + name)


def verify_receipts(folder, receipts, expected_files):
    if sorted(row['file'] for row in receipts) != sorted(expected_files):
        raise ValueError('Unexpected native checkpoint receipts')
    for row in receipts:
        if (row['publisher_sha256_matched'] is not True or not re.fullmatch('[a-f0-9]{64}', row['sha256'])
                or (folder / row['file']).stat().st_size != row['bytes']):
            raise ValueError('Native checkpoint receipt/size mismatch: ' + row['file'])


def worker_environment(library_dirs):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0,1', CUDA_DEVICE_ORDER='PCI_BUS_ID',
               NCCL_P2P_DISABLE='1', PYTHONUNBUFFERED='1', HF_HUB_OFFLINE='1')
    env.pop('GGML_CUDA_P2P', None)
    paths = [str(path) for path in library_dirs]
    if env.get('LD_LIBRARY_PATH'):
        paths.append(env['LD_LIBRARY_PATH'])
    env['LD_LIBRARY_PATH'] = os.pathsep.join(paths)
    return env


def main(*, work, profile, manifest, command_builder, receipt_files, library_dirs):
    os.umask(0o077)
    work.mkdir(parents=True, exist_ok=True)
    require_host_staged()
    require_host_capacity(profile)
    group = next(line.split('::', 1)[1] for line in Path('/proc/self/cgroup').read_text().splitlines()
                 if line.startswith('0::'))
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    budget = worker_budget(profile)
    if not group.endswith('/llm-router-worker.service') or any(
            (base / name).read_text().strip() != budget_limit_string(budget[field])
            for name, field in [('memory.high', 'high'), ('memory.max', 'max'), ('memory.swap.max', 'swap')]):
        raise RuntimeError('Start llama.cpp through the router with the selected worker budget')
    pins = json.loads(manifest.read_text())
    command = command_builder(profile, pins)
    verify_runtime_files(ROOT, pins)
    if pins['checkpoint_directory'] != profile['storage']['checkpoint_directory']:
        raise ValueError('Native checkpoint directory differs from registry')
    verify_storage(profile)
    verify_receipts(ROOT / pins['checkpoint_directory'], pins['files'], receipt_files)
    key = read_private_key(ROOT / 'data/local-api-key')
    watch = WorkerWatch(base, profile['id'], key, evidence=work / 'swap-guard.jsonl')
    life = LifecycleLog(profile['id'], path=None, interval=2)
    host_floor = host_ram_reserve_gib(profile) * 1024**2
    print('Pinned command: ' + json.dumps(command), flush=True)
    engine_log = work / 'engine.log'
    with engine_log.open('w') as log:
        child = subprocess.Popen(command, env=worker_environment(library_dirs), start_new_session=True,
                                 stdout=log, stderr=subprocess.STDOUT)
    stopping = False

    def stop(*args):
        nonlocal stopping
        stopping = True
        life.set_phase('stopping')
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)

    reason = None
    bad = loading_bad = 0
    placement_verified = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        life.start()
        while child.poll() is None and not stopping:
            reason = watch.step()
            if stopping:
                break
            life.set_phase(watch.last_phase)
            pressure = read_cgroup(base)['pressure_pct']
            if not math.isfinite(pressure):
                raise ValueError('Invalid pressure telemetry')
            available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                             if line.startswith('MemAvailable:'))
            raw = subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu,memory.free',
                                           '--format=csv,noheader,nounits'], text=True, timeout=10)
            cards = [[float(v) for v in line.split(',')] for line in raw.splitlines()]
            if len(cards) != 2 or any(len(card) != 2 or not all(map(math.isfinite, card)) for card in cards):
                raise ValueError('Invalid pair resource telemetry')
            low = available < host_floor or any(temp >= 100 or free < GPU_FREE_MIB for temp, free in cards)
            bad = bad + 1 if low else 0
            loading_bad = loading_bad + 1 if watch.last_phase == 'loading' and pressure > 15 else 0
            if watch.ready and not placement_verified:
                placement_verified = native_placement_proof(engine_log, profile['allocated_context'])
                if not placement_verified:
                    reason = reason or 'Native two-GPU placement/configured context proof missing'
            if loading_bad >= 3 or bad >= 3:
                reason = reason or 'Sustained loading pressure or host/temperature/GPU-headroom limit reached'
            state = dict(phase=watch.last_phase, ready=watch.ready, child_pid=child.pid, guard_reason=reason,
                         host_available_KiB=available, GPU_temp_free_MiB=cards, bad_samples=bad,
                         loading_bad_samples=loading_bad, loading_PSI_percent=pressure, time=time.time())
            tmp = work / 'worker-status.tmp'
            tmp.write_text(json.dumps(state))
            tmp.replace(work / 'worker-status.json')
            if reason:
                raise SystemExit(reason)
            time.sleep(2)
        raise SystemExit(0 if stopping else child.returncode)
    finally:
        stop()
        try:
            child.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=10)
        life.stop(child.returncode, reason)
