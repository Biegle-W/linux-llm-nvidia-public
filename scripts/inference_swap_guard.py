"""Observe owned-cgroup swap churn; loading and parked pages are not violations."""
from collections import deque
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PAGE_BYTES = os.sysconf('SC_PAGE_SIZE')
MIB = 1024 ** 2
# User-approved dense GPU free-memory floor; independent of swap thresholds.
DENSE_GPU_FREE_MIB = 512
# Explicit maintained SSD-streaming profiles; unknown/dense profiles fail closed.
SSD_STREAMING_PROFILES = frozenset({
    'flash-next-strata', 'glm-maya', 'deepseek-strata', 'deepseek-maya',
})


class TelemetryError(RuntimeError):
    pass


class SwapGuard:
    """A violation latches for this worker invocation until explicitly reloaded."""
    def __init__(self, window_s=30, write_mib_s=1, combined_mib_s=8,
                 pressure_pct=10, bad_samples=3):
        self.window_s, self.write_limit = window_s, write_mib_s
        self.combined_limit, self.pressure_limit = combined_mib_s, pressure_pct
        self.bad_samples = bad_samples
        self.history = deque()
        self.pressure_bad = self.missing = 0
        self.violation = None
        self.last_rates = None

    def fail(self, reason):
        self.violation = self.violation or reason
        return self.violation

    def unavailable(self, reason):
        self.missing += 1
        if self.missing >= self.bad_samples:
            self.fail('Inference telemetry unavailable: ' + reason)
        return self.violation

    def sample(self, now, phase, swap_in_pages, swap_out_pages, pressure_pct):
        if self.violation:
            return self.violation
        self.missing = 0
        if phase != 'inference':
            self.history.clear()
            self.pressure_bad = 0
            self.last_rates = None
            return None
        if self.history:
            last = self.history[-1]
            if now <= last[0] or swap_in_pages < last[1] or swap_out_pages < last[2]:
                return self.fail('Inference counter/time continuity lost')
        self.history.append((now, swap_in_pages, swap_out_pages))
        while len(self.history) > 2 and self.history[1][0] <= now - self.window_s:
            self.history.popleft()
        first = self.history[0]
        duration = now - first[0]
        if duration >= self.window_s:
            self.pressure_bad = self.pressure_bad + 1 if pressure_pct > self.pressure_limit else 0
            if self.pressure_bad >= self.bad_samples:
                return self.fail('Sustained full-memory pressure during inference')
            read = (swap_in_pages - first[1]) * PAGE_BYTES / MIB / duration
            write = (swap_out_pages - first[2]) * PAGE_BYTES / MIB / duration
            self.last_rates = {'window_s': duration, 'read_mib_s': read,
                               'write_mib_s': write, 'combined_mib_s': read + write}
            if write > self.write_limit or read + write > self.combined_limit:
                return self.fail('Sustained owned-worker swap churn during inference')
        return None


def read_cgroup(group):
    values = dict(line.split() for line in (group / 'memory.stat').read_text().splitlines())
    pressure = {}
    for line in (group / 'memory.pressure').read_text().splitlines():
        fields = line.split()
        pressure[fields[0]] = dict(part.split('=') for part in fields[1:])
    try:
        return {'swap_in_pages': int(values['pswpin']), 'swap_out_pages': int(values['pswpout']),
                'pressure_pct': float(pressure['full']['avg10']),
                'swap_current_bytes': int((group / 'memory.swap.current').read_text())}
    except (KeyError, ValueError) as error:
        raise TelemetryError('Missing or invalid owned-cgroup swap/pressure counters') from error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


class WorkerWatch:
    def __init__(self, group, profile, key, *, evidence=None, phase_file=None, latch=True):
        self.group, self.profile, self.key = Path(group), profile, key
        # SSD-streaming profiles may evict cold anonymous pages as file caches
        # warm. Keep their bounded I/O policy separate from dense defaults.
        self.policy = ({'write_mib_s': 128, 'combined_mib_s': 160}
                       if profile in SSD_STREAMING_PROFILES else {})
        self.guard, self.ready = SwapGuard(**self.policy), False
        self.evidence = Path(evidence) if evidence else ROOT / 'data/router' / (profile + '-swap-guard.jsonl')
        self.phase_file = Path(phase_file) if phase_file else None
        self.latch = latch
        self.last_phase = 'loading'
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, path):
        request = urllib.request.Request('http://127.0.0.1:10000' + path,
                                         headers={'Authorization': 'Bearer ' + self.key})
        with self.opener.open(request, timeout=1.5) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise TelemetryError('Worker telemetry exceeds the bounded response size')
        return data.decode()

    def phase(self):
        if self.phase_file and self.phase_file.exists():
            phase = json.loads(self.phase_file.read_text())['phase']
            if phase in ('loading', 'warmup', 'idle'):
                return 'loading' if phase == 'warmup' else phase
        try:
            if self.profile.startswith('qwen27b-'):
                text = self.get('/metrics')
                name = ('sglang:num_running_reqs' if self.profile.endswith('sglang')
                        else 'vllm:num_requests_running')
                values = [float(line.rsplit(' ', 1)[1]) for line in text.splitlines()
                          if line.startswith(name + '{') or line.startswith(name + ' ')]
                if not values:
                    raise TelemetryError('Running-request gauge missing')
                busy = any(value > 0 for value in values)
            else:
                status = json.loads(self.get('/status'))
                if type(status.get('busy')) is not bool:
                    raise TelemetryError('Native busy status missing')
                busy = status['busy'] or bool(status.get('compute_active'))
                if status.get('loading'):
                    return 'loading'
                if status.get('loaded') is False and not busy:
                    return 'unloaded'
                stage = str(status.get('phase') or '').lower()
                if busy and any(word in stage for word in ('loading', 'encoding image', 'vision encoder')):
                    return 'loading'
            self.ready = True
            return 'inference' if busy else 'idle'
        except (OSError, ValueError) as error:
            if not self.ready:
                return 'loading'
            raise TelemetryError('Owned worker request-state telemetry unavailable') from error

    def step(self):
        now = time.monotonic()
        row = {'time': time.time(), 'profile': self.profile,
               'limits': {'window_s': self.guard.window_s,
                          'write_mib_s': self.guard.write_limit,
                          'combined_mib_s': self.guard.combined_limit,
                          'pressure_pct': self.guard.pressure_limit}}
        try:
            phase = self.phase()
            self.last_phase = phase
            counters = read_cgroup(self.group)
            reason = self.guard.sample(now, phase, counters['swap_in_pages'],
                                       counters['swap_out_pages'], counters['pressure_pct'])
            row.update(phase=phase, **counters)
        except (OSError, ValueError, TelemetryError) as error:
            reason = self.guard.unavailable(str(error))
            row.update(phase='unknown', telemetry_error=str(error))
        row.update(rates=self.guard.last_rates, violation=reason)
        self.evidence.parent.mkdir(parents=True, exist_ok=True)
        if self.evidence.exists() and self.evidence.stat().st_size > 5 * MIB:
            self.evidence.replace(self.evidence.with_suffix('.jsonl.1'))
        with self.evidence.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        self.evidence.chmod(0o600)
        if reason and self.latch:
            path = ROOT / 'data/router/guard-stops' / (self.profile + '.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(row, indent=2) + '\n')
            path.chmod(0o600)
        return reason
