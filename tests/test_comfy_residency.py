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

    def test_h3_selected_encoder_allowed(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='minimax-h3-image'):
            self.assertIn('qwen3vl_32b',self.selected_file('text_encoders','qwen3vl_32b_minimax_h3_int8_convrot.safetensors'))

    def test_h3_encoder_rejected_for_other_models(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='flux3-klein'):
            with self.assertRaisesRegex(AssertionError,'matching model launcher'):
                self.selected_file('text_encoders','qwen3vl_32b_minimax_h3_int8_convrot.safetensors')

    def test_unpinned_model_rejected(self):
        with patch.dict(os.environ,COMFY_MODEL_ID='flux3-klein'):
            with self.assertRaises(AssertionError):self.selected_file('vae','unreviewed.safetensors')


class EncoderExceptionTests(unittest.TestCase):
    """The RAM-streamed encoder exception is per patcher; everything else keeps the all-on-GPU audit."""
    def setUp(self):
        tree=ast.parse((ROOT/'scripts/comfy_nodes/__init__.py').read_text())
        wanted=('encoder_mode','register_encoder')
        functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in wanted]
        audits=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='audit']
        self.assertEqual(len(audits),2)
        import weakref
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.log=Path(self.temp.name)/'placement.jsonl'
        self.env=patch.dict(os.environ,COMFY_PLACEMENT_LOG=str(self.log));self.env.start();self.addCleanup(self.env.stop)
        namespace=dict(json=json,os=os,Path=Path,time=time,weakref=weakref,CPU='cpu',GPU1='cuda:1',GiB=1024**3,ENCODER_BUDGET=4*1024**3,_encoder_policy={})
        exec(compile(ast.Module(body=[audits[0]],type_ignores=[]),'audit','exec'),namespace)
        namespace['_resident_audit']=namespace['audit']
        exec(compile(ast.Module(body=functions+[audits[1]],type_ignores=[]),'audit','exec'),namespace)
        self.ns=namespace

    class Patcher:
        def __init__(self,load,offload,devices,loaded=0):
            self.load_device=load;self.offload_device=offload;self._loaded=loaded
            tensors=[SimpleNamespace(device=d,numel=lambda:1024) for d in devices]
            self.model=SimpleNamespace(parameters=lambda:tensors,model_lowvram=True)
        def loaded_size(self):return self._loaded

    def test_registered_stream_encoder_passes(self):
        p=self.Patcher('cuda:1','cpu',['cpu','cuda:1'],loaded=1024**3)
        self.ns['register_encoder'](p,'stream');self.ns['audit'](p)
        self.assertEqual(json.loads(self.log.read_text())['encoder_exception'],'stream')

    def test_unregistered_cpu_offload_still_rejected(self):
        with self.assertRaisesRegex(AssertionError,'CPU offload'):self.ns['audit'](self.Patcher('cuda:1','cpu',['cpu']))

    def test_stream_encoder_on_wrong_gpu_rejected(self):
        p=self.Patcher('cuda:1','cpu',['cpu','cuda:0']);self.ns['register_encoder'](p,'stream')
        with self.assertRaisesRegex(AssertionError,'Unexpected encoder placement'):self.ns['audit'](p)

    def test_stream_encoder_over_budget_rejected(self):
        p=self.Patcher('cuda:1','cpu',['cpu','cuda:1'],loaded=6*1024**3);self.ns['register_encoder'](p,'stream')
        with self.assertRaisesRegex(AssertionError,'GPU budget'):self.ns['audit'](p)

    def test_exception_is_not_inherited_by_another_patcher(self):
        p=self.Patcher('cuda:1','cpu',['cpu']);self.ns['register_encoder'](p,'stream')
        other=self.Patcher('cuda:1','cpu',['cpu'])
        with self.assertRaisesRegex(AssertionError,'CPU offload'):self.ns['audit'](other)


if __name__=='__main__':unittest.main()
