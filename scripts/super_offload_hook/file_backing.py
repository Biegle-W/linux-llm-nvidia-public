"""Bit-preserving bounded clean file backing for CPU offload tensors."""
import os,mmap,hashlib
from pathlib import Path

def mapped_copy(source,path):
 import torch
 if source.device.type!='cpu' or not source.is_contiguous() or source.storage_offset()!=0:raise ValueError('Contiguous complete CPU tensor required')
 path=Path(path);size=source.numel()*source.element_size();path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600)
 try:
  os.ftruncate(fd,size);mapping=mmap.mmap(fd,size,access=mmap.ACCESS_WRITE)
  flat=torch.frombuffer(mapping,dtype=source.dtype,count=source.numel());original=source.view(-1);step=max(1,32*2**20//source.element_size())
  before=hashlib.sha256();after=hashlib.sha256()
  for start in range(0,original.numel(),step):
   a=original[start:start+step];b=flat[start:start+step];b.copy_(a)
   before.update(a.view(torch.uint8).numpy().tobytes());after.update(b.view(torch.uint8).numpy().tobytes())
   offset=start*source.element_size();mapping.flush(offset,b.numel()*source.element_size())
  os.fsync(fd)
  if before.digest()!=after.digest():raise RuntimeError('File-backed CPU tensor differs bitwise')
  return flat.view(source.shape),mapping,before.hexdigest()
 finally:os.close(fd)

def install(module):
 import torch
 directory=os.environ.get('SUPER_FILE_BACKING_DIRECTORY')
 if not directory:return
 cap=int(os.environ.get('SUPER_FILE_BACKING_MIB_PER_RANK','2048'))*2**20
 if not 0<cap<=2048*2**20:raise ValueError('File backing cap must be <=2GiB per rank')
 original_initial=module._CpuParamOffloader._offload_to_cpu_internal
 original_assign=module._CpuParamOffloader.assign_static_buffer
 used=0;counter=0
 def map_parameter(off,stage):
  nonlocal used,counter
  source=off._param.data;size=source.numel()*source.element_size()
  if source.device.type!='cpu' or size<16*2**20 or used+size>cap:return False
  rank=torch.distributed.get_rank();path=Path(directory)/f'rank{rank}-tensor{counter}.bin';counter+=1
  target,mapping,digest=mapped_copy(source,path)
  off._param.data=target;off._cpu_storage=target;off._file_mapping=mapping;off._file_backed_pointer=target.data_ptr();used+=size
  del source,target
  from host_trim import trim_host_pages
  trim_host_pages('file-backed-'+stage,0)
  print('SUPER_FILE_BACKED_EXPERT',{'stage':stage,'rank':rank,'name':off._param_name,'bytes':size,'total_bytes':used,'sha256':digest},flush=True)
  return True
 def initialized(off):
  original_initial(off)
  # Reserve clean backing for CPU input projections before checkpoint loading.
  # This permits more GPU headroom without adding anonymous loading allocations.
  if 'in_proj' in off._param_name:map_parameter(off,'initial-projection')
 def assigned(off,gpu_buffer):
  if hasattr(off,'_file_mapping'):
   source=off._param.data
   if source.device.type!='cpu' or source.data_ptr()!=off._file_backed_pointer or not source.is_contiguous():raise RuntimeError('Processed projection did not preserve mapped CPU storage')
   off._file_mapping.flush()
   digest=hashlib.sha256()
   flat=source.view(-1).view(torch.uint8)
   for start in range(0,flat.numel(),32*2**20):digest.update(flat[start:start+32*2**20].numpy().tobytes())
   print('SUPER_FILE_BACKED_FINAL',{'rank':torch.distributed.get_rank(),'name':off._param_name,'bytes':flat.numel(),'sha256':digest.hexdigest()},flush=True)
   del source,flat
  elif 'experts' in off._param_name:map_parameter(off,'processed-expert')
  return original_assign(off,gpu_buffer)
 module._CpuParamOffloader._offload_to_cpu_internal=initialized
 module._CpuParamOffloader.assign_static_buffer=assigned
