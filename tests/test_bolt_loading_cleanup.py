import contextlib,io,os,runpy,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parents[1]/'scripts'
class PluginTests(unittest.TestCase):
 def check_context(self,cuda=True,fail=False,early=True):
  events=[]
  @contextlib.contextmanager
  def original(layer,device):
   events.append('enter')
   try:yield layer
   finally:events.append('exit')
  class Base:
   def exec_module(self,m):m.device_loading_context=original
  fake=types.SimpleNamespace(cuda=types.SimpleNamespace(empty_cache=lambda:events.append('trim'),memory_allocated=lambda _:1,memory_reserved=lambda _:2))
  off=types.SimpleNamespace(module_offloaders=[types.SimpleNamespace(sync_cpu_storage=lambda:events.append('sync'))])
  modules={'checkpoint_cache':types.SimpleNamespace(release_once=lambda:events.append('cache')),'host_trim':types.SimpleNamespace(trim_host_pages=lambda _:events.append('host-trim')),'torch':fake,'vllm.model_executor.offloader':types.SimpleNamespace(get_offloader=lambda:off)}
  before=list(sys.meta_path)
  try:
   with patch.dict(os.environ,{'BOLT_POSTLOAD_CACHE_TRIM':'1','BOLT_PREFETCH_EARLY_SYNC':'1' if early else '0'}),patch.dict(sys.modules,modules),contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path(str(B/'bolt_offload_hook/sitecustomize.py'));m=types.SimpleNamespace();ns['Loader'](Base()).exec_module(m)
    try:
     with m.device_loading_context(object(),types.SimpleNamespace(type='cuda' if cuda else 'cpu')):
      events.append('body')
      if fail:raise ValueError('expected')
    except ValueError:
     if not fail:raise
  finally:sys.meta_path[:]=before
  self.assertEqual(events,(['cache','trim','enter','body','exit']+(['sync'] if early else [])+['trim','host-trim']) if cuda else ['enter','body','exit'])
 def test_trim_after_restoration(self):self.check_context()
 def test_exception_preserves_cleanup(self):self.check_context(fail=True)
 def test_cpu_context_unchanged(self):self.check_context(cuda=False)
 def test_trim_without_prefetch_sync(self):self.check_context(early=False)
 def test_disabled_plugin_does_not_install_hook(self):
  before=list(sys.meta_path)
  with patch.dict(os.environ,{'BOLT_POSTLOAD_CACHE_TRIM':'0'}):runpy.run_path(str(B/'bolt_offload_hook/sitecustomize.py'))
  self.assertEqual(before,sys.meta_path)
class HostAllocator(unittest.TestCase):
 def test_live_tensor_survives_real_allocator_trim(self):
  sys.path.insert(0,str(B/'bolt_offload_hook'))
  import torch
  from host_trim import trim_host_pages
  tensor=torch.arange(10000,dtype=torch.int64);expected=tensor.clone();pointer=tensor.data_ptr()
  with contextlib.redirect_stdout(io.StringIO()):result=trim_host_pages('cpu-regression',min_free_bytes=0)
  self.assertEqual(tensor.data_ptr(),pointer);self.assertTrue(torch.equal(tensor,expected));self.assertIn(result['released'],[0,1])
 def test_below_threshold_skips_allocator_call(self):
  sys.path.insert(0,str(B/'bolt_offload_hook'))
  from host_trim import trim_host_pages
  self.assertIsNone(trim_host_pages('skip',min_free_bytes=2**63))
class CheckpointCache(unittest.TestCase):
 def module(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('cache_fixture',B/'bolt_offload_hook/checkpoint_cache.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def fixture(self,root):
  for i in range(27):(root/f'model-{i:05d}.safetensors').write_bytes(b'fixture weight bytes')
  (root/'unrelated.txt').write_bytes(b'preserve')
 def test_readonly_model_scoped_advice_once_preserves_file_bytes(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);m=self.module();m.CHECKPOINT_BYTES=27*len(b'fixture weight bytes')
   with patch.object(m.os,'posix_fadvise',wraps=os.posix_fadvise) as advise,contextlib.redirect_stdout(io.StringIO()):
    m.release_once(root);m.release_once(root);self.assertEqual(advise.call_count,27)
    for args in advise.call_args_list:self.assertEqual(args.args[1:],(0,0,os.POSIX_FADV_DONTNEED))
   self.assertTrue(all(p.read_bytes()==b'fixture weight bytes' for p in root.glob('*.safetensors')));self.assertEqual((root/'unrelated.txt').read_bytes(),b'preserve')
 def test_incomplete_or_changed_checkpoint_rejected_before_advice(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);m=self.module()
   with patch.object(m.os,'posix_fadvise') as advise:
    with self.assertRaises(ValueError):m.release_once(root)
    self.fixture(root)
    with self.assertRaises(ValueError):m.release_once(root)
    advise.assert_not_called()
class ShardIterator(unittest.TestCase):
 def test_same_tensor_order_and_options_with_scoped_advice(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);test=CheckpointCache();test.fixture(root);m=test.module();m.CHECKPOINT_BYTES=27*len(b'fixture weight bytes');events=[];objects={p.name:object() for p in root.glob('*.safetensors')}
   def original(files,progress,strategy,ids,**kwargs):
    self.assertFalse(progress);self.assertIsNone(strategy);self.assertEqual(ids,{7});self.assertEqual(kwargs,{'safetensors_prefetch_num_threads':2})
    p=Path(files[0]);events.append(('start',p.name));yield p.name,objects[p.name];events.append(('end',p.name))
   mod=types.SimpleNamespace(safetensors_weights_iterator=original,_natural_sort_key=str);m.install_iterator(mod)
   with patch.dict(os.environ,{'BOLT_CHECKPOINT_DIRECTORY':str(root)}),patch.object(m,'advise_file',side_effect=lambda p:events.append(('advice',Path(p).name))),contextlib.redirect_stdout(io.StringIO()):
    got=[]
    for name,value in mod.safetensors_weights_iterator(list(reversed(list(root.glob('*.safetensors')))),True,None,{7},safetensors_prefetch_num_threads=2):events.append(('consume',name));got.append((name,value))
   self.assertEqual([name for name,value in got],sorted(objects));self.assertTrue(all(value is objects[name] for name,value in got));self.assertGreaterEqual(sum(kind=='advice' for kind,name in events),54)
   self.assertLess(events.index(('consume','model-00000.safetensors')),events.index(('advice','model-00000.safetensors'),27))
 def test_unsupported_load_strategy_rejected(self):
  m=CheckpointCache().module();mod=types.SimpleNamespace(safetensors_weights_iterator=lambda *a:iter([]),_natural_sort_key=str);m.install_iterator(mod)
  with self.assertRaises(ValueError):list(mod.safetensors_weights_iterator([],False,'torchao'))
if __name__=='__main__':unittest.main()
