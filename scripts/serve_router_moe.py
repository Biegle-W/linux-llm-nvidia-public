#!/usr/bin/env python3
"""Run the canonical selected MoE setting in the router's bounded owned service."""
import json
import os
from pathlib import Path
import sys
import subprocess
import signal
import time
from profile_catalog import get_profile

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.umask(0o077)
    group = next(line.split('::', 1)[1] for line in Path('/proc/self/cgroup').read_text().splitlines()
                 if line.startswith('0::'))
    limit = (Path('/sys/fs/cgroup') / group.lstrip('/') / 'memory.max').read_text().strip()
    profile = get_profile(sys.argv[1])
    cap = 48 if profile['id'] in ('flash-next-strata', 'glm-maya') else 36
    if not group.endswith('/llm-router-worker.service') or limit == 'max' or int(limit) > cap * 1024 ** 3:
        sys.exit('Start MoE workers through the model router.')
    if profile['id'] == 'flash-next-strata':
        source = Path.home() / '.local/state/strata/launch/qwen-flash-next.json'
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
    for name, value in profile.get('selected_settings', {}).get('environment', {}).items():
        if str(config.get('env', {}).get(name)) != str(value):
            sys.exit('Canonical RAM/cache setting differs from the selected registry.')
    args = config['args']
    if int(args[args.index('--max-context') + 1]) != profile['allocated_context']:
        sys.exit('Canonical context differs from the selected registry; refusing launch.')
    key = ROOT / 'data/local-api-key'
    if key.stat().st_mode & 0o077:
        sys.exit('API-key permissions must be owner-only.')
    config.update(host='127.0.0.1', port=10000, api_key=key.read_text().strip(),
                  parallel=1, reasoning_effort='none', open_browser=False,
                  log=str(ROOT / 'data/router' / (profile['id'] + '-engine.log')))
    config.pop('args_written', None)
    target = ROOT / 'data/router' / (profile['id'] + '-runtime.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + '\n')
    target.chmod(0o600)
    os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID', PYTHONUNBUFFERED='1')
    if profile['engine'] == 'Strata':
        binary = ROOT / 'runtimes/bin/strata'
        command = [str(binary), 'serve', '--profile', str(target), '--offline']
    else:
        base = ROOT / 'runtimes/project-maya'
        python = base / '.venv/bin/python'
        command = [str(python), str(base / 'serve/server.py'), '--engine', 'strata', '--port', '10000', '--config', str(target)]
    child = subprocess.Popen(command, start_new_session=True)
    def stop(*_):
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    bad = 0
    try:
        while child.poll() is None:
            available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
            temps = subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'], text=True)
            bad = bad + 1 if available < 8 * 1024 ** 2 or any(float(t) >= 82 for t in temps.splitlines()) else 0
            if bad >= 3:
                print('Worker stopped by host-memory/temperature guard.', flush=True)
                stop()
                child.wait(timeout=20)
                raise SystemExit(1)
            time.sleep(2)
        raise SystemExit(child.returncode)
    finally:
        if child.poll() is None:
            stop()
            child.wait(timeout=20)


if __name__ == '__main__':
    main()
