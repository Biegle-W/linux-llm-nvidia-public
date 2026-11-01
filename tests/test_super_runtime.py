import copy,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from super_runtime import build_launch,verify
class Runtime(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.r=Path(self.temp.name)
  for name in ['config','models/super','runtimes/bin','data']:(self.r/name).mkdir(parents=True)
  (self.r/'runtimes/bin/python').write_text('fixture runtime');(self.r/'models/super/config.json').write_text('{}');(self.r/'models/super/weights.safetensors').write_bytes(b'weights')
  h=lambda p:hashlib.sha256((self.r/p).read_bytes()).hexdigest()
  self.m={'schema':1,'profile':'super-vllm','context':65536,'gpu_indices':[0,1],'model_directory':'models/super','binary':'runtimes/bin/python','prefill_batch_tokens':256,'kv_cache_mib_per_gpu':384,'resident_expert_layers':'6,1','cpu_input_projection_counts':'12,20','gpu_output_projection_counts':'0,40','file_backing_mib_per_rank':2048,'processed_backing_directory':'data/backing','runtime_sha256':{'runtimes/bin/python':h('runtimes/bin/python')},'model_source_sha256':{'config.json':h('models/super/config.json')},'weight_sizes':{'weights.safetensors':7}}
  self.p={'id':'super-vllm','engine':'vLLM-offload','allocated_context':65536,'storage':{'checkpoint_directory':'models/super','processed_backing_directory':'data/backing','processed_backing_transport':'nvme'}};self.save()
  self.transport=patch('super_runtime.subprocess.check_output',side_effect=lambda argv,**kw:'/dev/fixture1\n' if argv[0]=='findmnt' else 'part\ndisk nvme\n');self.transport.start();self.addCleanup(self.transport.stop)
  self.env=patch.dict(os.environ,{'INVOCATION_ID':'1'*32});self.env.start();self.addCleanup(self.env.stop)
 def save(self):(self.r/'config/super-offload-runtime.json').write_text(json.dumps(self.m))
 def test_launch_preserves_qualified_placement_bounds_and_auth(self):
  args,env=build_launch(self.p,'fixture',self.r)
  for flag,value in [('--max-model-len','65536'),('--max-num-seqs','1'),('--max-num-batched-tokens','256'),('--kv-cache-memory-bytes',str(384*2**20)),('--tool-call-parser','qwen3_coder')]:self.assertEqual(args[args.index(flag)+1],value)
  self.assertIn('--enable-expert-parallel',args);self.assertIn('--no-enable-prefix-caching',args);self.assertIn('--language-model-only',args);self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'0,1');self.assertEqual(env['SUPER_FILE_BACKING_MIB_PER_RANK'],'2048');self.assertEqual(env['SUPER_INPUT_OFFLOAD_COUNTS'],'12,20');self.assertEqual(env['SUPER_OUTPUT_RESIDENT_COUNTS'],'0,40');self.assertEqual(env['VLLM_API_KEY'],'fixture');self.assertEqual(env['VLLM_USE_FLASHINFER_SAMPLER'],'0');self.assertNotIn('--api-key',args);self.assertEqual(json.loads(args[args.index('--default-chat-template-kwargs')+1]),{'enable_thinking':False})
 def test_runtime_source_drift_rejected(self):
  (self.r/'runtimes/bin/python').write_text('changed')
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_checkpoint_source_and_weight_size_drift_rejected(self):
  (self.r/'models/super/config.json').write_text('{"changed":true}')
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_weight_size_drift_rejected(self):
  (self.r/'models/super/weights.safetensors').write_bytes(b'changed-size')
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_context_drift_rejected(self):
  self.p['allocated_context']=16384
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_unqualified_backing_cap_rejected(self):
  self.m['file_backing_mib_per_rank']=2049;self.save()
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_backing_on_sata_rejected(self):
  with patch('super_runtime.subprocess.check_output',side_effect=['/dev/fixture1\n','part\ndisk sata\n']),self.assertRaisesRegex(ValueError,'requires NVMe'):verify(self.p,self.r)
 def test_path_escape_rejected(self):
  self.m['processed_backing_directory']='../escape';self.p['storage']['processed_backing_directory']='../escape';self.save()
  with self.assertRaises(ValueError):verify(self.p,self.r)
 def test_existing_backing_ownership_path_rejected(self):
  (self.r/'data/backing'/('router-'+'1'*32)).mkdir(parents=True)
  with self.assertRaisesRegex(ValueError,'already exists'):build_launch(self.p,'fixture',self.r)
if __name__=='__main__':unittest.main()
