from pathlib import Path
import sys,unittest,types
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/bolt_offload_hook'))
import torch
from compact_pool import initialize
class Info:
 def __init__(self,name,shape,stride,dtype=torch.float32):self.name=name;self.shape=shape;self.stride=stride;self.dtype=dtype
 @property
 def key(self):return (self.name,self.shape,self.stride,self.dtype)
class Pool:
 def __init__(self,infos,slots=1):initialize(self,infos,slots,'cpu')
 def get(self,info,slot=0):return self._buffers[info.key][slot%self.slot_capacity]
class Tests(unittest.TestCase):
 def test_same_name_reuses_capacity_across_shapes(self):
  a=Info('w',(4,8),(8,1));b=Info('w',(2,4),(4,1));p=Pool([a,b]);self.assertEqual(p.total_bytes,128);self.assertEqual(p.get(a).untyped_storage().data_ptr(),p.get(b).untyped_storage().data_ptr())
 def test_sequential_stages_have_reference_linear_results(self):
  a=Info('w',(4,8),(8,1));b=Info('w',(2,4),(4,1));p=Pool([a,b]);g=torch.Generator().manual_seed(71)
  for info in [a,b,a,b]:
   w=torch.randn(info.shape,generator=g);x=torch.randn((3,info.shape[1]),generator=g);p.get(info).copy_(w);torch.testing.assert_close(torch.nn.functional.linear(x,p.get(info)),torch.nn.functional.linear(x,w),rtol=0,atol=0)
 def test_distinct_fields_do_not_alias(self):
  a=Info('w1',(2,4),(4,1));b=Info('w2',(2,4),(4,1));p=Pool([a,b]);p.get(a).fill_(1);p.get(b).fill_(2);self.assertTrue(torch.all(p.get(a)==1));self.assertNotEqual(p.get(a).data_ptr(),p.get(b).data_ptr())
 def test_slots_independent_for_different_shapes(self):
  a=Info('w',(4,8),(8,1));b=Info('w',(2,4),(4,1));p=Pool([a,b],2);p.get(a,0).fill_(1);p.get(b,1).fill_(2);self.assertTrue(torch.all(p.get(a,0)==1));self.assertEqual(p.total_bytes,256)
 def test_noncontiguous_storage_span_preserved(self):
  a=Info('w',(3,4),(8,1));b=Info('w',(4,2),(2,1));p=Pool([a,b]);self.assertEqual(p.total_bytes,80);self.assertEqual(p.get(a).stride(),a.stride);v=torch.arange(12).reshape(3,4).float();p.get(a).copy_(v);torch.testing.assert_close(p.get(a),v)
 def test_dtypes_stay_separate(self):
  a=Info('w',(2,4),(4,1));b=Info('w',(2,4),(4,1),torch.float16);p=Pool([a,b]);self.assertEqual(p.total_bytes,48);self.assertNotEqual(p.get(a).data_ptr(),p.get(b).data_ptr())
 def test_empty_and_scalar(self):
  a=Info('empty',(0,3),(3,1));b=Info('scalar',(),());p=Pool([a,b]);self.assertEqual(p.total_bytes,4);self.assertEqual(p.get(a).numel(),0);p.get(b).fill_(7);self.assertEqual(p.get(b).item(),7)
 def test_invalid_geometry_or_slots_rejected(self):
  for info in [Info('w',(2,),(-1,)),Info('w',(2,3),(1,))]:
   with self.assertRaises(ValueError):Pool([info])
  with self.assertRaises(ValueError):Pool([],0)
if __name__=='__main__':unittest.main()
