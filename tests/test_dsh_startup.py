import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DSHStartup(unittest.TestCase):
    def launch(self, headless):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('dsh', 'scripts', 'data', 'runtimes/deepseek-harness/node_modules/@deepseek-ai/dsh/lib'):
                (root / name).mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / 'dsh/run', root / 'dsh/run')
            (root / 'scripts/visible_terminal.py').write_text('raise SystemExit(37)\n')
            (root / 'data/local-api-key').write_text('fixture-only')
            (root / 'runtimes/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js').write_text(
                'console.log(JSON.stringify({args:process.argv.slice(2),home:process.env.DSH_HOME,key:process.env.LOCAL_LLM_API_KEY}));')
            env = dict(os.environ)
            for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'NVIDIA_DSH_HEADLESS'):
                env.pop(key, None)
            if headless is not None:
                env['NVIDIA_DSH_HEADLESS'] = headless
            return subprocess.run([str(root / 'dsh/run'), 'web', '--host', '127.0.0.1', '--port', '3080', '--no-open'],
                                  env=env, capture_output=True, text=True, timeout=10)

    def test_explicit_headless_service_starts_without_display(self):
        result = self.launch('1')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['args'], ['web', '--host', '127.0.0.1', '--port', '3080', '--no-open'])
        self.assertTrue(payload['home'].endswith('/data/dsh'))
        self.assertEqual(payload['key'], 'fixture-only')

    def test_desktop_launch_never_falls_back_after_monitor_failure(self):
        for flag in (None, '0', 'unexpected'):
            with self.subTest(flag=flag):
                result = self.launch(flag)
                self.assertEqual(result.returncode, 37)
                self.assertEqual(result.stdout, '')

    def test_installer_reproduces_loopback_headless_client_unit(self):
        spec = importlib.util.spec_from_file_location('dsh_network_install', ROOT / 'network/install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        unit = installer.dsh_service_unit(Path('/fixture'))
        for required in ('Environment=NVIDIA_DSH_HEADLESS=1', '--host 127.0.0.1 --port 3080 --no-open',
                         'UMask=0077', 'NoNewPrivileges=true', 'MemoryMax=2G',
                         'StandardOutput=append:/fixture/data/dsh-web.log',
                         'StandardError=append:/fixture/data/dsh-web.log'):
            self.assertIn(required, unit)
        self.assertNotIn('PartOf=', unit)


if __name__ == '__main__':
    unittest.main()
