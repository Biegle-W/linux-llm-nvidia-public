"""Exercise the installed vision class without importing or starting an inference server."""
import ast
import base64
import contextlib
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'runtimes/project-maya/serve/server.py'


@unittest.skipUnless(SOURCE.is_file(), 'Local Maya runtime is required for this patch regression')
class LazyVision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text())
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Vision')
        namespace = dict(globals())
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
        cls.Vision = namespace['Vision']

    def test_cpu_encoder_starts_for_image_and_stops_after_request(self):
        process = unittest.mock.Mock()
        process.stdout = io.StringIO('READY\nOK 4\n')
        config = {'exe': 'encoder', 'mmproj': 'weights', 'model': 'vocab', 'gpu': False}
        with patch.object(subprocess, 'Popen', return_value=process) as spawn:
            vision = self.Vision(config, start=False)
            self.addCleanup(shutil.rmtree, vision.dir, ignore_errors=True)
            spawn.assert_not_called()
            source = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()
            with vision.active():
                self.assertEqual(vision.encode(source)[1], 4)
                self.assertIs(vision.proc, process)
            self.assertIsNone(vision.proc)
            process.wait.assert_called_once()
            with vision.active():
                self.assertEqual(vision.encode(source)[1], 4)
            self.assertEqual(spawn.call_count, 1)  # Cached embeddings need no new encoder.

    def test_gpu_lending_is_reclaimed_after_on_demand_image_work(self):
        process = unittest.mock.Mock()
        process.stdout = io.StringIO('READY\n')
        with patch.object(subprocess, 'Popen', return_value=process):
            vision = self.Vision({'exe': 'encoder', 'mmproj': 'weights', 'model': 'vocab', 'gpu': True}, start=False)
            self.addCleanup(shutil.rmtree, vision.dir, ignore_errors=True)
            vision.lend = unittest.mock.Mock()
            vision.reclaim = unittest.mock.Mock()
            with vision.active():
                vision._start()
            vision.lend.assert_called_once()
            vision.reclaim.assert_called_once()
            self.assertIsNone(vision.proc)


if __name__ == '__main__':
    unittest.main()
