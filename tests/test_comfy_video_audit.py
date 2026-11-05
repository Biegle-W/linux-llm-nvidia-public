"""Check that FSDP pre-hooks run before residency enforcement."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class VideoAuditTests(unittest.TestCase):
    def run_module(self, materialize):
        class Module:
            def __init__(self):self.device='cpu';self.computed=False
            def parameters(self,recurse=False):
                return [SimpleNamespace(device=self.device,numel=lambda:1)]
            def forward(self):self.computed=True;return 42
            def _call_impl(self):
                forward=self.forward
                if materialize:self.device='cuda:0'
                return forward()
        with tempfile.TemporaryDirectory() as directory:
            fake=SimpleNamespace(nn=SimpleNamespace(Module=Module))
            with patch.dict(sys.modules,torch=fake),patch.dict(os.environ,COMFY_VIDEO_AUDIT_DIR=directory,CUDA_VISIBLE_DEVICES='1'):
                spec=importlib.util.spec_from_file_location('video_audit_test',ROOT/'scripts/comfy_video_hook/sitecustomize.py')
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                model=Module()
                if materialize:self.assertEqual(model._call_impl(),42)
                else:
                    with self.assertRaisesRegex(RuntimeError,'CPU/meta'):model._call_impl()
                    self.assertFalse(model.computed)
                rows=[json.loads(line) for p in Path(directory).glob('*.jsonl') for line in p.read_text().splitlines()]
                self.assertEqual(rows[0]['CUDA_VISIBLE_DEVICES'],'1')
                self.assertEqual(rows[0]['devices'],['cuda:0' if materialize else 'cpu'])
    def test_pre_hook_materialization_precedes_audit(self):self.run_module(True)
    def test_cpu_forward_still_rejected(self):self.run_module(False)

class MeshMetadataTests(unittest.TestCase):
    def test_full_checkpoint_metadata_cannot_restore_remote_blocks(self):
        spec=importlib.util.spec_from_file_location('mesh_gguf_test',ROOT/'scripts/comfy_mesh_gguf.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        original={'config':json.dumps({'transformer':{'num_layers':48,'attention_head_dim':128}})}
        slim=module.slim_metadata(original,20)
        self.assertEqual(json.loads(slim['config'])['transformer'],{'num_layers':20,'attention_head_dim':128})
        self.assertEqual(json.loads(original['config'])['transformer']['num_layers'],48)

class VideoGraphTests(unittest.TestCase):
    def test_all_trial_graphs_build_before_acquiring_gpus(self):
        spec=importlib.util.spec_from_file_location('video_graph_test',ROOT/'scripts/comfy_video_trial.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for stage in ('prepare','baseline','raylight','mesh-prepare','mesh'):
            graph=module.graph(stage,27001)
            for node in graph.values():
                for value in node['inputs'].values():
                    if isinstance(value,list):self.assertIn(value[0],graph)
