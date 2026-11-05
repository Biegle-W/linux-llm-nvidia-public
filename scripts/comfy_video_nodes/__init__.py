"""GPU-only video entry orchestration and pinned phase loaders."""
import json
import os
from pathlib import Path
import time
import subprocess
import uuid
import torch
import folder_paths
import comfy.sd
import comfy.utils
import comfy.model_management as mm

WORK=Path(os.environ['COMFY_VIDEO_WORK'])
ROOT=Path(__file__).resolve().parents[2]
PINS=json.loads((ROOT/'config/comfy-video-trial.json').read_text())

def file(name,model=0):
    assert not os.environ.get('COMFY_VIDEO_ENTRY') or os.environ.get('COMFY_VIDEO_ENTRY_CHILD')=='1','Use the selected video workflow entry'
    row=next(row for row in PINS['models'][model]['files'] if row['file'].endswith('/'+name) or row['file']==name)
    return str(ROOT/PINS['checkpoint_directory']/row['file'])

def cpu_activations(value):
    if isinstance(value,torch.Tensor):return value.detach().cpu()
    if isinstance(value,dict):return {k:cpu_activations(v) for k,v in value.items()}
    if isinstance(value,list):return [cpu_activations(v) for v in value]
    if isinstance(value,tuple):return tuple(cpu_activations(v) for v in value)
    return value

class PrepareWanPrompt:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'prompt':('STRING',{'multiline':True})}}
    RETURN_TYPES=('STRING',)
    FUNCTION='prepare'
    OUTPUT_NODE=True
    CATEGORY='NVIDIA/video trial'
    def prepare(self,prompt):
        device=torch.device('cuda:0');start=time.monotonic()
        clip=comfy.sd.load_clip([file('umt5_xxl_int8_convrot.safetensors')],clip_type=comfy.sd.CLIPType.WAN,
            model_options={'load_device':device,'offload_device':device,'initial_device':device},disable_dynamic=True)
        positive=clip.encode_from_tokens_scheduled(clip.tokenize(prompt))
        negative=clip.encode_from_tokens_scheduled(clip.tokenize('blurred, static image, distorted anatomy, text, watermark'))
        assert all(p.device.type=='cuda' for p in clip.patcher.model.parameters())
        torch.save(dict(positive=cpu_activations(positive),negative=cpu_activations(negative)),WORK.parent/'wan-conditioning.pt')
        (WORK/'prompt-proof.json').write_text(json.dumps(dict(encoding_s=time.monotonic()-start,parameter_devices=sorted({str(p.device) for p in clip.patcher.model.parameters()}),CPU_weight_offload=False))+'\n')
        return (str(WORK.parent/'wan-conditioning.pt'),)

class PreparedWanConditioning:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{}}
    RETURN_TYPES=('CONDITIONING','CONDITIONING')
    FUNCTION='load'
    CATEGORY='NVIDIA/video trial'
    def load(self):
        value=torch.load(WORK.parent/'wan-conditioning.pt',map_location='cpu',weights_only=True)
        return value['positive'],value['negative']

class VideoDenoiser:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{}}
    RETURN_TYPES=('MODEL',)
    FUNCTION='load'
    CATEGORY='NVIDIA/video trial'
    def load(self):
        device=torch.device('cuda:0')
        model=comfy.sd.load_diffusion_model(file('wan2.2_ti2v_5B_fp16.safetensors'),
            model_options={'load_device':device,'offload_device':device},disable_dynamic=True)
        return (model,)

class WanSequentialCFG:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'model':('MODEL',)}}
    RETURN_TYPES=('MODEL',)
    FUNCTION='patch'
    CATEGORY='NVIDIA/video'
    def patch(self,model):
        from comfy_wan_memory import sequential_cfg
        model=model.clone()
        model.model_options['sampler_calc_cond_batch_function']=sequential_cfg
        return (model,)

class ResidentWanBlock(torch.nn.Module):
    """Keep a native block on GPU1 without GPU0 patcher relocation."""
    def __init__(self,block,last=False):
        super().__init__()
        object.__setattr__(self,'resident',block)
        self.last=last
    def forward(self,*args,**kwargs):
        def move(value):
            if isinstance(value,torch.Tensor):return value.to('cuda:1')
            if isinstance(value,dict):return {k:move(v) for k,v in value.items()}
            if isinstance(value,list):return [move(v) for v in value]
            if isinstance(value,tuple):return tuple(move(v) for v in value)
            return value
        with torch.cuda.device(1):
            result=self.resident(*move(args),**move(kwargs))
        return result.to('cuda:0') if self.last else result

class WanSplitDenoiser(VideoDenoiser):
    def load(self):
        model=comfy.sd.load_diffusion_model(file('wan2.2_ti2v_5B_fp16.safetensors'),
            model_options={'load_device':torch.device('cuda:0'),'offload_device':torch.device('cpu')},disable_dynamic=True)
        blocks=model.model.diffusion_model.blocks;count=len(blocks);remote=14
        assert count>remote,'Expected native Wan transformer blocks'
        resident=[]
        for index in range(count-remote,count):
            block=blocks[index].to('cuda:1')
            assert all(p.device==torch.device('cuda:1') for p in block.parameters())
            resident.append(block);blocks[index]=ResidentWanBlock(block,last=index==count-1)
        model.offload_device=model.load_device=torch.device('cuda:0')
        model._wan_resident_remote_blocks=resident
        (WORK/'wan-split-proof.json').write_text(json.dumps(dict(total_blocks=count,GPU0_blocks=count-remote,GPU1_blocks=remote,CPU_weight_offload=False))+'\n')
        return (model,)

class VideoVAE:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{}}
    RETURN_TYPES=('VAE',)
    FUNCTION='load'
    CATEGORY='NVIDIA/video trial'
    def load(self):
        state,metadata=comfy.utils.load_torch_file(file('wan2.2_vae.safetensors'),return_metadata=True)
        vae=comfy.sd.VAE(sd=state,metadata=metadata,device=torch.device('cuda:1'))
        vae.patcher.offload_device=vae.device
        vae.patcher.model.to(vae.device)
        return (vae,)

def require_bounded_ltx_tokens(tokens):
    assert tokens and all(len(batches)==1 and len(batches[0])<=256 for batches in tokens.values()), 'LTX prompt exceeds the qualified256-token encoder limit; shorten the caption'

class PrepareLTXPrompt(PrepareWanPrompt):
    def prepare(self,prompt):
        from comfy_mesh_gguf import gguf_nodes
        loader=gguf_nodes().DualCLIPLoaderGGUF()
        paths=[file('gemma-3-12b-it-Q4_K_M.gguf',1),file('ltx-2.3_text_projection_bf16.safetensors',1)]
        start=time.monotonic()
        nodes=gguf_nodes()
        clip=comfy.sd.load_text_encoder_state_dicts(clip_type=comfy.sd.CLIPType.LTXV,state_dicts=loader.load_data(paths),
            model_options={'custom_operations':nodes.GGMLOps,'initial_device':torch.device('cpu'),
                           'load_device':torch.device('cuda:0'),'offload_device':torch.device('cuda:0')},disable_dynamic=True)
        clip.patcher=nodes.GGUFModelPatcher.clone(clip.patcher)
        # Text-only trial: omit unused, absent vision weights and bound padding.
        transformer=clip.patcher.model.gemma3_12b.transformer
        transformer.vision_model=None;transformer.multi_modal_projector=None
        clip.tokenizer.gemma3_12b.min_length=256
        assert clip.patcher.load_device==clip.patcher.offload_device==torch.device('cuda:0')
        # The text projection is a separate GPU1 stage. Keep its lifecycle
        # outside the GPU0 Gemma patcher, which otherwise moves everything.
        projection=clip.patcher.model.text_embedding_projection.to(torch.device('cuda:1'))
        class ProjectionOnSecondGPU(torch.nn.Module):
            def forward(self,value):
                return projection(value.to('cuda:1')).to(value.device)
        clip.patcher.model.text_embedding_projection=ProjectionOnSecondGPU()
        assert all(p.device==torch.device('cuda:1') for p in projection.parameters())
        tokens=clip.tokenize(prompt)
        require_bounded_ltx_tokens(tokens)
        positive=clip.encode_from_tokens_scheduled(tokens)
        negative=clip.encode_from_tokens_scheduled(clip.tokenize('blurred, static image, distorted anatomy, text, watermark'))
        assert all(p.device.type=='cuda' for p in clip.patcher.model.parameters())
        torch.save(dict(positive=cpu_activations(positive),negative=cpu_activations(negative)),WORK.parent/'ltx-conditioning.pt')
        (WORK/'prompt-proof.json').write_text(json.dumps(dict(encoding_s=time.monotonic()-start,parameter_devices=sorted({str(p.device) for p in clip.patcher.model.parameters()}|{str(p.device) for p in projection.parameters()}),CPU_weight_offload=False))+'\n')
        return (str(WORK.parent/'ltx-conditioning.pt'),)

class PreparedLTXConditioning(PreparedWanConditioning):
    def load(self):
        value=torch.load(WORK.parent/'ltx-conditioning.pt',map_location='cpu',weights_only=True)
        return value['positive'],value['negative']

class MeshDenoiser(VideoDenoiser):
    def load(self):
        from comfy_mesh_gguf import gguf_nodes
        nodes=gguf_nodes();state,extra=nodes.gguf_sd_loader(file('ltx-2.3-22b-distilled-1.1-Q4_0.gguf',1))
        # Keep ordinary checkpoint loading on CPU until Mesh strips the remote
        # blocks; the retained front half is fully GPU-loaded before sampling.
        model=comfy.sd.load_diffusion_model_state_dict(state,
            model_options={'custom_operations':nodes.GGMLOps(),'load_device':torch.device('cuda:0'),'offload_device':torch.device('cpu')},
            metadata=extra.get('metadata',{}),disable_dynamic=True)
        assert model is not None
        model=nodes.GGUFModelPatcher.clone(model)
        model.offload_device=model.load_device=torch.device('cuda:0');model.patch_on_device=True
        return (model,)

class MeshVAE(VideoVAE):
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'kind':(['video','audio'],)}}
    def load(self,kind):
        name='LTX23_video_vae_bf16.safetensors' if kind=='video' else 'LTX23_audio_vae_bf16.safetensors'
        state,metadata=comfy.utils.load_torch_file(file(name,1),return_metadata=True)
        vae=comfy.sd.VAE(sd=state,metadata=metadata,device=torch.device('cuda:1'))
        vae.patcher.offload_device=vae.device;vae.patcher.model.to(vae.device)
        return (vae,)

class ReleaseMeshServer:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'samples':('LATENT',)}}
    RETURN_TYPES=('LATENT',)
    FUNCTION='release'
    CATEGORY='NVIDIA/video trial'
    def release(self,samples):
        # Sampling has completed. End the owned back-half process before VAE
        # decoding so GPU1 can reuse its VRAM without moving weights to CPU.
        (WORK/'mesh-stop-request').touch()
        deadline=time.monotonic()+30
        while not (WORK/'mesh-server-stopped').exists():
            if time.monotonic()>deadline:raise TimeoutError('Owned Mesh server did not release VRAM')
            time.sleep(0.1)
        return (samples,)

class VideoEntry:
    @classmethod
    def INPUT_TYPES(cls):
        entry=os.environ.get('COMFY_VIDEO_ENTRY','wan22-5b')
        from comfy_video_entries import RESOLUTIONS
        return {'required':{'entry':([entry],),'prompt':('STRING',{'multiline':True,'default':'A red fox standing in snow slowly turns its head toward the camera and blinks. Gentle snowflakes drift through the air. Static camera, natural sunrise light, realistic smooth motion.'}),'seed':('INT',{'default':27001,'min':0,'max':2**64-1,'control_after_generate':True}),'resolution':(list(RESOLUTIONS),{'default':os.environ.get('COMFY_VIDEO_RESOLUTION','512x288')})}}
    RETURN_TYPES=('VIDEO',)
    FUNCTION='generate'
    CATEGORY='NVIDIA/video'
    def generate(self,entry,prompt,seed,resolution="512x288"):
        from comfy_api.latest import InputImpl
        assert os.environ.get('COMFY_VIDEO_ENTRY')==entry and not os.environ.get('COMFY_VIDEO_ENTRY_CHILD'),'Cross-entry generation forbidden'
        assert prompt.strip() and len(prompt)<=4000,'Use a non-empty prompt up to4000 characters'
        from comfy_video_entries import dimensions
        dimensions(resolution)
        job=WORK/'jobs'/uuid.uuid4().hex;job.mkdir(parents=True)
        (job/'request.json').write_text(json.dumps(dict(entry=entry,prompt=prompt,seed=seed,resolution=resolution))+'\n')
        process=subprocess.Popen([str(ROOT/PINS['python']),str(ROOT/'scripts/comfy_video_job.py'),str(job)],start_new_session=True)
        try:
            while process.poll() is None:
                mm.throw_exception_if_processing_interrupted();time.sleep(0.2)
            assert process.returncode==0,'Video job failed; inspect the foreground backend log'
            result=json.loads((job/'result.json').read_text())
            return (InputImpl.VideoFromFile(result['video']),)
        finally:
            from comfy_video_entries import stop_job_group
            stop_job_group(process)

NODE_CLASS_MAPPINGS={'NvidiaVideoEntry':VideoEntry,'NvidiaPrepareWanPrompt':PrepareWanPrompt,'NvidiaPreparedWanConditioning':PreparedWanConditioning,
                     'NvidiaWanSequentialCFG':WanSequentialCFG,'NvidiaWanSplitDenoiser':WanSplitDenoiser,'NvidiaVideoDenoiser':VideoDenoiser,'NvidiaVideoVAE':VideoVAE,
                     'NvidiaPrepareLTXPrompt':PrepareLTXPrompt,'NvidiaPreparedLTXConditioning':PreparedLTXConditioning,
                     'NvidiaMeshDenoiser':MeshDenoiser,'NvidiaMeshVAE':MeshVAE,'NvidiaReleaseMeshServer':ReleaseMeshServer}
