"""Advise away clean checkpoint cache after weight loading, once per rank."""
from pathlib import Path
import os
_done=False
CHECKPOINT_BYTES=55332700488

def release_once(directory=None):
 global _done
 if _done:return
 root=Path(directory if directory is not None else os.environ['BOLT_CHECKPOINT_DIRECTORY'])
 files=sorted(root.glob('model-*.safetensors'))
 if len(files)!=27 or sum(p.stat().st_size for p in files)!=CHECKPOINT_BYTES:
  raise ValueError('Expected the reviewed complete Bolt checkpoint')
 for p in files:advise_file(p)
 _done=True
 print('BOLT_CHECKPOINT_CLEAN_CACHE_ADVICE','files',len(files),'bytes',CHECKPOINT_BYTES,flush=True)

def advise_file(path):
 result=release_clean_mappings(path)
 if result['mappings']:print('BOLT_CLEAN_SOURCE_RECLAIM',result,flush=True)
 fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC)
 try:os.posix_fadvise(fd,0,0,os.POSIX_FADV_DONTNEED)
 finally:os.close(fd)

def install_iterator(module):
 original=module.safetensors_weights_iterator
 def bounded(files,use_tqdm_on_load,safetensors_load_strategy=None,local_expert_ids=None,**kwargs):
  if safetensors_load_strategy not in (None,'lazy'):
   raise ValueError('Only the qualified lazy safetensors path is supported')
  root=Path(os.environ['BOLT_CHECKPOINT_DIRECTORY']).resolve()
  ordered=sorted(files,key=module._natural_sort_key)
  if (len(ordered)!=27 or sum(Path(p).stat().st_size for p in ordered)!=CHECKPOINT_BYTES
      or any(Path(p).resolve().parent!=root for p in ordered)):
   raise ValueError('Expected only the complete reviewed Bolt checkpoint')
  # Deterministic cold checkpoint state, scoped to these files, not global caches.
  for path in ordered:advise_file(path)
  previous=None
  for index,path in enumerate(ordered):
   first=True
   for name,tensor in original([path],False,safetensors_load_strategy,local_expert_ids,**kwargs):
    yield name,tensor
    # The caller has now replaced its last reference to the previous shard's
    # final source tensor; unmapped clean pages can be reclaimed by the kernel.
    if first and previous is not None:advise_file(previous)
    first=False
   import torch
   if torch.cuda.is_initialized():torch.cuda.current_stream().synchronize()
   advise_file(path)
   previous=path
   print('BOLT_SHARD_CONSUMED',index+1,'of',len(ordered),flush=True)
  if previous is not None:advise_file(previous)
 module.safetensors_weights_iterator=bounded

def release_clean_mappings(path):
 """Reclaim only matching file VMAs proven to have no private/dirty data."""
 import ctypes,re,mmap
 target=str(Path(path).resolve());inode=str(Path(path).stat().st_ino)
 if target not in re.sub(r'\\([0-7]{3})',lambda m:chr(int(m.group(1),8)),Path('/proc/self/maps').read_text()):return {'mappings':0,'mapped_bytes':0}
 candidates=[];current=None
 for line in Path('/proc/self/smaps').read_text().splitlines()+['0-0 ---- 0 00:00 0']:
  if re.match(r'^[0-9a-f]+-[0-9a-f]+ ',line):
   if current is not None:candidates.append(current)
   parts=line.split(maxsplit=5);current=None
   if len(parts)==6 and parts[1] in ('r--p','r--s','rw-p') and parts[4]==inode:
    name=re.sub(r'\\([0-7]{3})',lambda m:chr(int(m.group(1),8)),parts[5])
    if name==target:current={'span':parts[0]}
  elif current is not None and ':' in line:
   key,value=line.split(':',1)
   if key in ['Anonymous','Private_Dirty','Shared_Dirty','Swap','Locked']:current[key]=int(value.split()[0])
   if key=='VmFlags':current[key]=value.split()
 libc=ctypes.CDLL(None,use_errno=True);libc.madvise.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int];libc.madvise.restype=ctypes.c_int
 count=total=0
 for row in candidates:
  if any(row.get(k)!=0 for k in ['Anonymous','Private_Dirty','Shared_Dirty','Swap','Locked']):continue
  if any(k in row.get('VmFlags',[]) for k in ['io','pf','ht']):continue
  begin,end=(int(x,16) for x in row['span'].split('-'))
  if libc.madvise(begin,end-begin,mmap.MADV_DONTNEED)!=0:
   code=ctypes.get_errno();raise OSError(code,os.strerror(code))
  count+=1;total+=end-begin
 return {'mappings':count,'mapped_bytes':total}
