"""Keep CFG execution shape identical across unequal-memory GPU ranks."""
import json
import os
from pathlib import Path
import time

def sequential_cfg(args):
    import comfy.samplers
    results=[]
    value=args['input'];device=getattr(value,'device',None)
    cuda=device is not None and device.type=='cuda'
    if cuda:import torch
    def trace(event):
        if cuda and os.environ.get('COMFY_VIDEO_WORK'):
            row=dict(event=event,time=time.time(),pid=os.getpid(),input_shape=list(value.shape),condition_passes=len(args['conds']),allocated=torch.cuda.memory_allocated(device),reserved=torch.cuda.memory_reserved(device))
            with (Path(os.environ['COMFY_VIDEO_WORK'])/('cfg-memory-'+str(os.getpid())+'.jsonl')).open('a') as stream:stream.write(json.dumps(row)+'\n')
    for condition in args['conds']:
        trace('branch-start')
        results.append(comfy.samplers.calc_cond_batch(args['model'],[condition],value,args['sigma'],args['model_options'])[0])
        # Release only unused allocator segments, never live GPU weight tensors.
        # This prevents a completed branch's scratch cache consuming the next
        # branch's independent free-VRAM margin on these small cards.
        if cuda:torch.cuda.empty_cache()
        trace('branch-end')
    return results
