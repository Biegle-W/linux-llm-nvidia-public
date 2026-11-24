"""Offline checks for Kolibri's trial command, receipts and router integration."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import kolibri_llamacpp_runtime as runtime
from daily_engine_update import validate_update_coverage
from llamacpp_worker import verify_receipts, verify_runtime_files, worker_environment
from profile_catalog import get_profile, load_catalog
from weights_tracker import claims


class KolibriRuntime(unittest.TestCase):
    def setUp(self):
        self.profile = get_profile(runtime.PROFILE)
        self.pins = json.loads((ROOT / runtime.MANIFEST).read_text())

    def test_measured_command_and_registry_changes(self):
        cmd = runtime.build_command(self.profile, self.pins, port=10007)
        self.assertEqual(cmd, [
            str(ROOT / self.pins['binary']), '-m', str(ROOT / self.pins['checkpoint_directory'] / runtime.MODEL),
            '-ngl', '99', '-sm', 'layer', '--tensor-split', '12,10',
            '-ot', r'blk\.([7-9]|[1-3][0-9]|4[0-4])\.ffn_(up|down|gate)_exps\.weight=CPU',
            '-c', '131072', '-np', '1', '-b', '2048', '-ub', '2048', '-fa', 'on',
            '-ctk', 'f16', '-ctv', 'f16', '--jinja', '--reasoning-format', 'deepseek', '--temp', '1.0',
            '--top-p', '0.99', '--top-k', '128', '--min-p', '0', '--chat-template-kwargs',
            '{"reasoning_effort":"none","enable_thinking":false}', '--no-webui', '--host', '127.0.0.1',
            '--port', '10007', '--alias', 'kolibri', '--api-key-file', str(ROOT / 'data/local-api-key'),
            '--metrics', '--verbosity', '4'])
        self.profile['selected_settings']['batch'] = 1024
        self.assertEqual(runtime.build_command(self.profile, self.pins)[cmd.index('-b') + 1], '1024')
        self.profile['allocated_context'] = 16384
        with self.assertRaises(ValueError):
            runtime.build_command(self.profile, self.pins)

    def test_worker_uses_pinned_libraries_on_both_cards(self):
        with patch.object(runtime, 'serve') as worker:
            runtime.main(self.profile)
        args = worker.call_args.kwargs
        self.assertIs(args['command_builder'], runtime.build_command)
        self.assertEqual(args['receipt_files'], (runtime.MODEL,))
        with patch.dict(os.environ, {'GGML_CUDA_P2P': '1', 'LD_LIBRARY_PATH': '/existing'}, clear=True):
            env = worker_environment(args['library_dirs'])
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'], '0,1')
        self.assertEqual(env['NCCL_P2P_DISABLE'], '1')
        self.assertNotIn('GGML_CUDA_P2P', env)
        self.assertEqual(env['LD_LIBRARY_PATH'].split(os.pathsep),
                         [str(ROOT / runtime.RUNTIME), '/usr/lib/x86_64-linux-gnu', '/existing'])

    def test_binary_and_eight_library_hashes(self):
        digest = hashlib.sha256(b'fixture').hexdigest()
        libs = dict.fromkeys(self.pins['runtime_files_sha256'], digest)
        self.assertEqual(len(libs), 8)
        pins = dict(self.pins, binary_sha256=digest, runtime_files_sha256=libs)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / runtime.RUNTIME).mkdir(parents=True)
            for name in [pins['binary'], *libs]:
                (root / name).write_bytes(b'fixture')
            verify_runtime_files(root, pins)
            for name in [pins['binary'], *libs]:
                with self.subTest(name=name):
                    (root / name).write_bytes(b'drift')
                    with self.assertRaisesRegex(ValueError, 'SHA-256'):
                        verify_runtime_files(root, pins)
                    (root / name).write_bytes(b'fixture')
        libs.popitem()
        with self.assertRaisesRegex(ValueError, 'runtime'):
            runtime.build_command(self.profile, pins)

    def test_checkpoint_size_and_publisher_receipt(self):
        receipt, = self.pins['files']
        self.assertEqual((receipt['file'], receipt['bytes']), (runtime.MODEL, 53394217408))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / runtime.MODEL).write_bytes(b'x')
            row = dict(receipt, bytes=1)
            verify_receipts(folder, [row], (runtime.MODEL,))
            for invalid in ([receipt], [], [row, row], [dict(row, publisher_sha256_matched=False)]):
                with self.subTest(receipts=invalid), self.assertRaises(ValueError):
                    verify_receipts(folder, invalid, (runtime.MODEL,))

    def test_router_owns_only_selected_weights_and_updater_skips_engine(self):
        inventory = json.loads((ROOT / 'config/weights-inventory.json').read_text())
        entries, _, _ = claims(inventory)
        self.assertEqual([p for p, _, owner, _ in entries if owner == 'router:' + runtime.PROFILE],
                         [ROOT / self.profile['storage']['checkpoint_directory'] / runtime.MODEL])
        policy = json.loads((ROOT / 'config/daily-update.json').read_text())
        validate_update_coverage(load_catalog(), policy)
        self.assertFalse(any(runtime.PROFILE in c['profiles'] for c in policy['components']))
