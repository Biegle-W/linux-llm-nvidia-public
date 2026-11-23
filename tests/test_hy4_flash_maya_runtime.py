"""Exercise Hy4 Maya startup with a synthetic preset, small artifacts and no GPU."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hy4_flash_maya_runtime import MANIFEST, CONFIG, PROFILE, prepare_config
from profile_catalog import get_profile
from storage_policy import verify_storage


class Hy4MayaRuntime(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.profile = get_profile(PROFILE)
        self.pins = json.loads((ROOT / MANIFEST).read_text())
        self.manifest = self.root / MANIFEST
        self.manifest.parent.mkdir()
        self.preset = self.root / CONFIG
        self.preset.parent.mkdir(parents=True)
        self.weights = self.root / self.profile['storage']['checkpoint_directory']
        self.weights.mkdir(parents=True)
        for row in self.pins['files']:
            (self.weights / row['file']).write_bytes(b'trial')
            row['bytes'] = 5
        pack = self.weights / 'maya-hy4'
        for name in self.pins['pack_files_sha256']:
            path = pack / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            self.pins['pack_files_sha256'][name] = hashlib.sha256(name.encode()).hexdigest()
        binary = self.root / 'runtimes/maya-hy4-v1174/maya-hy4'
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b'engine')
        self.pins['binary']['sha256'] = hashlib.sha256(b'engine').hexdigest()
        self.config = dict(exe=str(binary), cwd=str(self.root / 'runtimes/project-maya'),
                           tokenizer=str(pack / 'tokenizer'), model_name='hy4-flash-maya-l', gpu=[0, 1],
                           reasoning_effort='none', web_ui=False,
                           args=['--pack', str(pack), '--main-gpu', '0', '--tp', '0', '--max-context', '131072',
                                 '--vision', 'off', '--kv', 'auto', '--reserve-gb', '0.75',
                                 '--kv-spill-dir', str(self.root / 'data/hy4-maya-state'), '--drafting', 'off'])

    def prepare(self, config=None, pins=None, profile=None):
        self.manifest.write_text(json.dumps(self.pins if pins is None else pins))
        self.preset.write_text(json.dumps(self.config if config is None else config))
        return prepare_config(self.profile if profile is None else profile, self.root)

    def test_exact_preset(self):
        self.assertEqual(self.prepare(), self.config)

    def test_supervised_launch_uses_validated_config_and_shared_idle_policy(self):
        import inference_policy
        import serve_router_moe as launcher
        from profile_catalog import budget_limit_string

        self.prepare()
        group = self.root / 'llm-router-worker.service'
        group.mkdir()
        for name, value in self.profile['worker_memory_gib'].items():
            filename = 'memory.swap.max' if name == 'swap' else 'memory.' + name
            (group / filename).write_text(budget_limit_string(value))
        proc = self.root / 'cgroup'
        proc.write_text('0::/llm-router-worker.service')
        def path(value):
            return {'/proc/self/cgroup': proc, '/sys/fs/cgroup': self.root}.get(value, Path(value))
        key = self.root / 'data/local-api-key'
        key.parent.mkdir()
        key.write_text('fixture')
        key.chmod(0o600)
        adapter = self.root / inference_policy.NATIVE_SOURCES['Maya']
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_text('# Managed NVIDIA idle reservation\n# idle_activity_path idle_lock_path')
        (self.root / 'config/inference-policy.json').write_bytes((ROOT / 'config/inference-policy.json').read_bytes())
        target = self.root / 'data/router' / (PROFILE + '-runtime.json')
        with ExitStack() as stack:
            mock = lambda *a, **kw: stack.enter_context(patch(*a, **kw))
            mock('pair_p2p_health.require_verified_pair')
            mock('profile_catalog.require_host_capacity')
            mock('sys.argv', ['supervisor', 'hy4-maya'])
            stack.enter_context(patch.dict(os.environ))
            mock('os.umask')
            mock('signal.signal')
            mock('serve_router_moe.ROOT', self.root)
            mock('serve_router_moe.Path', side_effect=path)
            mock('serve_router_moe.verify_storage')
            mock('serve_router_moe.telemetry_enabled', return_value=False)
            mock('serve_router_moe.apply_native_idle', side_effect=lambda c, p: inference_policy.apply_native_idle(c, p, self.root))
            mock('hy4_flash_maya_runtime.prepare_config', wraps=lambda p: prepare_config(p, self.root))
            popen = mock('serve_router_moe.subprocess.Popen', return_value=Mock(returncode=0, poll=lambda: 0))
            with self.assertRaises(SystemExit) as result:
                launcher.main()
        self.assertEqual(result.exception.code, 0)
        maya = self.root / 'runtimes/project-maya'
        popen.assert_called_once_with([str(maya / '.venv/bin/python'), str(maya / 'serve/server.py'),
                                      '--engine', 'strata', '--port', '10000', '--config', str(target)],
                                     start_new_session=True)
        config = json.loads(target.read_text())
        self.assertEqual(set(config), set(self.config) | {'log', 'host', 'port', 'api_key',
                                                         'idle_unload_s', 'idle_activity_path', 'idle_lock_path'})
        self.assertEqual({k: config[k] for k in self.config}, self.config)
        self.assertEqual((config['idle_unload_s'], target.stat().st_mode & 0o777), (600, 0o600))

    def test_malformed_and_overridden_preset(self):
        for key, wrong in dict(gpu=[1, 0], env={}, vision={}, sampling={}, layer_split='auto',
                               exe='/other', cwd='/tmp', tokenizer='other', web_ui=0,
                               model_name='other', reasoning_effort='high', user_args=[]).items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare(dict(self.config, **{key: wrong}))
        for wrong in ([False, 1], [0, True], [0.0, 1]):
            with self.subTest(gpu=wrong), self.assertRaises(ValueError):
                self.prepare(dict(self.config, gpu=wrong))
        for wrong in ([], {}):
            with self.assertRaises(ValueError):
                self.prepare(wrong)

    def test_arguments_are_exact_and_ordered(self):
        args = self.config['args']
        for flag in ('--chunk', '--gpus', '--layer-split', '--mtp', '--dfly2', '--serve', '--cpu-threads', '--gpu-fetch'):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                self.prepare(dict(self.config, args=args + [flag]))
        for i in range(0, len(args), 2):
            with self.subTest(flag=args[i]), self.assertRaises(ValueError):
                self.prepare(dict(self.config, args=args[:i+1] + ['wrong'] + args[i+2:]))
        with self.assertRaises(ValueError):
            self.prepare(dict(self.config, args=args[2:] + args[:2]))

    def test_profile_identity_and_context(self):
        for key, wrong in [('id', 'other'), ('engine', 'Strata'), ('allocated_context', 8192), ('runtime_manifest', 'other'), ('runtime_selector', {})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare(profile=dict(self.profile, **{key: wrong}))

    def test_each_weight_receipt(self):
        for i, row in enumerate(self.pins['files']):
            for field, wrong in [('publisher_sha256_matched', False), ('bytes', 4), ('file', 'other')]:
                pins = deepcopy(self.pins)
                pins['files'][i][field] = wrong
                with self.subTest(file=row['file'], field=field), self.assertRaises(ValueError):
                    self.prepare(pins=pins)

    def test_each_runtime_hash_is_required_and_verified(self):
        pins = deepcopy(self.pins)
        pins['binary']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.prepare(pins=pins)
        for name in self.pins['pack_files_sha256']:
            pins = deepcopy(self.pins)
            pins['pack_files_sha256'][name] = '0' * 64
            with self.subTest(mismatch=name), self.assertRaises(ValueError):
                self.prepare(pins=pins)
            del pins['pack_files_sha256'][name]
            with self.subTest(missing=name), self.assertRaises(ValueError):
                self.prepare(pins=pins)

    def test_storage_preflight(self):
        for transport, rotational in [('sata', '0'), ('sata', '1'), ('nvme', '0')]:
            answers = ['/dev/test', 'disk ' + transport, 'disk ' + rotational, '/dev/test']
            with self.subTest(transport=transport, rotational=rotational), patch(
                    'storage_policy.subprocess.check_output', side_effect=answers):
                if (transport, rotational) == ('sata', '0'):
                    self.assertEqual(verify_storage(self.profile, self.root)['weight_files'], 2)
                else:
                    with self.assertRaises(RuntimeError):
                        verify_storage(self.profile, self.root)

    def test_short_check_headroom_and_native_phase(self):
        from cli_short_models import guards
        from inference_swap_guard import WorkerWatch
        policy = guards(self.profile)
        self.assertEqual((policy['host_available_reserve_GiB'], policy['explicit_GPU_free_floor_MiB']), (2, None))
        self.assertIsNone(policy['native_cache_reserve_MiB'])
        self.assertIsNone(policy['loading_PSI_percent'])
        watch = WorkerWatch(self.root, PROFILE, 'fixture', latch=False)
        for busy, phase in [(True, 'inference'), (False, 'idle')]:
            with patch.object(watch, 'get', return_value=json.dumps(dict(busy=busy, queued=0))) as status:
                self.assertEqual(watch.phase(), phase)
                status.assert_called_once_with('/status')

    def test_update_coverage_and_manual_engine_install(self):
        from update_builders import canonical
        from update_native_builders import native
        policy = json.loads((ROOT / 'config/daily-update.json').read_text())
        component = next(c for c in policy['components'] if c['id'] == 'maya')
        self.assertIn(PROFILE, component['profiles'])
        self.assertIn(MANIFEST, policy['publication_files']['maya'])
        self.assertEqual(canonical(ROOT, PROFILE), ROOT / CONFIG)
        from update_native_builders import stage_maya_hy4_pin
        self.manifest.write_text(json.dumps(self.pins))
        candidate = self.root / 'candidate-maya-hy4'; candidate.write_bytes(b'new build')
        staged = self.root / 'staged'; staged.mkdir()
        receipt = {'files': []}
        stage_maya_hy4_pin(self.root, 'f' * 40, candidate, staged, receipt)
        written = json.loads((staged / 'maya-hy4-runtime.json').read_text())
        import hashlib
        self.assertEqual((written['source_commit'], written['binary']['sha256'], written['binary']['path']),
                         ('f' * 40, hashlib.sha256(b'new build').hexdigest(), 'runtimes/maya-hy4-v1174/maya-hy4'))
        self.assertEqual([f['target'] for f in receipt['files']],
                         [str(self.root / 'runtimes/maya-hy4-v1174/maya-hy4'), str(self.root / 'config/maya-hy4-runtime.json')])
