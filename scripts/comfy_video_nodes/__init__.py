"""GPU-only prompt preparation and regular loaders for isolated video trials."""
import json
import os
from pathlib import Path
import time
import torch
import folder_paths
import comfy.sd
import comfy.utils
import comfy.model_management as mm

WORK=Path(os.environ['COMFY_VIDEO_WORK'])
ROOT=Path(__file__).resolve().parents[2]
PINS=json.loads((ROOT/'config/comfy-video-trial.json').read_text())

def file(name,model=0):
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
        positive=clip.encode_from_tokens_scheduled(clip.tokenize(prompt))
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

NODE_CLASS_MAPPINGS={'NvidiaPrepareWanPrompt':PrepareWanPrompt,'NvidiaPreparedWanConditioning':PreparedWanConditioning,
                     'NvidiaVideoDenoiser':VideoDenoiser,'NvidiaVideoVAE':VideoVAE,
                     'NvidiaPrepareLTXPrompt':PrepareLTXPrompt,'NvidiaPreparedLTXConditioning':PreparedLTXConditioning,
                     'NvidiaMeshDenoiser':MeshDenoiser,'NvidiaMeshVAE':MeshVAE,'NvidiaReleaseMeshServer':ReleaseMeshServer}
