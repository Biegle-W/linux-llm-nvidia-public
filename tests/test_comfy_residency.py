"""CPU checks for the diffusion placement gate; no GPU model is loaded."""
import ast
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class ResidencyTests(unittest.TestCase):
    def setUp(self):
        tree=ast.parse((ROOT/'scripts/comfy_nodes/__init__.py').read_text())
        function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='audit')
        namespace=dict(json=json,os=os,Path=Path,time=time)
        exec(compile(ast.Module(body=[function],type_ignores=[]),'audit','exec'),namespace)
        self.audit=namespace['audit']
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log=Path(self.temp.name)/'placement.jsonl'
        self.env=patch.dict(os.environ,COMFY_PLACEMENT_LOG=str(self.log));self.env.start();self.addCleanup(self.env.stop)

    def model(self,device='cuda:1',offload='cuda:1',parameter='cuda:1',low=False):
        tensor=SimpleNamespace(device=parameter,numel=lambda:1024)
        model=SimpleNamespace(parameters=lambda:[tensor],model_lowvram=low)
        return SimpleNamespace(load_device=device,offload_device=offload,model=model)

    def test_gpu_parameters_logged(self):
        self.audit(self.model())
        self.assertEqual(json.loads(self.log.read_text())['parameter_elements_by_device'],{'cuda:1':1024})

    def test_cpu_offload_rejected(self):
        with self.assertRaisesRegex(AssertionError,'CPU offload'):self.audit(self.model(offload='cpu'))

    def test_cpu_weights_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Nonresident'):self.audit(self.model(parameter='cpu'))

    def test_wrong_gpu_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Nonresident'):self.audit(self.model(parameter='cuda:0'))

    def test_partial_load_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Partial'):self.audit(self.model(low=True))

    def test_unexpected_device_rejected(self):
        with self.assertRaises(AssertionError):self.audit(self.model(device='cpu'))


class OwnershipTests(unittest.TestCase):
    def check(self, **changes):
        tree=ast.parse((ROOT/'scripts/comfy_run.py').read_text())
        function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='ended_unit')
        values=dict(InvocationID='',ActiveState='inactive',MainPID='0',ControlGroup='')
        values.update(changes)
        namespace=dict(UNIT='owned.service',property_of=lambda unit,key:values[key])
        exec(compile(ast.Module(body=[function],type_ignores=[]),'ownership','exec'),namespace)
        return namespace['ended_unit']()

    def test_collected_worker_releases(self):self.assertTrue(self.check())
    def test_replacement_invocation_preserved(self):self.assertFalse(self.check(InvocationID='another-invocation'))
    def test_running_worker_preserved(self):self.assertFalse(self.check(ActiveState='active',MainPID='123'))
    def test_remaining_cgroup_preserved(self):self.assertFalse(self.check(ControlGroup='/still-owned'))


class SelectionTests(unittest.TestCase):
    def setUp(self):
        source=ROOT/'scripts/comfy_nodes/__init__.py'
        tree=ast.parse(source.read_text())
        function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='selected_file')
        namespace=dict(__file__=str(source),Path=Path,json=json,os=os,
                       folder_paths=SimpleNamespace(get_full_path_or_raise=lambda category,name:category+'/'+name))
        exec(compile(ast.Module(body=[function],type_ignores=[]),'selection','exec'),namespace)
        self.selected_file=namespace['selected_file']

    def test_qwen_selected_checkpoint_allowed(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='qwen-image-2.1-turbo'):
            self.assertIn('qwen_image_2.1',self.selected_file('diffusion_models','qwen_image_2.1_turbo_int8_convrot.safetensors'))

    def test_flux_selected_encoder_allowed(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='flux3-klein'):
            self.assertIn('qwen3vl_4b',self.selected_file('text_encoders','qwen3vl_4b_int8_convrot.safetensors'))

    def test_cross_profile_load_requires_restart(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='qwen-image-2.1-turbo'):
            with self.assertRaisesRegex(AssertionError,'matching model launcher'):
                self.selected_file('diffusion_models','flux3-image-klein-int8-convrot.safetensors')

    def test_unpinned_model_rejected(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='flux3-klein'):
            with self.assertRaises(AssertionError):self.selected_file('vae','unreviewed.safetensors')


if __name__=='__main__':unittest.main()
