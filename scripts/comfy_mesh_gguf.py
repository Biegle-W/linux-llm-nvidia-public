"""Experimental GPU-only GGUF loader for the pinned Mesh LTX back-half server."""
import importlib.util
import importlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def gguf_nodes():
    name='nvidia_video_gguf'
    if name not in sys.modules:
        folder=ROOT/'runtimes/ComfyUI-GGUF'
        spec=importlib.util.spec_from_file_location(name,folder/'__init__.py',submodule_search_locations=[str(folder)])
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return importlib.import_module(name+'.nodes')

def slim_metadata(metadata,n_blocks):
    metadata=dict(metadata)
    if 'config' in metadata:
        config=json.loads(metadata['config']);config.setdefault('transformer',{})['num_layers']=n_blocks
        metadata['config']=json.dumps(config)
    return metadata

def load_ltx_gguf(weights_path,device,dtype,n_blocks=None):
    import torch
    import comfy.sd
    import comfy.model_management as mm
    nodes=gguf_nodes()
    print('Loading Mesh GGUF back-half checkpoint',flush=True)
    state,extra=nodes.gguf_sd_loader(str(weights_path))
    prefix='model.diffusion_model.'
    canonical={key if key.startswith(prefix) else prefix+key.removeprefix('diffusion_model.'):value for key,value in state.items()}
    block_prefix=prefix+'transformer_blocks.'
    indices={int(key[len(block_prefix):].split('.')[0]) for key in canonical if key.startswith(block_prefix)}
    assert indices==set(range(48)),'Expected LTX2.3 AV48-block architecture'
    assert any('audio_attn1' in key for key in canonical),'AV checkpoint required'
    assert n_blocks is not None and 0<n_blocks<48
    drop_first=48-n_blocks;slim={}
    for key,value in canonical.items():
        if key.startswith(block_prefix):
            index=int(key[len(block_prefix):].split('.')[0])
            if index<drop_first:continue
            tail=key[len(block_prefix):].split('.',1)[1]
            slim[block_prefix+str(index-drop_first)+'.'+tail]=value
        else:slim[key]=value
    state.clear();canonical.clear()
    metadata=slim_metadata(extra.get('metadata',{}),n_blocks)
    print('Constructing '+str(n_blocks)+' Mesh blocks; full-model metadata rewritten to slim count',flush=True)
    patcher=comfy.sd.load_diffusion_model_state_dict(slim,
        model_options={'custom_operations':nodes.GGMLOps(),'dtype':dtype,'load_device':device,'offload_device':device},
        metadata=metadata,disable_dynamic=True)
    assert patcher is not None
    patcher=nodes.GGUFModelPatcher.clone(patcher);patcher.patch_on_device=True
    patcher.load_device=patcher.offload_device=device
    slim.clear();mm.load_models_gpu([patcher],force_full_load=True)
    assert all(p.device.type=='cuda' for p in patcher.model.parameters())
    assert len(patcher.model.diffusion_model.transformer_blocks)==n_blocks
    patcher._mesh_slim_meta=dict(drop_first=drop_first,total_blocks=48,variant='ltxav')
    print('Experimental GGUF Mesh back-half loaded entirely on '+str(device),flush=True)
    if os.environ.get('COMFY_VIDEO_WORK'):
        (Path(os.environ['COMFY_VIDEO_WORK'])/'mesh-server-ready').touch()
    return patcher

def main():
    # ComfyUI and Mesh both use a top-level protocol module. Load Comfy's
    # dependency first, then give Mesh its own module reference.
    gguf_nodes()
    comfy_protocol=sys.modules.pop('protocol',None)
    sys.path.insert(0,str(ROOT/'runtimes/comfyui-mesh/server'))
    import mesh_server_ltx
    if comfy_protocol is not None:sys.modules['protocol']=comfy_protocol
    original=mesh_server_ltx.load_ltx_av
    def load(weights_path,device,dtype,n_blocks=None):
        return load_ltx_gguf(weights_path,device,dtype,n_blocks) if weights_path.suffix=='.gguf' else original(weights_path,device,dtype,n_blocks)
    mesh_server_ltx.load_ltx_av=load
    mesh_server_ltx.main()

if __name__=='__main__':main()
