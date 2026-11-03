import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from maya_cachebound_runtime import verify


class RuntimePin(unittest.TestCase):
    def test_legacy_runtime_is_unchanged(self):
        verify({'exe': '/nonexistent/legacy-maya-ds4'}, {'id': 'deepseek-maya'})

    def test_pinned_binary_and_rejected_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / 'runtimes/maya-ds4-file-cache-bound/maya-ds4'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'qualified-binary-fixture')
            (root / 'config').mkdir()
            manifest = {'schema': 1, 'profile': 'deepseek-maya', 'binary': {
                'path': str(binary.relative_to(root)),
                'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}}
            (root / 'config/maya-cachebound-runtime.json').write_text(json.dumps(manifest))
            cfg = {'exe': str(binary), 'cache_bound_runtime': {'manifest': 'config/maya-cachebound-runtime.json'}}
            verify(cfg, {'id': 'deepseek-maya'}, root)
            with self.assertRaises(ValueError): verify(cfg, {'id': 'glm-maya'}, root)
            with self.assertRaises(ValueError): verify({'exe': str(binary)}, {'id': 'deepseek-maya'}, root)
            with self.assertRaises(ValueError): verify({**cfg, 'exe': str(root / 'foreign')}, {'id': 'deepseek-maya'}, root)
            with self.assertRaises(ValueError): verify({**cfg, 'cache_bound_runtime': {'manifest': '../foreign'}}, {'id': 'deepseek-maya'}, root)
            binary.write_bytes(b'tampered')
            with self.assertRaises(ValueError): verify(cfg, {'id': 'deepseek-maya'}, root)


    def test_glm_pin_profile_and_tamper_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / 'runtimes/maya-glm-v1150/maya'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'glm-qualified-fixture')
            (root / 'config').mkdir()
            manifest = {'schema': 1, 'profile': 'glm-maya', 'binary': {
                'path': str(binary.relative_to(root)),
                'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}}
            (root / 'config/maya-glm-runtime.json').write_text(json.dumps(manifest))
            cfg = {'exe': str(binary), 'pinned_runtime': {'manifest': 'config/maya-glm-runtime.json'}}
            verify(cfg, {'id': 'glm-maya'}, root)
            with self.assertRaises(ValueError): verify(cfg, {'id': 'deepseek-maya'}, root)
            with self.assertRaises(ValueError): verify({'exe': str(binary)}, {'id': 'glm-maya'}, root)
            with self.assertRaises(ValueError): verify({**cfg, 'exe': str(root / 'foreign')}, {'id': 'glm-maya'}, root)
            binary.write_bytes(b'tampered')
            with self.assertRaises(ValueError): verify(cfg, {'id': 'glm-maya'}, root)

    def test_ambiguous_pin_selection_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            verify({'exe': '/foreign', 'pinned_runtime': {}, 'cache_bound_runtime': {}}, {'id': 'glm-maya'})


class GLMUpdaterPin(unittest.TestCase):
    def fixture(self, root, pin='config/maya-glm-runtime.json'):
        (root / 'config').mkdir()
        binary = root / 'runtimes/maya-glm-v1150/maya'
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b'old-engine'); binary.chmod(0o755)
        manifest = {'schema': 1, 'profile': 'glm-maya', 'release': '1.1.50', 'binary': {
            'path': str(binary.relative_to(root)), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}}
        (root / 'config/maya-glm-runtime.json').write_text(json.dumps(manifest))
        cfg = {'exe': str(binary), 'pinned_runtime': {'manifest': pin}, 'lib_dirs': []}
        (root / 'native.json').write_text(json.dumps(cfg))
        (root / 'config/maintained-profiles.json').write_text(json.dumps({'profiles': [
            {'id': 'glm-maya', 'runtime_selector': {'path': 'native.json'}}]}))
        return binary

    def build_candidate(self, root):
        from unittest.mock import patch
        from update_builders import build
        revision = '2' * 40
        def fake_run(command, log, cwd=None, env=None, timeout=None):
            command = list(map(str, command))
            if command[:2] == ['git', 'clone']: Path(command[-1]).mkdir()
            if command[:2] == ['cmake', '--build']:
                binary = Path(command[2]) / 'maya'
                binary.parent.mkdir(parents=True); binary.write_bytes(b'new-engine')
        component = {'id': 'maya-glm', 'profiles': ['glm-maya'], 'builder': 'maya',
                     'upstream': 'https://github.com/mw00/project-maya.git'}
        with patch('update_builders.run', side_effect=fake_run), patch(
                'update_builders.subprocess.check_output', return_value=revision):
            return build(root, component, revision, root / 'candidate')

    def test_update_activation_and_rollback_keep_binary_and_manifest_together(self):
        from update_transaction import Transaction
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); binary = self.fixture(root)
            receipt = self.build_candidate(root)
            transaction = Transaction(root / 'transaction.json'); transaction.begin('glm-maya', 'candidate', {})
            for action in receipt['files']: transaction.file(action['target'], action['candidate'])
            verify(json.loads((root / 'native.json').read_text()), {'id': 'glm-maya'}, root)
            self.assertEqual(binary.read_bytes(), b'new-engine')
            self.assertNotIn('release', json.loads((root / 'config/maya-glm-runtime.json').read_text()))
            transaction.rollback()
            verify(json.loads((root / 'native.json').read_text()), {'id': 'glm-maya'}, root)
            self.assertEqual(binary.read_bytes(), b'old-engine')

    def test_unreviewed_manifest_is_rejected_without_changing_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); binary = self.fixture(root, '../foreign.json')
            with self.assertRaisesRegex(RuntimeError, 'Unreviewed'): self.build_candidate(root)
            self.assertEqual(binary.read_bytes(), b'old-engine')


if __name__ == '__main__':
    unittest.main()
