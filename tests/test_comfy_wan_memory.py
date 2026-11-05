"""Guidance branches must not be batched differently on unequal GPU ranks."""
import importlib.util
import ast
from contextlib import nullcontext
from pathlib import Path
import sys
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class WanMemoryTests(unittest.TestCase):
    def test_cfg_branches_run_separately_without_changing_combination_inputs(self):
        helper=module('wan_memory_test','scripts/comfy_wan_memory.py');calls=[]
        def calc(model,conds,value,sigma,options):
            calls.append((model,conds,value,sigma,options));return ['result:'+str(conds[0])]
        parent=ModuleType('comfy');samplers=ModuleType('comfy.samplers');samplers.calc_cond_batch=calc;parent.samplers=samplers
        options={'retained':'value'};args=dict(model='model',conds=['positive','negative'],input='latent',sigma='sigma',model_options=options)
        with patch.dict(sys.modules,{'comfy':parent,'comfy.samplers':samplers}):result=helper.sequential_cfg(args)
        self.assertEqual(result,['result:positive','result:negative'])
        self.assertEqual([call[1] for call in calls],[['positive'],['negative']])
        self.assertTrue(all(call[4] is options for call in calls));self.assertEqual(args['conds'],['positive','negative'])
    def test_hd_native_path_selects_sequential_cfg_and_gpu_tiles_only(self):
        trial=module('wan_graph_test','scripts/comfy_video_trial.py');graph=trial.graph('baseline',27001,1920,1080)
        self.assertEqual(graph['1']['class_type'],'NvidiaWanSplitDenoiser')
        self.assertEqual(graph['24']['class_type'],'NvidiaWanSequentialCFG')
        self.assertEqual(graph['7']['inputs']['model'],['24',0])
        self.assertEqual(graph['8']['class_type'],'VAEDecodeTiled')
        self.assertNotIn('24',trial.graph('baseline',27001))

    def test_remote_block_moves_activations_without_cpu_weight_offload(self):
        class Tensor:
            def __init__(self,device):self.device=device
            def to(self,device):
                self.assert_cuda(device);return Tensor(device)
            def assert_cuda(self,device):
                if not device.startswith('cuda:'):raise AssertionError('CPU transfer forbidden')
        class Module:
            def __init__(self):self._modules={}
        calls=[]
        def resident(value,**kwargs):calls.append((value,kwargs));return value
        tree=ast.parse((ROOT/'scripts/comfy_video_nodes/__init__.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ResidentWanBlock')
        namespace={'torch':SimpleNamespace(Tensor=Tensor,nn=SimpleNamespace(Module=Module),cuda=SimpleNamespace(device=lambda index:nullcontext()))};exec(compile(ast.Module(body=[node],type_ignores=[]),'remote_block','exec'),namespace)
        block=namespace['ResidentWanBlock'](resident,last=True)
        output=block.forward(Tensor('cuda:0'),context={'nested':[Tensor('cuda:0')]})
        self.assertEqual(calls[0][0].device,'cuda:1')
        self.assertEqual(calls[0][1]['context']['nested'][0].device,'cuda:1')
        self.assertEqual(output.device,'cuda:0');self.assertEqual(block._modules,{})
