"""Isolated Super trial: reclaim unused CUDA allocator blocks after quant postprocessing."""
import os
if os.environ.get('SUPER_POSTLOAD_CACHE_TRIM') == '1':
 import sys, importlib.abc, importlib.machinery, contextlib
 class Loader:
  def __init__(self, base): self.base=base
  def create_module(self,spec): return self.base.create_module(spec) if hasattr(self.base,'create_module') else None
  def exec_module(self,module):
   self.base.exec_module(module)
   if getattr(module,'__name__','') == 'vllm.model_executor.layers.fused_moe.oracle.int_wna16':
    from repack import install
    install(module)
    return
   if getattr(module,'__name__','') == 'vllm.model_executor.offloader.prefetch':
    from placement import install
    install(module)
    initial=module._ModuleOffloader.__init__
    def initialized(instance,*args,**kwargs):
     initial(instance,*args,**kwargs)
     import torch
     torch.cuda.empty_cache()
     print('SUPER_INIT_OFFLOAD_TRIM','device',torch.cuda.current_device(),'allocated',torch.cuda.memory_allocated(instance.device),'reserved',torch.cuda.memory_reserved(instance.device),'cpu_parameter_bytes',sum(x.offloaded_bytes for x in instance._param_offloaders.values()),flush=True)
    module._ModuleOffloader.__init__=initialized
    from file_backing import install as install_file_backing
    install_file_backing(module)
    from compact_pool import initialize
    module.StaticBufferPool.__init__=initialize
    return
   if getattr(module,'__name__','') == 'vllm.model_executor.model_loader.weight_utils':
    from checkpoint_cache import install_iterator
    install_iterator(module)
    return
   original=module.device_loading_context
   @contextlib.contextmanager
   def trimmed(layer,device):
    import torch
    if device.type != 'cuda':
     with original(layer,device) as value: yield value
     return
    from checkpoint_cache import release_once
    release_once()
    torch.cuda.empty_cache()
    before=torch.cuda.memory_allocated(device)
    from reuse import loading_context
    successful=False
    try:
     with loading_context(layer,device) as value: yield value
     successful=True
    finally:
     if successful and os.environ.get('SUPER_PREFETCH_EARLY_SYNC') == '1':
      from vllm.model_executor.offloader import get_offloader
      for off in getattr(get_offloader(), 'module_offloaders', []): off.sync_cpu_storage()
     torch.cuda.empty_cache()
     from host_trim import trim_host_pages
     trim_host_pages(type(layer).__name__)
     print('SUPER_POSTLOAD_TRIM',type(layer).__name__,'device',torch.cuda.current_device(),'allocated_before',before,'allocated_after',torch.cuda.memory_allocated(device),'reserved_after',torch.cuda.memory_reserved(device),flush=True)
   module.device_loading_context=trimmed
 class Finder(importlib.abc.MetaPathFinder):
  def find_spec(self,fullname,path=None,target=None):
   if fullname not in ('vllm.model_executor.model_loader.utils','vllm.model_executor.offloader.prefetch','vllm.model_executor.model_loader.weight_utils','vllm.model_executor.layers.fused_moe.oracle.int_wna16'): return None
   spec=importlib.machinery.PathFinder.find_spec(fullname,path)
   if spec is not None and spec.loader is not None: spec.loader=Loader(spec.loader)
   return spec
 sys.meta_path.insert(0,Finder())
