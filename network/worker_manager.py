"""Serialize qualified workers without changing their measured engine settings."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from profile_catalog import load_catalog, worker_budget

DENSE_UNIT = 'llm-test-qwen27b.service'
MOE_UNIT = 'llm-router-worker.service'
STATE = ROOT / 'data/router/worker.json'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class RouterError(Exception):
    def __init__(self, message, code='backend_unavailable', status=503):
        super().__init__(message)
        self.code, self.status = code, status


def profiles():
    return {p['id']: p for p in load_catalog()['profiles']}


def unit_property(unit, prop):
    return subprocess.run(['systemctl', '--user', 'show', unit, '-p', prop, '--value'],
                          capture_output=True, text=True).stdout.strip()


class Workers:
    def __init__(self, key, timeout=1200):
        self.key, self.timeout = key, timeout
        self.lock = threading.Lock()
        self.active = self.detect()
        self.loading = None
        self.busy = False

    def backend_models(self):
        req = urllib.request.Request('http://127.0.0.1:10000/v1/models',
                                     headers={'Authorization': 'Bearer ' + self.key})
        try:
            with OPENER.open(req, timeout=3) as r:
                return json.load(r).get('data', [])
        except (OSError, ValueError):
            return []

    def detect(self):
        # A model name alone cannot distinguish the two dense engines.
        pid = unit_property(DENSE_UNIT, 'MainPID')
        if pid.isdigit() and int(pid) > 0:
            try:
                cmd = (Path('/proc') / pid / 'cmdline').read_bytes().split(b'\0')
                if any(b'env-hyperqwen/bin/vllm' in x for x in cmd):
                    return 'qwen27b-hyperqwen'
                if any(b'serve_qwen27b_engines.py' in x for x in cmd) and b'sglang' in cmd:
                    return 'qwen27b-sglang'
            except OSError:
                pass
        try:
            state = json.loads(STATE.read_text())
            if (state.get('profile') in profiles() and
                    state.get('invocation') == unit_property(state['unit'], 'InvocationID') and
                    unit_property(state['unit'], 'ActiveState') == 'active'):
                return state['profile']
        except (OSError, ValueError, KeyError):
            pass
        return None

    def stop_owned(self):
        if (ROOT / 'data/GPU-LOCK').exists():
            raise RouterError('GPUs are reserved; managed unloading is blocked.', 'gpu_reserved')
        # Exact unit and executable checks; never search for/kill all Python or GPU jobs.
        owned_pids = set()
        for unit in [DENSE_UNIT, MOE_UNIT]:
            if unit_property(unit, 'ActiveState') not in ('active', 'activating'):
                continue
            command = unit_property(unit, 'ExecStart')
            expected = 'serve_qwen27b_engines.py' if unit == DENSE_UNIT else 'serve_router_moe.py'
            if str(ROOT / 'scripts' / expected) not in command:
                raise RouterError('An unexpected process owns the inference unit; nothing was stopped.', 'ownership_conflict')
            group = unit_property(unit, 'ControlGroup')
            if group.startswith('/'):
                base = Path('/sys/fs/cgroup') / group.lstrip('/')
                for path in [base / 'cgroup.procs', *base.glob('**/cgroup.procs')]:
                    try:
                        owned_pids.update(int(x) for x in path.read_text().split())
                    except OSError:
                        pass
            subprocess.run(['systemctl', '--user', 'stop', unit], check=True, timeout=90)
        self.active = None
        STATE.unlink(missing_ok=True)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                occupied = probe.connect_ex(('127.0.0.1', 10000)) == 0
            output = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid',
                                           '--format=csv,noheader,nounits'], text=True)
            pids = {int(x.strip()) for x in output.splitlines() if x.strip().isdigit()}
            if not occupied and not (pids & owned_pids):
                return
            time.sleep(.5)
        raise RouterError('Port 10000 or GPU compute resources are still occupied. Unrecognized work was preserved.',
                          'resources_busy')

    def start(self, profile_id, progress=lambda: None):
        if (ROOT / 'data/GPU-LOCK').exists():
            raise RouterError('GPUs are reserved; remove the reservation after its owner finishes.', 'gpu_reserved')
        if self.active == profile_id and self.backend_models():
            return
        # Native Strata/Maya pages call their worker directly, outside this router lock.
        # Observe their status as well before starting a switch.
        if self.active and profiles().get(self.active, {}).get('engine') in ('Strata', 'Maya'):
            deadline = time.monotonic() + 7200
            while True:
                req = urllib.request.Request('http://127.0.0.1:10000/status',
                      headers={'Authorization': 'Bearer ' + self.key})
                try:
                    with OPENER.open(req, timeout=3) as response:
                        status = json.load(response)
                except (OSError, ValueError):
                    break
                if not status.get('busy') and not status.get('queued'):
                    break
                progress()
                if time.monotonic() >= deadline:
                    raise RouterError('The native web app is still answering.', 'backend_busy')
                time.sleep(1)
        self.stop_owned()
        profile = profiles()[profile_id]
        self.loading = profile_id
        try:
            if profile_id.startswith('qwen27b-'):
                cmd = [str(ROOT / 'scripts/start_model.sh'), *profile['launch']]
                unit = DENSE_UNIT
            else:
                budget = worker_budget(profile)
                cmd = ['systemd-run', '--user', '--collect', '--service-type=exec',
                       '--unit=' + MOE_UNIT,
                       '--property=MemoryHigh=' + str(budget['high']) + 'G',
                       '--property=MemoryMax=' + str(budget['max']) + 'G',
                       '--property=MemorySwapMax=' + str(budget['swap']) + 'G', '--property=OOMPolicy=kill',
                       '--property=LimitRTTIME=infinity', '--working-directory=' + str(ROOT),
                       '/usr/bin/python3', str(ROOT / 'scripts/serve_router_moe.py'), profile_id]
                unit = MOE_UNIT
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RouterError('Worker launch failed; inspect the owned worker journal.', 'launch_failed')
            invocation = unit_property(unit, 'InvocationID')
            STATE.parent.mkdir(parents=True, exist_ok=True)
            temp = STATE.with_suffix('.tmp')
            temp.write_text(json.dumps({'profile': profile_id, 'unit': unit, 'invocation': invocation}) + '\n')
            temp.chmod(0o600)
            temp.replace(STATE)
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline:
                progress()
                if unit_property(unit, 'ActiveState') not in ('active', 'activating'):
                    raise RouterError('Worker stopped during loading; inspect its journal.', 'launch_failed')
                models = self.backend_models()
                if models:
                    self.active = profile_id
                    return
                time.sleep(1)
            raise RouterError('Worker startup timed out; no second model was launched.', 'load_timeout', 504)
        finally:
            self.loading = None

    def acquire(self, profile_id, progress=lambda: None):
        # One active request; selection and inference share the same switch lock.
        deadline = time.monotonic() + 3600
        while not self.lock.acquire(timeout=1):
            progress()
            if time.monotonic() >= deadline:
                raise RouterError('A prior inference request is still running.', 'backend_busy')
        self.busy = True
        try:
            self.start(profile_id, progress)
        except BaseException:
            self.release()
            raise

    def release(self):
        self.busy = False
        self.lock.release()
