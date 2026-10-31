"""Fixed prefetch slots sharing capacity across heterogeneous layer shapes.

Reuse is only across layers for the same named parameter and dtype. Existing
prefetch stream/event ordering owns each slot; within-layer names stay separate.
"""
def initialize(pool, param_infos, slot_capacity, device):
 import torch
 device=torch.device(device)
 if type(slot_capacity) is not int or slot_capacity<1:raise ValueError('Positive slot capacity required')
 unique={x.key:x for x in param_infos};groups={};item_sizes={}
 for info in unique.values():
  if len(info.shape)!=len(info.stride) or any(x<0 for x in (*info.shape,*info.stride)):raise ValueError('Unsupported shape/stride')
  span=0 if any(x==0 for x in info.shape) else 1+sum((n-1)*s for n,s in zip(info.shape,info.stride))
  group=(info.name,info.dtype);groups[group]=max(groups.get(group,0),span)
  item_sizes[info.dtype]=torch.empty((),dtype=info.dtype,device='cpu').element_size()
 needed=sum(n*item_sizes[dtype] for (_,dtype),n in groups.items())*slot_capacity
 if device.type=='cuda':
  torch.cuda.empty_cache();free,_=torch.cuda.mem_get_info(device)
  print('BOLT_COMPACT_PREFETCH_POOL','device',device,'shape_classes',len(unique),'storage_groups',len(groups),'required_bytes',needed,'free_bytes',free,flush=True)
  if needed>free-512*2**20:raise RuntimeError('Compact prefetch buffers exceed GPU budget with 512MiB reserve')
 pool.slot_capacity=slot_capacity;pool._device=device;pool.total_bytes=needed;pool._backings={};pool._buffers={}
 for group,n in groups.items():pool._backings[group]=[torch.empty(n,dtype=group[1],device=device) for _ in range(slot_capacity)]
 for key,info in unique.items():pool._buffers[key]=[t.as_strided(info.shape,info.stride) for t in pool._backings[(info.name,info.dtype)]]
