"""Protect the deployed runtime from wrong imports, source drift and path errors."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sglang_runtime as runtime


class RuntimeIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / 'runtime/python/sglang'
        self.package.mkdir(parents=True)
        (self.package / '__init__.py').write_text('qualified = True\n')
        (self.root / 'runtime/bin').mkdir()
        (self.root / 'runtime/bin/python').symlink_to(sys.executable)
        (self.root / 'candidate.patch').write_text('qualified patch\n')
        (self.root / 'config').mkdir()
        self.config = {'schema': 1, 'package_directory': 'runtime/python',
                       'python': 'runtime/bin/python', 'patch': 'candidate.patch',
                       'patch_sha256': hashlib.sha256((self.root / 'candidate.patch').read_bytes()).hexdigest(),
                       'package_tree_sha256': runtime.tree_digest(self.package),
                       'cache_directory': 'runtime/cache', 'runtime_versions': {'torch': 'qualified'}}
        self.save()

    def save(self):
        (self.root / 'config/sglang-runtime.json').write_text(json.dumps(self.config))

    def test_venv_interpreter_link_keeps_venv_path_and_enables_tested_environment(self):
        python, env, _ = runtime.prepare_environment({'CUDA_HOME': '/cuda', 'SGLANG_PP_LAYER_PARTITION': '64'}, self.root)
        self.assertEqual(python, self.root / 'runtime/bin/python')
        self.assertEqual(env['LOCAL_SGLANG_MLP_W4A8'], '1')
        self.assertEqual(env['PYTHONPATH'], str(self.package.parent))
        self.assertNotIn('SGLANG_PP_LAYER_PARTITION', env)

    def test_changed_source_rejected_but_python_bytecode_is_ignored(self):
        bytecode = self.package / '__pycache__'
        bytecode.mkdir()
        (bytecode / 'cache.pyc').write_bytes(b'generated')
        runtime.prepare_environment({'CUDA_HOME': '/cuda'}, self.root)
        (self.package / '__init__.py').write_text('unqualified = True\n')
        with self.assertRaisesRegex(RuntimeError, 'source hash changed'):
            runtime.prepare_environment({'CUDA_HOME': '/cuda'}, self.root)

    def test_changed_patch_rejected(self):
        (self.root / 'candidate.patch').write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'patch hash changed'):
            runtime.prepare_environment({'CUDA_HOME': '/cuda'}, self.root)

    def test_project_escape_rejected(self):
        self.config['package_directory'] = '../elsewhere'
        self.save()
        with self.assertRaisesRegex(ValueError, 'project-relative'):
            runtime.prepare_environment({'CUDA_HOME': '/cuda'}, self.root)

    def test_wrong_import_rejected(self):
        with patch.object(runtime, 'ROOT', self.root):
            with self.assertRaisesRegex(RuntimeError, 'unqualified package'):
                runtime.verify_loaded_runtime(self.config, '/tmp/wrong/sglang/__init__.py')

    def test_dependency_version_change_rejected(self):
        with patch.object(runtime, 'ROOT', self.root), patch.object(runtime.importlib.metadata, 'version', return_value='changed'):
            with self.assertRaisesRegex(RuntimeError, 'dependency changed'):
                runtime.verify_loaded_runtime(self.config, self.package / '__init__.py')


if __name__ == '__main__':
    unittest.main()
