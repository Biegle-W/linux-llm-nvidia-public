"""Fail closed before any neural module executes with CPU-resident parameters."""
import json
import os
from pathlib import Path
import time

if os.environ.get('COMFY_VIDEO_AUDIT_DIR'):
    import torch
    _call = torch.nn.Module._call_impl
    _seen = set()

    def audit(self):
        parameters = list(self.parameters(recurse=False))
        if parameters:
            devices = {str(p.device) for p in parameters if p.numel()}
            row = dict(time=time.time(), pid=os.getpid(), module=type(self).__name__, devices=sorted(devices),CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'))
            if hasattr(torch,'cuda'):
                row['cuda_device_uuids'] = sorted({str(torch.cuda.get_device_properties(device).uuid) for device in devices if device.startswith('cuda:')})
            if any(not device.startswith('cuda:') for device in devices):
                row['violation'] = 'CPU/meta execution parameters forbidden'
            if id(self) not in _seen or row.get('violation'):
                folder=Path(os.environ['COMFY_VIDEO_AUDIT_DIR']);folder.mkdir(parents=True,exist_ok=True)
                with (folder/(str(os.getpid())+'.jsonl')).open('a') as stream:stream.write(json.dumps(row)+'\n')
                _seen.add(id(self))
            if row.get('violation'):
                raise RuntimeError(row['violation']+': '+str(row))

    def gpu_forward(self,*args,**kwargs):
        # FSDP materializes execution parameters in forward pre-hooks. Audit
        # inside forward, after those hooks, rather than its idle shard state.
        if not getattr(self.forward,'_nvidia_gpu_audit',False):
            original=self.forward
            def checked(*forward_args,**forward_kwargs):
                audit(self)
                return original(*forward_args,**forward_kwargs)
            checked._nvidia_gpu_audit=True
            self.forward=checked
        return _call(self,*args,**kwargs)

    torch.nn.Module._call_impl=gpu_forward
