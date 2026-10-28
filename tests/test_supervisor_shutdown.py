"""Intentional teardown must not manufacture a missing-telemetry guard latch."""
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import supervise_dense
import serve_router_moe


class ShutdownTest(unittest.TestCase):
    def exercise(self, module, intentional):
        dense = module is supervise_dense
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unit = 'llm-test-qwen27b.service' if dense else 'llm-router-worker.service'
            group = root / 'cgroups/managed' / unit
            group.mkdir(parents=True)
            high, hard = (30, 36) if dense else (46, 48)
            for name, value in [('memory.high', high * 1024**3),
                                ('memory.max', hard * 1024**3), ('memory.swap.max', 'max')]:
                (group / name).write_text(str(value))
            (root / 'data/router').mkdir(parents=True)
            (root / 'data/local-api-key').write_text('test-only-key')
            (root / 'data/local-api-key').chmod(0o600)
            (root / 'data/router/access.json').write_text('{}')
            (root / 'canonical.json').write_text(json.dumps({'args': ['--max-context', '32768']}))
            profile = dict(id='qwen27b-hyperqwen' if dense else 'glm-maya', engine='Maya',
                           allocated_context=32768, runtime_selector={'path': 'canonical.json'})
            proc_state = Mock()
            proc_state.read_text.return_value = '0::/managed/' + unit + '\n'
            mem = Mock()
            mem.read_text.return_value = 'MemAvailable: 20971520 kB\n'
            def paths(value):
                if value == '/proc/self/cgroup': return proc_state
                if value == '/proc/meminfo': return mem
                if value == '/sys/fs/cgroup': return root / 'cgroups'
                return Path(value)
            child = Mock(pid=12345, returncode=-15)
            # A slow teardown stays alive after SIGTERM. Further telemetry would fail.
            child.poll.return_value = None
            watch = Mock(ready=True, last_phase='idle')
            if intentional:
                watch.step.side_effect = [None, AssertionError('Telemetry sampled after intentional stop')]
            else:
                watch.step.return_value = 'Unexpected telemetry loss'
            handlers = {}
            def register(sig, handler): handlers[sig] = handler
            def sleep(_seconds): handlers[signal.SIGTERM](signal.SIGTERM, None)
            extra = patch.object(module, 'verify_storage') if not dense else patch.object(module, 'ROOT', root)
            with patch.object(module, 'ROOT', root), patch.object(module, 'Path', side_effect=paths), \
                 patch.object(module, 'get_profile', return_value=profile), \
                 patch.object(module, 'worker_budget', return_value={'high': high, 'max': hard, 'swap': None}), \
                 patch.object(module, 'telemetry_enabled', return_value=False), \
                 patch.object(module.subprocess, 'Popen', return_value=child), \
                 patch.object(module.subprocess, 'check_output', return_value='45, 2048\n' if dense else '45\n'), \
                 patch.object(module, 'WorkerWatch', return_value=watch), \
                 patch.object(module.signal, 'signal', side_effect=register), \
                 patch.object(module.os, 'killpg'), patch.object(module.time, 'sleep', side_effect=sleep), \
                 patch.object(sys, 'argv', ['supervisor', 'hyperqwen' if dense else 'glm-maya']), extra:
                with self.assertRaises(SystemExit) as result:
                    module.main()
            self.assertEqual(result.exception.code, 0 if intentional else 1)
            watch.step.assert_called_once()
            child.wait.assert_called()

    def test_dense_intentional_slow_shutdown_stops_monitoring(self):
        self.exercise(supervise_dense, True)

    def test_moe_intentional_slow_shutdown_stops_monitoring(self):
        self.exercise(serve_router_moe, True)

    def test_dense_unexpected_telemetry_loss_still_fails_closed(self):
        self.exercise(supervise_dense, False)

    def test_moe_unexpected_telemetry_loss_still_fails_closed(self):
        self.exercise(serve_router_moe, False)


if __name__ == '__main__':
    unittest.main()
