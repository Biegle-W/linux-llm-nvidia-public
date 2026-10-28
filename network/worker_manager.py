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
from inference_policy import load_policy
from visible_terminal import open_monitor, close_backend_monitor
from inference_swap_guard import WorkerWatch
from idle_control import claim as claim_idle, release as release_idle, owned_native_idle

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
    def __init__(self, key, timeout=1200, idle_timeout=None):
        self.key, self.timeout = key, timeout
        self.lock = threading.Lock()
        self.active = self.detect()
        self.loading = None
        self.busy = False
        self.idle_timeout = load_policy()['idle_timeout_s'] if idle_timeout is None else idle_timeout
        if type(self.idle_timeout) is not int or self.idle_timeout <= 0:
            raise ValueError('Managed model idle timeout must be positive')
        self.last_activity = time.monotonic()
        self.idle_unloading = None
        self._idle_probe = None

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
                if any(b'supervise_dense.py' in x for x in cmd) and b'hyperqwen' in cmd:
                    return 'qwen27b-hyperqwen'
                if any(b'supervise_dense.py' in x for x in cmd) and b'sglang' in cmd:
                    return 'qwen27b-sglang'
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

    def stop_owned(self, allowed_lock=None, only_unit=None):
        reservation = ROOT / 'data/GPU-LOCK'
        if reservation.exists():
            try:
                allowed = allowed_lock is not None and json.loads(reservation.read_text()) == allowed_lock
            except (OSError, ValueError):
                allowed = False
            if not allowed:
                raise RouterError('GPUs are reserved; managed unloading is blocked.', 'gpu_reserved')
        # Exact unit and executable checks; never search for/kill all Python or GPU jobs.
        owned_pids = set()
        for unit in [DENSE_UNIT, MOE_UNIT]:
            if only_unit is not None and unit != only_unit:
                continue
            if unit_property(unit, 'ActiveState') not in ('active', 'activating'):
                continue
            command = unit_property(unit, 'ExecStart')
            expected = 'serve_qwen27b_engines.py' if unit == DENSE_UNIT else 'serve_router_moe.py'
            recognized = str(ROOT / 'scripts' / expected) in command
            if unit == DENSE_UNIT:
                recognized = recognized or str(ROOT / 'scripts/supervise_dense.py') in command
            if not recognized:
                raise RouterError('An unexpected process owns the inference unit; nothing was stopped.', 'ownership_conflict')
            invocation = unit_property(unit, 'InvocationID')
            if unit == MOE_UNIT:
                request = urllib.request.Request('http://127.0.0.1:10000/status',
                          headers={'Authorization': 'Bearer ' + self.key})
                try:
                    with OPENER.open(request, timeout=3) as response:
                        status = json.load(response)
                    if type(status.get('busy')) is not bool:
                        raise ValueError('Native busy state missing')
                except (OSError, ValueError) as error:
                    raise RouterError('Native worker state is unavailable; active work was preserved.',
                                      'backend_state_unknown', 409) from error
                if any(status.get(k) for k in ('busy', 'queued', 'loading', 'compute_active')):
                    raise RouterError('The native web app is active; unloading was deferred.',
                                      'backend_busy', 409)
            group = unit_property(unit, 'ControlGroup')
            if group.startswith('/'):
                base = Path('/sys/fs/cgroup') / group.lstrip('/')
                for path in [base / 'cgroup.procs', *base.glob('**/cgroup.procs')]:
                    try:
                        owned_pids.update(int(x) for x in path.read_text().split())
                    except OSError:
                        pass
            if invocation != unit_property(unit, 'InvocationID'):
                raise RouterError('Worker ownership changed during switching; retry after it settles.',
                                  'ownership_conflict')
            subprocess.run(['systemctl', '--user', 'stop', unit], check=True, timeout=90)
            close_backend_monitor(unit)
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

    def wait_native_idle(self, progress=lambda: None):
        reservation = ROOT / 'data/GPU-LOCK'
        deadline = time.monotonic() + 120
        while reservation.exists() and owned_native_idle(reservation):
            if time.monotonic() >= deadline:
                raise RouterError('Native idle teardown is still running; retry after it finishes.', 'idle_teardown_busy')
            progress()
            time.sleep(.25)

    def start(self, profile_id, progress=lambda: None):
        self.wait_native_idle(progress)
        if (ROOT / 'data/GPU-LOCK').exists():
            raise RouterError('GPUs are reserved by another task. Wait for its owner to finish; the router and harness are preserved.', 'gpu_reserved')
        latch = ROOT / 'data/router/guard-stops' / (profile_id + '.json')
        if latch.exists():
            raise RouterError('This worker was stopped by a safety guard. Explicitly select the model to reload after reviewing its guard log.',
                              'safety_guard_latched')
        if self.active == profile_id:
            models = self.backend_models()
            if any(model.get('status', {}).get('value') != 'unloaded' for model in models):
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
                if (not status.get('busy') and not status.get('queued')
                        and not status.get('loading') and not status.get('compute_active')):
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
                       '--property=MemorySwapMax=infinity', '--property=OOMPolicy=kill',
                       '--property=LimitRTTIME=infinity', '--working-directory=' + str(ROOT),
                       '/usr/bin/python3', str(ROOT / 'scripts/serve_router_moe.py'), profile_id]
                unit = MOE_UNIT
                open_monitor('NVIDIA MoE backend', unit, [ROOT / 'data/router' / (p['id'] + '-engine.log')
                             for p in profiles().values() if p['engine'] in ('Strata', 'Maya')])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                    env=dict(os.environ, LOCAL_LLM_ROUTER_WORKER='1'))
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
                    self.touch_activity()
                    return
                time.sleep(1)
            raise RouterError('Worker startup timed out; no second model was launched.', 'load_timeout', 504)
        finally:
            self.loading = None

    def acquire(self, profile_id, progress=lambda: None, clear_guard=False):
        # One active request; selection and inference share the same switch lock.
        deadline = time.monotonic() + 3600
        while not self.lock.acquire(timeout=1):
            progress()
            if time.monotonic() >= deadline:
                raise RouterError('A prior inference request is still running.', 'backend_busy')
        self.busy = True
        try:
            if clear_guard:
                self.wait_native_idle(progress)
                if (ROOT / 'data/GPU-LOCK').exists():
                    raise RouterError('GPUs are reserved; explicit reload is blocked.', 'gpu_reserved')
                (ROOT / 'data/router/guard-stops' / (profile_id + '.json')).unlink(missing_ok=True)
            self.start(profile_id, progress)
        except BaseException:
            self.release()
            raise

    def release(self):
        self.touch_activity()
        self.busy = False
        self.lock.release()

    def touch_activity(self):
        self.last_activity = time.monotonic()
        active = getattr(self, 'active', None)
        if not active:
            return
        try:
            path = ROOT / 'data/router/activity' / (active + '.txt')
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(str(time.time()))
            temporary.chmod(0o600)
            temporary.replace(path)
        except OSError:
            # Activity-log failure must not strand the request/switch lock.
            pass

    def idle_tick(self, now=None):
        """Dense engines use the router lock; native engines use their FIFO adapter."""
        now = time.monotonic() if now is None else now
        if (not getattr(self, 'idle_timeout', 0) or not self.active
                or not self.active.startswith('qwen27b-')):
            return False
        if not self.lock.acquire(blocking=False):
            return False
        owner = None
        reservation = ROOT / 'data/GPU-LOCK'
        try:
            if self.busy or self.loading or reservation.exists():
                return False
            if self._idle_probe is None or self._idle_probe.profile != self.active:
                self._idle_probe = WorkerWatch('/unused', self.active, self.key, latch=False)
            if self._idle_probe.phase() != 'idle':
                self.last_activity = now
                return False
            if now - self.last_activity < self.idle_timeout:
                return False
            profile = self.active
            owner = claim_idle(reservation, profile)
            if owner is None:
                return False
            if self._idle_probe.phase() != 'idle':
                self.last_activity = now
                return False
            self.idle_unloading = profile
            self.stop_owned(allowed_lock=owner, only_unit=DENSE_UNIT)
            record = ROOT / 'data/router/idle-events.jsonl'
            record.parent.mkdir(parents=True, exist_ok=True)
            with record.open('a') as stream:
                stream.write(json.dumps({'time': time.time(), 'profile': profile,
                                         'event': 'idle-unloaded', 'timeout_s': self.idle_timeout}) + '\n')
            record.chmod(0o600)
            return True
        except Exception:
            # Missing state never justifies stopping a possibly active worker.
            self.last_activity = now
            return False
        finally:
            self.idle_unloading = None
            release_idle(reservation, owner)
            self.lock.release()
