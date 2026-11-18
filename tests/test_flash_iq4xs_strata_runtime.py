"""The UD-IQ4_XS-v31 Flash-Next entry keeps its own preset and fails closed on drift."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from flash_iq4xs_strata_runtime import MANIFEST, PRESET, INSTALLED, PROFILE, prepare_config
from inference_swap_guard import WorkerWatch
from profile_catalog import get_profile, load_catalog


class FlashIQ4XS(unittest.TestCase):
    def fixture(self, root):
        directory = root / 'models/iq4xs'
        directory.mkdir(parents=True)
        files = []
        for i in range(1, 5):
            name = f'Qwen3.8-Flash-Next-UD-IQ4_XS-0000{i}-of-00004.gguf'
            (directory / name).write_bytes(b'x')
            files.append(dict(file=name, bytes=1, publisher_sha256_matched=True))
        pack = root / 'pack'
        (pack / 'tokenizer').mkdir(parents=True)
        (pack / 'dense.bin').write_bytes(b'dense')
        engine = root / 'engine/strata'
        engine.parent.mkdir()
        engine.write_bytes(b'native')
        pins = dict(checkpoint_directory='models/iq4xs', pack_directory='pack', files=files,
                    pack_files_sha256={'pack/dense.bin': hashlib.sha256(b'dense').hexdigest()})
        manifest = root / MANIFEST
        manifest.parent.mkdir()
        manifest.write_text(json.dumps(pins))
        config = dict(exe=str(engine), lib_dirs=[str(engine.parent)], tokenizer=str(pack / 'tokenizer'),
                      gpu=[0, 1], layer_split='auto',
                      args=['--pack', str(pack), '--native', str(directory / files[0]['file']), '--spec', '4',
                            '--max-context', '131072', '--kv', 'int8', '--kv-resident', '32768', '--vision',
                            '--pool-workers', '15'])
        preset = root / 'home' / PRESET
        preset.parent.mkdir(parents=True)
        preset.write_text(json.dumps(config))
        (root / 'home' / INSTALLED).write_text(json.dumps(dict(exe=str(engine), lib_dirs=[str(engine.parent)])))
        profile = dict(id=PROFILE, allocated_context=131072, runtime_manifest=MANIFEST,
                       storage=dict(checkpoint_directory='models/iq4xs'),
                       selected_settings=dict(gpu=[0, 1], gpu_order=None, layer_split='auto', kv='int8',
                                              kv_resident=32768, pool_workers=15))
        return profile, preset, config

    def refused(self, change):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, preset, config = self.fixture(root)
            change(root, profile, preset, config)
            with self.assertRaises((ValueError, OSError)):
                prepare_config(profile, root, root / 'home')

    def test_matching_preset_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, preset, _ = self.fixture(root)
            self.assertEqual(prepare_config(profile, root, root / 'home'), preset)

    def test_layout_and_argument_drift_is_refused(self):
        def set_field(field, value):
            def change(root, profile, preset, config):
                config[field] = value
                preset.write_text(json.dumps(config))
            return change
        for field, value in [('gpu', [1, 0]), ('gpu', [0]), ('layer_split', '29'), ('gpu_order', 'as_given'),
                             ('tokenizer', 'other-pack'), ('args', []), ('user_args', ['--kv-resident', '0']),
                             ('user_args', ['--layer-split', '29']), ('user_args', '--kv-resident=0'),
                             ('args', None), ('args', ['--pack', None]), ('gpu', [False, True]), ('gpu', None),
                             ('exe', None), ('lib_dirs', None)]:
            with self.subTest(field=field, value=value):
                self.refused(set_field(field, value))

        def edit_args(edit):
            def change(root, profile, preset, config):
                config['args'] = edit(list(config['args']))
                preset.write_text(json.dumps(config))
            return change
        for name, edit in [
                ('context', lambda a: [('65536' if x == '131072' else x) for x in a]),
                ('kv-resident', lambda a: [('65536' if x == '32768' else x) for x in a]),
                ('workers', lambda a: [('9' if x == '15' else x) for x in a]),
                ('kv', lambda a: [('fp16' if x == 'int8' else x) for x in a]),
                ('split flag', lambda a: a + ['--layer-split', '29']),
                ('trim', lambda a: a + ['--trim-stage-weights']),
                ('table mode', lambda a: a + ['--ple-io', 'direct']),
                ('reserve', lambda a: a + ['--vram-reserve-mib', '1024']),
                ('joined form', lambda a: a + ['--kv-resident=0']),
                ('repeated flag', lambda a: a + ['--pool-workers', '15'])]:
            with self.subTest(args=name):
                self.refused(edit_args(edit))

    def test_weights_pack_and_engine_drift_is_refused(self):
        def resized(root, profile, preset, config):
            (root / 'models/iq4xs/Qwen3.8-Flash-Next-UD-IQ4_XS-00002-of-00004.gguf').write_bytes(b'xx')

        def repacked(root, profile, preset, config):
            (root / 'pack/dense.bin').write_bytes(b'other')

        def other_engine(root, profile, preset, config):
            (root / 'home' / INSTALLED).write_text(json.dumps(dict(exe='/other/strata', lib_dirs=config['lib_dirs'])))

        def other_context(root, profile, preset, config):
            profile['allocated_context'] = 65536

        def unverified(root, profile, preset, config):
            pins = json.loads((root / MANIFEST).read_text())
            pins['files'][1]['publisher_sha256_matched'] = False
            (root / MANIFEST).write_text(json.dumps(pins))
        for change in (resized, repacked, other_engine, other_context, unverified):
            with self.subTest(change=change.__name__):
                self.refused(change)

    def test_registry_entry_and_guards(self):
        profile = get_profile(PROFILE)
        s = profile['selected_settings']
        self.assertEqual((profile['engine'], profile['allocated_context'], profile['launch'], profile['runtime_manifest']),
                         ('Strata', 131072, ['qwen-iq4xs'], MANIFEST))
        self.assertEqual((s['gpu'], s['layer_split'], s.get('gpu_order'), s['kv_resident'], s['pool_workers']),
                         ([0, 1], 'auto', None, 32768, 15))
        self.assertEqual(profile['storage']['required_transport'], 'nvme')
        installed = get_profile('flash-next-strata')
        self.assertEqual(profile['worker_memory_gib'], installed['worker_memory_gib'])
        self.assertNotEqual(profile['storage']['checkpoint_directory'], installed['storage']['checkpoint_directory'])
        guard = WorkerWatch('/unused', PROFILE, 'fixture', latch=False).guard
        self.assertEqual((guard.window_s, guard.write_limit, guard.combined_limit, guard.pressure_limit), (30, 128, 160, 15))

    def test_manifest_matches_registry(self):
        pins = json.loads((ROOT / MANIFEST).read_text())
        profile = get_profile(PROFILE)
        self.assertEqual(pins['checkpoint_directory'], profile['storage']['checkpoint_directory'])
        self.assertEqual(sum(row['bytes'] for row in pins['files']), profile['storage']['base_weight_bytes'])
        self.assertTrue(all(len(row['sha256']) == 64 and row['publisher_sha256_matched'] is True for row in pins['files']))
        self.assertTrue(pins['pack_files_sha256'])

    def test_launch_name_and_update_coverage(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/start_model.sh'), 'qwen-iq4xs', 'extra'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('qwen-iq4xs', (ROOT / 'scripts/start_model.sh').read_text())
        policy = json.loads((ROOT / 'config/daily-update.json').read_text())
        strata = next(c for c in policy['components'] if c['id'] == 'strata')
        self.assertIn(PROFILE, strata['profiles'])
        self.assertIn(MANIFEST, policy['publication_files']['strata'])
        from daily_engine_update import validate_update_coverage
        validate_update_coverage(load_catalog(), policy)
        from update_builders import canonical
        self.assertEqual(canonical(ROOT, PROFILE), Path.home() / PRESET)


if __name__ == '__main__':
    unittest.main()
