# Verify packed group-128 INT8 lookup against direct dequantization.
import importlib.util, torch, sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('runtimes/env-sglang/lib/python3.12/site-packages/sglang/srt/layers/quantization/compressed_tensors/compressed_tensors_embedding.py')
s=importlib.util.spec_from_file_location('embedding_adapter',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for device in ['cuda:0','cuda:1']:
 torch.cuda.set_device(device)
 for dtype in [torch.bfloat16,torch.float16]:
  torch.manual_seed(123)
  q=torch.randint(-128,128,(256,5120),device=device,dtype=torch.int32)
  scale=torch.rand(256,40,device=device,dtype=dtype)
  packed=sum(((q[:,i::4]+128)&255) << (8*i) for i in range(4))
  for ids in [torch.tensor([0,17,255,17],device=device),torch.arange(256,device=device)]:
   actual=m._dequant_gather_triton(ids,packed,scale,5120,8)
   expected=(q[ids].float()*scale[ids].repeat_interleave(128,dim=1).float()).to(dtype)
   torch.testing.assert_close(actual,expected,rtol=0,atol=0)
  print(device,str(dtype),'bit-exact row lookup passed',flush=True)
