import hashlib,json,sys,tempfile,unittest,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bolt_runtime import build_launch,verify
from supervise_bolt import resource_fault
class Runtime(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.r=Path(self.temp.name)
  for p in ['config','models/bolt','runtimes/bin']:(self.r/p).mkdir(parents=True)
  (self.r/'runtimes/bin/vllm').write_text('fixture runtime');(self.r/'models/bolt/weights.safetensors').write_bytes(b'weights')
  (self.r/'models/bolt/config.json').write_text(json.dumps({'quantization_config':{'config_groups':{'g':{'targets':['re:experts.(?:up_proj|down_proj)']}}}}))
  digest=lambda p:hashlib.sha256((self.r/p).read_bytes()).hexdigest()
  self.manifest={'schema':1,'context':8192,'gpu_indices':[0,1],'model_directory':'models/bolt','binary':'runtimes/bin/vllm','prefill_batch_tokens':1024,'runtime_sha256':{'runtimes/bin/vllm':digest('runtimes/bin/vllm')},'model_source_sha256':{'config.json':digest('models/bolt/config.json')},'weight_sizes':{'weights.safetensors':7}}
  self.p={'id':'bolt-vllm','engine':'vLLM-offload','allocated_context':8192,'storage':{'checkpoint_directory':'models/bolt'}};self.save()
 def save(self):(self.r/'config/bolt-offload-runtime.json').write_text(json.dumps(self.manifest))
 def test_scoped_placement_offline_auth_and_context(self):
  args,env=build_launch(self.p,'fixture',self.r);self.assertEqual(args[args.index('--max-model-len')+1],'8192');self.assertEqual(args[args.index('--max-num-batched-tokens')+1],'1024');self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'0,1');self.assertEqual(env['HF_HUB_OFFLINE'],'1');self.assertEqual(env['VLLM_API_KEY'],'fixture');self.assertEqual(env['BOLT_CHECKPOINT_DIRECTORY'],str(self.r/'models/bolt'));self.assertNotIn('--api-key',args);self.assertNotIn('--cpu-offload-gb',args);self.assertIn('--enforce-eager',args)
 def test_runtime_drift_fails_closed(self):
  (self.r/'runtimes/bin/vllm').write_text('changed')
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_model_drift_fails_closed(self):
  (self.r/'models/bolt/config.json').write_text('{}')
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_weight_size_drift_fails_closed(self):
  (self.r/'models/bolt/weights.safetensors').write_bytes(b'drift')
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_context_and_gpu_contract(self):
  p=copy.deepcopy(self.p);p['allocated_context']=32768
  with self.assertRaises(ValueError):verify(p,self.r)
  self.manifest['gpu_indices']=[0,1,2];self.save()
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_traversal_rejected(self):
  self.manifest['runtime_sha256']={'../escape':'unused'};self.save()
  with self.assertRaises(ValueError):verify(self.p,self.r)
class Guards(unittest.TestCase):
 def test_reserve_and_temperature_boundaries(self):
  c=[[81,512],[81,512],[81,512]];self.assertFalse(resource_fault(2**21,c,2**21));self.assertTrue(resource_fault(2**21-1,c,2**21));c[1][1]=511;self.assertTrue(resource_fault(2**21,c,2**21));c[1]=[82,1024];self.assertTrue(resource_fault(2**21,c,2**21))
 def test_invalid_inventory_and_nan_fail_closed(self):
  for c in [[[30,1000]],[[30,float('nan')],[30,1000],[30,1000]]]:
   with self.assertRaises(ValueError):resource_fault(2**21,c,2**21)
if __name__=='__main__':unittest.main()
