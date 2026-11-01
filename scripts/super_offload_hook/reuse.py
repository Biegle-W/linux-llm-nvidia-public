"""Restore processed CPU-offloaded parameters without a second full CPU copy."""
from contextlib import contextmanager

@contextmanager
def loading_context(layer,device):
 import torch
 originals={n:p.data for n,p in layer.named_parameters(remove_duplicate=False) if p.device.type=='cpu'}
 for _,p in layer.named_parameters():
  if p.device.type=='cpu':p.data=p.data.to(device)
 successful=False
 try:
  yield layer
  successful=True
 finally:
  restored=set()
  for name,p in layer.named_parameters(remove_duplicate=False):
   if name not in originals or id(p) in restored:continue
   original=originals[name];restored.add(id(p))
   if not successful:
    p.data=original
    continue
   if original.dtype==p.data.dtype and original.numel()==p.data.numel() and original.is_contiguous() and p.data.is_contiguous():
    target=original.view(p.data.shape)
   else:
    target=torch.empty_strided(p.data.size(),p.data.stride(),dtype=p.data.dtype,device='cpu',pin_memory=False)
   target.copy_(p.data);p.data=target
