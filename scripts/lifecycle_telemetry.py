"""Bounded private CPU/GPU lifecycle records; absent sensors remain unavailable."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['index', 'name', 'pci.bus_id', 'temperature.gpu', 'pstate',
          'clocks.current.sm', 'clocks.current.memory', 'power.draw', 'power.limit',
          'fan.speed', 'utilization.gpu', 'utilization.memory', 'memory.used', 'memory.free']


def enabled():
    try:
        from inference_policy import load_policy
        return load_policy(ROOT)['lifecycle_telemetry']
    except (OSError, ValueError):
        return False


def numeric(value):
    value = value.strip()
    if value in ('N/A', '[N/A]', '[Not Supported]', 'Not Supported'):
        return None
    try:
        return float(value)
    except ValueError:
        return value


def gpu_sample():
    raw = subprocess.check_output(['nvidia-smi', '--query-gpu=' + ','.join(FIELDS),
                                   '--format=csv,noheader,nounits'], text=True, timeout=3)
    cards = [dict(zip(FIELDS, (numeric(v) for v in row))) for row in csv.reader(raw.splitlines())]
    # This optional mask is evidence, not a claim that a particular limiter hurt speed.
    try:
        reasons = subprocess.check_output(['nvidia-smi', '--query-gpu=index,clocks_event_reasons.active',
                                           '--format=csv,noheader,nounits'], text=True, timeout=3)
        masks = {int(row[0]): row[1].strip() for row in csv.reader(reasons.splitlines())}
        for card in cards:
            card['clocks_event_reasons.active'] = masks.get(int(card['index']))
    except (OSError, ValueError, subprocess.SubprocessError):
        for card in cards:
            card['clocks_event_reasons.active'] = None
    return cards


def cpu_and_board_sample():
    devices = []
    for directory in Path('/sys/class/hwmon').glob('hwmon*'):
        try:
            name = (directory / 'name').read_text().strip()
        except OSError:
            continue
        sensors = {}
        for pattern, divisor, unit in [('temp*_input', 1000, 'C'), ('fan*_input', 1, 'rpm'),
                                       ('power*_input', 1000000, 'W')]:
            for path in directory.glob(pattern):
                try:
                    label = path.with_name(path.name.replace('_input', '_label'))
                    label = label.read_text().strip() if label.exists() else path.stem
                    sensors[path.stem + '/' + label] = {'value': float(path.read_text()) / divisor, 'unit': unit}
                except (OSError, ValueError):
                    sensors[path.stem] = {'value': None, 'unit': unit}
        if sensors:
            devices.append({'device': name, 'sensors': sensors})
    mhz = []
    for line in Path('/proc/cpuinfo').read_text().splitlines():
        if line.startswith('cpu MHz'):
            mhz.append(float(line.split(':')[1]))
    throttle = {}
    for path in Path('/sys/devices/system/cpu').glob('cpu*/thermal_throttle/*_throttle_count'):
        try:
            throttle[path.parent.parent.name + '/' + path.name] = int(path.read_text())
        except (OSError, ValueError):
            pass
    return {'hwmon': devices, 'cpu_mhz_min': min(mhz) if mhz else None,
            'cpu_mhz_max': max(mhz) if mhz else None, 'cpu_throttle_counts': throttle}


def owned_cgroup_sample():
    group = next(line.split('::', 1)[1] for line in Path('/proc/self/cgroup').read_text().splitlines()
                 if line.startswith('0::'))
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    values = {}
    for name in ['memory.current', 'memory.swap.current', 'memory.high', 'memory.max',
                 'memory.swap.max', 'memory.events', 'io.stat']:
        try:
            values[name] = (base / name).read_text().strip()
        except OSError:
            values[name] = None
    return values


class LifecycleLog:
    def __init__(self, profile, *, path=None, interval=5, limit_bytes=10 * 1024 ** 2):
        self.profile, self.interval, self.limit_bytes = profile, interval, limit_bytes
        self.path = Path(path) if path else ROOT / 'data/telemetry' / profile / 'lifecycle.jsonl'
        self.last = 0
        self.phase = 'loading'
        self.done = threading.Event()
        self.thread = None
        self.lock = threading.Lock()
        self.last_error = None

    def event(self, event, **values):
        with self.lock:
            self._event(event, **values)

    def _event(self, event, **values):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size >= self.limit_bytes:
            one = self.path.with_suffix('.1.jsonl')
            two = self.path.with_suffix('.2.jsonl')
            if one.exists():
                one.replace(two)
            self.path.replace(one)
        row = {'time': time.time(), 'monotonic_s': time.monotonic(),
               'profile': self.profile, 'event': event, **values}
        with self.path.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        self.path.chmod(0o600)

    def start(self):
        registry = ROOT / 'config/maintained-profiles.json'
        self.event('starting', pid=os.getpid(), kernel=os.uname().release,
                   catalog_sha256=hashlib.sha256(registry.read_bytes()).hexdigest())
        def collect():
            while not self.done.is_set():
                try:
                    self.sample(self.phase, force=True)
                    self.last_error = None
                except OSError as error:
                    # Optional telemetry must not kill the safety supervisor.
                    self.last_error = type(error).__name__
                    print('Lifecycle telemetry write failed: ' + self.last_error,
                          file=sys.stderr, flush=True)
                self.done.wait(self.interval)
        self.thread = threading.Thread(target=collect, daemon=True)
        self.thread.start()

    def set_phase(self, phase):
        self.phase = phase

    def sample(self, phase, force=False):
        now = time.monotonic()
        if not force and now - self.last < self.interval:
            return
        self.last = now
        row = {'phase': phase}
        try:
            row['gpu'] = gpu_sample()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            row.update(gpu=None, gpu_error=type(error).__name__)
        try:
            row.update(cpu_and_board_sample())
            row['memory_kib'] = {name: int(value.split()[0]) for name, value in
                (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
                if name in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree')}
        except (OSError, ValueError) as error:
            row['host_sensor_error'] = type(error).__name__
        try:
            row['owned_cgroup'] = owned_cgroup_sample()
        except (OSError, ValueError, StopIteration) as error:
            row.update(owned_cgroup=None, owned_cgroup_error=type(error).__name__)
        self.event('sample', **row)

    def stop(self, returncode, reason=None):
        self.done.set()
        if self.thread:
            self.thread.join(timeout=7)
        self.sample('stopping', force=True)
        self.event('stopped', returncode=returncode, reason=reason)
