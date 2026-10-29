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


if __name__ == '__main__':
    unittest.main()
