#!/usr/bin/env python3
"""Run the canonical selected MoE setting in the router's bounded owned service."""
import json
import math
import os
from pathlib import Path
import sys
import subprocess
import signal
import time
from profile_catalog import get_profile, worker_budget, host_ram_reserve_gib, require_enabled, budget_limit_string
from storage_policy import verify_storage
from maya_cachebound_runtime import verify as verify_cachebound_runtime
from inference_policy import apply_native_idle
from inference_swap_guard import WorkerWatch, GPU_FREE_MIB
from lifecycle_telemetry import LifecycleLog, enabled as telemetry_enabled

ROOT = Path(__file__).resolve().parents[1]


def pair_gpu_free_values(raw):
    values = [float(x) for x in raw.splitlines()]
    if len(values) != 2 or any(not math.isfinite(x) or x < 0 for x in values):
        raise RuntimeError('Expected valid GPU telemetry for the permanent 3080 pair')
    return values


def require_flash_next_split(config, profile):
    """Refuse a Flash-Next launch whose card order, layer split or stage trim drifted from the registry."""
    selected = profile.get('selected_settings', {})
    args = config.get('args', [])
    if (config.get('gpu') != selected.get('gpu') or str(config.get('layer_split')) != str(selected.get('layer_split'))
            or config.get('gpu_order') != selected.get('gpu_order') or '--layer-split' in args
            or ('--trim-stage-weights' in args) != bool(selected.get('trim_stage_weights'))):
        raise ValueError('Flash-Next layer split differs from the selected registry; refusing launch.')


def main():
    os.umask(0o077)
    from pair_p2p_health import require_verified_pair
    require_verified_pair()
    require_enabled(get_profile(sys.argv[1]))
    from profile_catalog import require_host_capacity
    require_host_capacity(get_profile(sys.argv[1]))
    if sys.argv[1] == 'bolt-llamacpp':
        from bolt_iq2_runtime import main as bolt_main
        return bolt_main()
    group = next(line.split('::', 1)[1] for line in Path('/proc/self/cgroup').read_text().splitlines()
                 if line.startswith('0::'))
    limit = (Path('/sys/fs/cgroup') / group.lstrip('/') / 'memory.max').read_text().strip()
    profile = get_profile(sys.argv[1])
    budget = worker_budget(profile)
    host_floor_kib = host_ram_reserve_gib(profile) * 1024 ** 2
    cgroup_base = Path('/sys/fs/cgroup') / group.lstrip('/')
    if (not group.endswith('/llm-router-worker.service') or limit == 'max'
            or int(limit) != budget['max'] * 1024 ** 3
            or (cgroup_base / 'memory.high').read_text().strip() != budget_limit_string(budget['high'])
            or (cgroup_base / 'memory.swap.max').read_text().strip() != 'max'):
        sys.exit('Start MoE workers through the model router with the selected bounded budget.')
    verify_storage(profile)
    if profile['id'] == 'deepseek-unsloth-strata':
        from strata_unsloth_runtime import prepare_config
        source = prepare_config(profile)
    elif profile['id'] == 'flash-next-strata':
        source = Path.home() / '.local/state/strata/launch/qwen-flash-next.json'
        try:
            require_flash_next_split(json.loads(source.read_text()), profile)
        except ValueError as error:
            sys.exit(str(error))
    elif profile['id'] == 'deepseek-strata':
        wrapper = json.loads((Path.home() / '.config/strata/profiles/deepseek-maya-s.json').read_text())
        if wrapper.get('overrides'):
            sys.exit('Review runtime overrides before using this selected profile.')
        source = Path(wrapper['source_config'])
    elif profile['engine'] == 'Maya':
        source = ROOT / profile['runtime_selector']['path']
    else:
        sys.exit('No qualified MoE profile selected.')
    config = json.loads(source.read_text())
    verify_cachebound_runtime(config, profile)
    for name, value in profile.get('selected_settings', {}).get('environment', {}).items():
        if str(config.get('env', {}).get(name)) != str(value):
            sys.exit('Canonical RAM/cache setting differs from the selected registry.')
    # No GPU peer access (the cards sit on CPU x8/x8 bifurcation). ggml enables peer access
    # whenever GGML_CUDA_P2P is present, whatever its value, so it must be absent, not '0'.
    config.setdefault('env', {}).update(NCCL_P2P_DISABLE='1')
    for name in ('NCCL_P2P_LEVEL', 'GGML_CUDA_P2P'):
        config['env'].pop(name, None)
        os.environ.pop(name, None)
    os.environ.update(NCCL_P2P_DISABLE='1')
    args = config['args']
    if int(args[args.index('--max-context') + 1]) != profile['allocated_context']:
        sys.exit('Canonical context differs from the selected registry; refusing launch.')
    key = ROOT / 'data/local-api-key'
    if key.stat().st_mode & 0o077:
        sys.exit('API-key permissions must be owner-only.')
    config.update(host='127.0.0.1', port=10000, api_key=key.read_text().strip(),
                  parallel=1, reasoning_effort='none', open_browser=False,
                  log=str(ROOT / 'data/router' / (profile['id'] + '-engine.log')))
    config = apply_native_idle(config, profile)
    config.pop('args_written', None)
    target = ROOT / 'data/router' / (profile['id'] + '-runtime.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + '\n')
    target.chmod(0o600)
    os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID', PYTHONUNBUFFERED='1')
    if profile['id'] == 'deepseek-unsloth-strata':
        isolated = ROOT / 'data/strata-unsloth'
        os.environ.update(XDG_STATE_HOME=str(isolated / 'state'),
                          XDG_CONFIG_HOME=str(isolated / 'config'),
                          XDG_CACHE_HOME=str(isolated / 'cache'),
                          HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        command = [str(ROOT / 'runtimes/project-maya/.venv/bin/python'),
                   str(ROOT / 'runtimes/strata-unsloth-029/source/serve/server.py'),
                   '--engine', 'strata', '--port', '10000', '--config', str(target)]
    elif profile['engine'] == 'Strata':
        binary = ROOT / 'runtimes/bin/strata'
        command = [str(binary), 'serve', '--profile', str(target), '--offline']
    else:
        maya_base = ROOT / 'runtimes/project-maya'
        python = maya_base / '.venv/bin/python'
        command = [str(python), str(maya_base / 'serve/server.py'), '--engine', 'strata', '--port', '10000', '--config', str(target)]
    lifecycle = LifecycleLog(profile['id']) if telemetry_enabled() else None
    if lifecycle:
        lifecycle.start()
    child = subprocess.Popen(command, start_new_session=True)
    watch = WorkerWatch(cgroup_base, profile['id'], key.read_text().strip())
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
        if lifecycle:
            lifecycle.set_phase("stopping")
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    bad = gpu_bad = loading_bad = 0
    reason = None
    try:
        while child.poll() is None and not stopping:
            reason = watch.step()
            if stopping:
                break
            if lifecycle:
                lifecycle.set_phase(watch.last_phase)
            if reason:
                print(reason, flush=True)
                stop()
                child.wait(timeout=20)
                raise SystemExit(1)
            if profile['id'] == 'deepseek-unsloth-strata':
                free = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True)
                free_values = pair_gpu_free_values(free)
                gpu_bad = gpu_bad + 1 if any(x < GPU_FREE_MIB for x in free_values) else 0
                from inference_swap_guard import read_cgroup
                pressure = read_cgroup(cgroup_base)['pressure_pct']
                loading_bad = loading_bad + 1 if profile['id']=='deepseek-unsloth-strata' and watch.last_phase == 'loading' and pressure > 15 else 0
                if gpu_bad >= 3 or loading_bad >= 3:
                    reason = 'Unsloth GPU reserve/loading pressure guard'
                    watch.guard.fail(reason)
                    watch.step()
                    stop()
                    child.wait(timeout=20)
                    raise SystemExit(1)
            available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
            temps = subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'], text=True)
            bad = bad + 1 if available < host_floor_kib or any(float(t) >= 100 for t in temps.splitlines()) else 0
            if bad >= 3:
                reason = 'Worker stopped by host-memory/temperature guard.'
                print('Worker stopped by host-memory/temperature guard.', flush=True)
                stop()
                child.wait(timeout=20)
                raise SystemExit(1)
            time.sleep(2)
        raise SystemExit(0 if stopping else child.returncode)
    finally:
        if child.poll() is None:
            stop()
            child.wait(timeout=20)
        if lifecycle:
            lifecycle.stop(child.returncode, reason)


if __name__ == '__main__':
    main()
