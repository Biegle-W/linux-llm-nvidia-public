"""Exercise the normal Maya launcher without starting an engine or touching GPUs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import serve_router_moe as supervisor


class MoeSupervisor(unittest.TestCase):
    def test_maya_monitor_keeps_owned_cgroup_separate_from_runtime_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            group = root / 'cgroups/managed/llm-router-worker.service'
            group.mkdir(parents=True)
            for name, value in [('memory.max', 48 * 1024**3),
                                ('memory.high', 46 * 1024**3), ('memory.swap.max', 'max')]:
                (group / name).write_text(str(value))
            (root / 'data/router').mkdir(parents=True)
            key = root / 'data/local-api-key'
            key.write_text('test-only-key')
            key.chmod(0o600)
            (root / 'data/router/access.json').write_text('{}')
            config = root / 'canonical.json'
            config.write_text(json.dumps({'args': ['--max-context', '32768']}))
            profile = dict(id='glm-maya', engine='Maya', allocated_context=32768,
                           runtime_selector={'path': 'canonical.json'})
            proc_state = Mock()
            proc_state.read_text.return_value = '0::/managed/llm-router-worker.service\n'
            def paths(value):
                if value == '/proc/self/cgroup':
                    return proc_state
                if value == '/sys/fs/cgroup':
                    return root / 'cgroups'
                return Path(value)
            child = Mock(returncode=0)
            child.poll.return_value = 0
            with patch.object(supervisor, 'ROOT', root), patch.object(supervisor, 'Path', side_effect=paths), \
                 patch.object(supervisor, 'get_profile', return_value=profile), \
                 patch.object(supervisor, 'worker_budget', return_value={'high': 46, 'max': 48, 'swap': None}), \
                 patch.object(supervisor, 'verify_storage'), patch.object(supervisor, 'telemetry_enabled', return_value=False), \
                 patch.object(supervisor.subprocess, 'Popen', return_value=child), \
                 patch.object(supervisor, 'WorkerWatch') as watch, \
                 patch.object(supervisor.signal, 'signal'), patch.object(sys, 'argv', ['supervisor', 'glm-maya']):
                with self.assertRaises(SystemExit) as result:
                    supervisor.main()
            self.assertEqual(result.exception.code, 0)
            self.assertEqual(watch.call_args.args[0], group)
            self.assertNotEqual(watch.call_args.args[0], root / 'runtimes/project-maya')


if __name__ == '__main__':
    unittest.main()
