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

class VideoResolutionTests(unittest.TestCase):
    def module(self):
        spec=importlib.util.spec_from_file_location('video_resolution_test',ROOT/'scripts/comfy_video_trial.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def test_exact_hd_output_uses_padded_native_latents_and_crop(self):
        module=self.module()
        for stage in ('baseline','raylight','mesh'):
            for width,height,render_height in ((1280,720,736),(1920,1080,1088)):
                graph=module.graph(stage,27001,width,height)
                self.assertEqual(graph['4']['inputs']['width'],width)
                self.assertEqual(graph['4']['inputs']['height'],render_height)
                self.assertEqual(graph['23']['inputs'],dict(image=['8',0],width=width,height=height,x=0,y=0))
                self.assertEqual(graph['10']['inputs']['images'],['23',0])
                if stage=='raylight':
                    self.assertEqual(graph['8']['class_type'],'VAEDecodeTiled')
                    self.assertEqual(graph['8']['inputs']['tile_size'],256)
    def test_selected_low_resolution_graphs_remain_unchanged(self):
        module=self.module()
        for stage in ('baseline','raylight','mesh'):
            self.assertEqual(module.graph(stage,27001),module._graph(stage,27001))
    def test_unreviewed_benchmark_dimensions_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Unreviewed'):
            self.module().graph('mesh',27001,3840,2160)

    def test_synchronized_ray_retry_is_explicit_and_gpu_only(self):
        module=self.module();graph=module.graph('raylight',27001,1920,1080,sync_ulysses=True)
        self.assertTrue(graph['11']['inputs']['sync_ulysses'])
        self.assertFalse(graph['11']['inputs']['FSDP_CPU_OFFLOAD'])
        self.assertFalse(module.graph('raylight',27001)['11']['inputs']['sync_ulysses'])
