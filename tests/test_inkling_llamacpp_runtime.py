"""Inkling's manual fork, measured command, guards and two checkpoint receipts."""
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
import inkling_llamacpp_runtime as runtime
from bolt_iq2_worker import verify_receipts, verify_runtime_files, worker_environment
from daily_engine_update import Updater, validate_update_coverage
from inference_swap_guard import WorkerWatch
from profile_catalog import get_profile, load_catalog
from weights_tracker import claims


class InklingRuntime(unittest.TestCase):
    def setUp(self):
        self.pins = json.loads((ROOT / runtime.MANIFEST).read_text())
        self.profile = get_profile(runtime.PROFILE)

    def test_measured_command(self):
        folder = ROOT / 'models/engine-tests/inkling2-mini-trial'
        self.assertEqual(runtime.build_command(self.pins, port=10007), [
            str(ROOT / 'runtimes/llama.cpp-unsloth/b12588-mix-c0c3de8/llama-server'),
            '-m', str(folder / 'Inkling-2-Mini-UD-Q4_K_M.gguf'), '--mmproj', str(folder / 'mmproj-F16.gguf'),
            '--alias', 'inkling', '--host', '127.0.0.1', '--port', '10007', '--api-key-file',
            str(ROOT / 'data/local-api-key'), '--verbosity', '4', '--jinja', '--split-mode', 'layer', '-ngl', '99',
            '--tensor-split', '13,12', '-fa', 'on', '--ctx-size', '32768', '--parallel', '1',
            '--threads', '8', '--metrics', '--no-webui', '--temp', '1.0', '--top-p', '1.0',
            '--top-k', '0', '--min-p', '0'])

    def test_drift_refused(self):
        for field, value in [('planned_context', 65536), ('tensor_split', [12, 13]),
                             ('binary', 'runtimes/llama.cpp/build/bin/llama-server'),
                             ('runtime_files_sha256', {}), ('mmproj', 'other.gguf')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                runtime.build_command(dict(self.pins, **{field: value}))

    def test_worker_parameters_and_environment(self):
        with patch.object(runtime, 'serve') as worker:
            runtime.main()
        args = worker.call_args.kwargs
        self.assertEqual((args['profile_id'], args['unit'], args['port'], args['latch'], args['capture_engine_log']),
                         (runtime.PROFILE, 'llm-router-worker.service', 10000, True, True))
        self.assertIs(args['command_builder'], runtime.build_command)
        self.assertEqual(args['receipt_files'], (runtime.MODEL, runtime.PROJECTOR))
        prefix = str(ROOT / runtime.RUNTIME) + ':' + str(ROOT / 'runtimes/engine-tools/lib/python3.12/site-packages/nvidia/cu13/lib')
        for existing in ('', '/existing'):
            with patch.dict(os.environ, {'LD_LIBRARY_PATH': existing, 'GGML_CUDA_P2P': '1'}, clear=True):
                env = worker_environment(args['library_dirs'])
                self.assertEqual(env['LD_LIBRARY_PATH'], prefix + (':' + existing if existing else ''))
                self.assertEqual(worker_environment()['LD_LIBRARY_PATH'], existing)
                self.assertNotIn('GGML_CUDA_P2P', env)
                self.assertEqual([env[k] for k in ('CUDA_VISIBLE_DEVICES', 'CUDA_DEVICE_ORDER', 'NCCL_P2P_DISABLE',
                                                  'HF_HUB_OFFLINE')], ['0,1', 'PCI_BUS_ID', '1', '1'])

    def test_binary_and_all_library_hashes_are_checked(self):
        digest = hashlib.sha256(b'fixture').hexdigest()
        self.assertEqual(self.pins['binary_sha256'], 'b695dc3a318e3771f75e491c3df2d0d79812217bad2159d56548a3597a0af97b')
        self.assertEqual(len(self.pins['runtime_files_sha256']), 9)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            libs = dict.fromkeys(self.pins['runtime_files_sha256'], digest)
            pins = dict(self.pins, binary_sha256=digest, runtime_files_sha256=libs)
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

    def test_both_receipts_required_and_checked(self):
        names = (runtime.MODEL, runtime.PROJECTOR)
        self.assertIsNone(self.pins['revision'])
        self.assertEqual([(r['file'], r['bytes']) for r in self.pins['files']],
                         [(names[0], 16610543328), (names[1], 639348160)])
        rows = [dict(r, bytes=1) for r in self.pins['files']]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in names:
                (folder / name).write_bytes(b'x')
            verify_receipts(folder, rows, rows, names)
            for bad in (rows[:1], rows * 2, [rows[0]] * 2, [rows[0], dict(rows[1], bytes=2)],
                        [dict(rows[0], publisher_sha256_matched=False), rows[1]]):
                with self.subTest(receipts=bad), self.assertRaises(ValueError):
                    verify_receipts(folder, bad, bad, names)

    def test_only_selected_trial_files_are_claimed(self):
        entries, _, _ = claims(json.loads((ROOT / 'config/weights-inventory.json').read_text()))
        folder = ROOT / self.profile['storage']['checkpoint_directory']
        self.assertEqual({path for path, _, owner, _ in entries if owner == 'router:' + runtime.PROFILE},
                         {folder / runtime.MODEL, folder / runtime.PROJECTOR})

    def test_pinned_profile_can_reach_short_smoke_admission(self):
        policy = json.loads((ROOT / 'config/daily-update.json').read_text())
        validate_update_coverage(load_catalog(), policy)
        self.assertFalse(any(runtime.PROFILE in c['profiles'] for c in policy['components']))
        with tempfile.TemporaryDirectory() as directory:
            updater = Updater.__new__(Updater)
            updater.policy, updater.base = policy, Path(directory)
            with patch.object(updater, 'recover'), patch.object(updater, 'idle_reserve', return_value=False) as reserve:
                with self.assertRaisesRegex(RuntimeError, 'requires idle'):
                    updater.smoke_current(runtime.PROFILE)
                reserve.assert_called_once_with(manual=True, current_only=True)

    def test_short_qualification_observes_native_queue(self):
        watch = WorkerWatch('/unused', runtime.PROFILE, 'fixture', latch=False)
        self.assertEqual((watch.guard.write_limit, watch.guard.combined_limit, watch.guard.pressure_limit), (1, 8, 10))
        with patch.object(watch, 'get', return_value='llamacpp:requests_processing 0\nllamacpp:requests_deferred 1') as get:
            self.assertEqual(watch.phase(), 'inference')
            get.assert_called_once_with('/metrics')
