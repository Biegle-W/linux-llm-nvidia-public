"""Exercise Inkling SQ-10 startup with a synthetic preset, small artifacts and no GPU."""
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
from inkling_strata_runtime import MANIFEST, PRESET, PROFILE, prepare_config
from profile_catalog import get_profile
from storage_policy import verify_storage


class InklingStrataRuntime(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.profile = get_profile(PROFILE)
        self.pins = json.loads((ROOT / MANIFEST).read_text())
        self.manifest = self.root / MANIFEST
        self.manifest.parent.mkdir()
        self.preset = self.root / 'home' / PRESET
        self.preset.parent.mkdir(parents=True)
        self.weights = self.root / self.profile['storage']['checkpoint_directory']
        self.weights.mkdir(parents=True)
        for row in self.pins['files']:
            (self.weights / row['file']).write_bytes(b'trial')
            row['bytes'] = 5
        for group in ('engine', 'tokenizer'):
            folder = self.root / self.pins[group + '_directory']
            folder.mkdir(parents=True)
            hashes = self.pins[group + '_files_sha256']
            for name in hashes:
                content = name.encode()
                (folder / name).write_bytes(content)
                hashes[name] = hashlib.sha256(content).hexdigest()
        engine = self.root / 'runtimes/strata-inkling/0.1.66-linux-x86_64-cuda-cuda13'
        self.config = dict(exe=str(engine / 'strata-inkling'), arch='inkling2_loop', cwd=str(self.root),
                           tokenizer=str(self.root / 'models/strata/packs/inkling-2-mini-sq-10/tokenizer'),
                           model_name='inkling-2-mini-sq-10', lib_dirs=[str(engine)], gpu=[0, 1], gpu_order='as_given', gpus_asked=True,
                           drafting='off', parallel=1, args=['--native', str(self.weights / 'Inkling-2-Mini-SQ-10.strata'),
                                                            '--max-context', '131072', '--draft', 'off', '--layer-split', 'auto'])

    def prepare(self, config=None, pins=None, profile=None):
        self.manifest.write_text(json.dumps(self.pins if pins is None else pins))
        self.preset.write_text(json.dumps(self.config if config is None else config))
        return prepare_config(self.profile if profile is None else profile, self.root, self.root / 'home')

    def test_write_preset(self):
        from inkling_strata_runtime import write_preset
        self.manifest.write_text(json.dumps(self.pins))
        write_preset(self.profile, self.root, self.root / 'home')
        self.assertEqual(self.preset.stat().st_mode & 0o777, 0o600)
        self.assertEqual(prepare_config(self.profile, self.root, self.root / 'home'), self.config)

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
        adapter = self.root / inference_policy.NATIVE_SOURCES['Strata']
        adapter.parent.mkdir(parents=True)
        adapter.write_text('# Managed NVIDIA idle reservation\n# idle_activity_path idle_lock_path')
        (self.root / 'config/inference-policy.json').write_bytes((ROOT / 'config/inference-policy.json').read_bytes())
        target = self.root / 'data/router' / (PROFILE + '-runtime.json')
        with ExitStack() as stack:
            mock = lambda *a, **kw: stack.enter_context(patch(*a, **kw))
            mock('pair_p2p_health.require_verified_pair')
            mock('profile_catalog.require_host_capacity')
            mock('sys.argv', ['supervisor', 'inkling-strata'])
            stack.enter_context(patch.dict(os.environ))
            mock('os.umask')
            mock('signal.signal')
            mock('serve_router_moe.ROOT', self.root)
            mock('serve_router_moe.Path', side_effect=path)
            mock('serve_router_moe.verify_storage')
            mock('serve_router_moe.telemetry_enabled', return_value=False)
            mock('serve_router_moe.apply_native_idle', side_effect=lambda c, p: inference_policy.apply_native_idle(c, p, self.root))
            mock('inkling_strata_runtime.prepare_config', wraps=lambda p: prepare_config(p, self.root, self.root / 'home'))
            popen = mock('serve_router_moe.subprocess.Popen', return_value=Mock(returncode=0, poll=lambda: 0))
            with self.assertRaises(SystemExit) as result:
                launcher.main()
        self.assertEqual(result.exception.code, 0)
        popen.assert_called_once_with([str(self.root / 'runtimes/bin/strata'), 'serve', '--profile', str(target),
                                      '--offline'], start_new_session=True)
        config = json.loads(target.read_text())
        self.assertEqual(set(config), set(self.config) | {'env', 'host', 'port', 'api_key', 'reasoning_effort',
                                                         'open_browser', 'log', 'idle_unload_s',
                                                         'idle_lock_path', 'idle_activity_path'})
        self.assertEqual({k: config[k] for k in self.config}, self.config)
        self.assertEqual(config['gpu'], [0, 1])
        self.assertEqual(config['env'], {'NCCL_P2P_DISABLE': '1'})
        self.assertEqual((config['host'], config['port'], config['parallel'], config['reasoning_effort']),
                         ('127.0.0.1', 10000, 1, 'none'))
        self.assertEqual((config['idle_unload_s'], target.stat().st_mode & 0o777), (600, 0o600))

    def test_malformed_and_overridden_preset(self):
        for key, wrong in dict(arch='qwen', gpu=[0], gpu_order='auto', gpus_asked=1, drafting='on', parallel=True,
                               env={}, exe='/other', cwd='/tmp', lib_dirs=[], tokenizer='other',
                               model_name='other', args='--serve', user_args=[], vision={}).items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare(dict(self.config, **{key: wrong}))
        for wrong in (False, 0, [1, 0], [False, True]):
            with self.subTest(gpu=wrong), self.assertRaises(ValueError):
                self.prepare(dict(self.config, gpu=wrong))
        for wrong in ([], {}):
            with self.assertRaises(ValueError):
                self.prepare(wrong)

    def test_arguments_are_exact_and_ordered(self):
        args = self.config['args']
        for flag in ('--gpus', '--gpu', '--vision', '--dspark', '--parallel', '--serve', '--cpu-threads', '--vram-reserve-mib', '--kv'):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                self.prepare(dict(self.config, args=args + [flag]))
        for i in range(0, len(args), 2):
            with self.subTest(flag=args[i]), self.assertRaises(ValueError):
                self.prepare(dict(self.config, args=args[:i+1] + ['wrong'] + args[i+2:]))
        with self.assertRaises(ValueError):
            self.prepare(dict(self.config, args=args[2:] + args[:2]))

    def test_profile_identity_and_context(self):
        for key, wrong in [('id', 'other'), ('engine', 'Maya'), ('allocated_context', 8192), ('runtime_manifest', 'other'), ('runtime_selector', {})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare(profile=dict(self.profile, **{key: wrong}))

    def test_registry_settings_match_the_trial(self):
        for key, value in [('gpu', [0]), ('gpu', [False, True]), ('layer_split', '1,1'),
                           ('context', 8192), ('drafting', 'on'), ('parallel', True)]:
            profile = deepcopy(self.profile)
            profile['selected_settings'][key] = value
            with self.subTest(setting=key), self.assertRaises(ValueError):
                self.prepare(profile=profile)

    def test_each_weight_receipt(self):
        for i, row in enumerate(self.pins['files']):
            for field, wrong in [('publisher_sha256_matched', False), ('bytes', 4), ('file', 'other')]:
                pins = deepcopy(self.pins)
                pins['files'][i][field] = wrong
                with self.subTest(file=row['file'], field=field), self.assertRaises(ValueError):
                    self.prepare(pins=pins)

    def test_each_runtime_hash_is_required_and_verified(self):
        for group in ('engine_files_sha256', 'tokenizer_files_sha256'):
            for name in self.pins[group]:
                pins = deepcopy(self.pins)
                pins[group][name] = '0' * 64
                with self.subTest(mismatch=name), self.assertRaises(ValueError):
                    self.prepare(pins=pins)
                del pins[group][name]
                with self.subTest(missing=name), self.assertRaises(ValueError):
                    self.prepare(pins=pins)

    def test_storage_preflight(self):
        with patch('storage_policy.subprocess.check_output', side_effect=['/dev/test', 'disk nvme']):
            self.assertEqual(verify_storage(self.profile, self.root)['weight_files'], 1)

    def test_short_check_headroom_and_native_phase(self):
        from cli_short_models import guards
        from inference_swap_guard import WorkerWatch
        policy = guards(self.profile)
        self.assertEqual((policy['host_available_reserve_GiB'], policy['explicit_GPU_free_floor_MiB']), (2, 256))
        self.assertIsNone(policy['native_cache_reserve_MiB'])
        self.assertIsNone(policy['loading_PSI_percent'])
        watch = WorkerWatch(self.root, PROFILE, 'fixture', latch=False)
        for busy, phase in [(True, 'inference'), (False, 'idle')]:
            with patch.object(watch, 'get', return_value=json.dumps(dict(busy=busy, queued=0))) as status:
                self.assertEqual(watch.phase(), phase)
                status.assert_called_once_with('/status')

    def test_update_coverage_and_manual_engine_install(self):
        from update_builders import canonical
        from update_native_builders import signed_strata
        policy = json.loads((ROOT / 'config/daily-update.json').read_text())
        component = next(c for c in policy['components'] if c['id'] == 'strata')
        self.assertIn(PROFILE, component['profiles'])
        self.assertIn(MANIFEST, policy['publication_files']['strata'])
        self.assertEqual(canonical(ROOT, PROFILE), Path.home() / PRESET)
        with self.assertRaisesRegex(RuntimeError, 'by hand'):
            signed_strata(self.root, dict(component, profiles=[PROFILE]), None, None, None, None, None)
