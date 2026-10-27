#!/usr/bin/env python3
"""Run a dense engine with the qualified host, temperature and swap guards."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from inference_swap_guard import WorkerWatch, ROOT
from profile_catalog import get_profile, worker_budget
from lifecycle_telemetry import LifecycleLog, enabled as telemetry_enabled


def main():
    os.umask(0o077)
    engine = sys.argv[1]
    if engine not in ('hyperqwen', 'sglang'):
        raise SystemExit('Choose a maintained dense engine.')
    profile = get_profile('qwen27b-' + engine)
    group = next(line.split('::', 1)[1] for line in Path('/proc/self/cgroup').read_text().splitlines()
                 if line.startswith('0::'))
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    budget = worker_budget(profile)
    if (not group.endswith('/llm-test-qwen27b.service')
            or (base / 'memory.max').read_text().strip() != str(budget['max'] * 1024 ** 3)
            or (base / 'memory.high').read_text().strip() != str(budget['high'] * 1024 ** 3)
            or (base / 'memory.swap.max').read_text().strip() != 'max'):
        raise SystemExit('Start the dense worker through the bounded launcher.')
    key = (ROOT / 'data/local-api-key').read_text().strip()
    watch = WorkerWatch(base, profile['id'], key)
    lifecycle = LifecycleLog(profile['id']) if telemetry_enabled() else None
    if lifecycle:
        lifecycle.start()
    env = dict(os.environ, LOCAL_LLM_GUARDED_WORKER='1')
    child = subprocess.Popen(['/usr/bin/python3', str(ROOT / 'scripts/serve_qwen27b_engines.py'), engine],
                             start_new_session=True, env=env)
    def stop(*_):
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    bad = 0
    reason = None
    try:
        while child.poll() is None:
            reason = watch.step()
            if lifecycle:
                lifecycle.set_phase(watch.last_phase)
            available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                             if line.startswith('MemAvailable:'))
            raw = subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu,memory.free',
                                           '--format=csv,noheader,nounits'], text=True)
            cards = [[float(value) for value in line.split(',')] for line in raw.splitlines()]
            bad = bad + 1 if (available < 8 * 1024 ** 2 or any(card[0] >= 82 for card in cards)
                             or (watch.ready and any(card[1] < 1024 for card in cards))) else 0
            if reason or bad >= 3:
                reason = reason or 'Dense host/temperature/GPU-headroom guard reached.'
                print(reason, flush=True)
                stop()
                raise SystemExit(1)
            time.sleep(2)
        raise SystemExit(child.returncode)
    finally:
        stop()
        try:
            child.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=10)
        if lifecycle:
            lifecycle.stop(child.returncode, reason)


if __name__ == '__main__':
    main()
