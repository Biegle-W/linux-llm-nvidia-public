"""Explicit GPU-resident loaders for the maintained, isolated ComfyUI runtime."""
import json
import os
from pathlib import Path
import time
import torch
import folder_paths
import comfy.sd
import comfy.utils
import comfy.model_management as mm
import comfy.samplers


def selected_file(category, name):
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root/'config/comfy-runtime.json').read_text())
    selected = next(model for model in config['models'] if model['id'] == os.environ['COMFY_MODEL_ID'])
    assert category+'/'+name in {row['file'] for row in selected['files']}, 'Use the matching model launcher; stop this instance before switching models'
    return folder_paths.get_full_path_or_raise(category, name)


def timed(stage, function):
    def run(*args, **kwargs):
        torch.cuda.synchronize(0)
        torch.cuda.synchronize(1)
        start = time.monotonic()
        result = function(*args, **kwargs)
        torch.cuda.synchronize(0)
        torch.cuda.synchronize(1)
        with Path(os.environ['COMFY_PLACEMENT_LOG']).with_name('timings.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(stage=stage, seconds=time.monotonic()-start, time=time.time()))+'\n')
        return result
    return run


comfy.samplers.KSAMPLER.sample = timed('sampling', comfy.samplers.KSAMPLER.sample)


def audit(patcher):
    expected = str(patcher.load_device)
    assert expected in ('cuda:0', 'cuda:1')
    assert patcher.offload_device == patcher.load_device, 'CPU offload is forbidden'
    devices = {}
    for tensor in patcher.model.parameters():
        device = str(tensor.device)
        devices[device] = devices.get(device, 0) + tensor.numel()
    assert devices and set(devices) == {expected}, f'Nonresident execution weights: {devices}'
    assert patcher.model.model_lowvram is False, 'Partial weight loading is forbidden'
    row = dict(time=time.time(), model=type(patcher.model).__name__, expected=expected,
               parameter_elements_by_device=devices, offload_device=str(patcher.offload_device))
    with Path(os.environ['COMFY_PLACEMENT_LOG']).open('a') as stream:
        stream.write(json.dumps(row) + '\n')


_load_models_gpu = mm.load_models_gpu
_free_memory = mm.free_memory


def free_memory(memory_required, device, keep_loaded=None, **kwargs):
    # Retain resident components even when a conservative activation estimate
    # asks Comfy to partially unload them. A genuine shortage must fail closed.
    keep = list(keep_loaded or [])
    keep.extend(item for item in mm.current_loaded_models
                if item.model.load_device.type == 'cuda' and item.model.load_device == item.model.offload_device)
    return _free_memory(memory_required, device, keep_loaded=keep, **kwargs)


mm.free_memory = free_memory

def load_models_gpu(models, *args, **kwargs):
    for model in models:
        assert model.load_device.type == 'cuda' and model.offload_device == model.load_device
    kwargs['force_full_load'] = True
    result = _load_models_gpu(models, *args, **kwargs)
    for model in models:
        audit(model)
    for item in mm.current_loaded_models:
        audit(item.model)
    return result

mm.load_models_gpu = load_models_gpu


class ResidentDenoiser:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'name': (folder_paths.get_filename_list('diffusion_models'),)}}
    RETURN_TYPES = ('MODEL',)
    FUNCTION = 'load'
    CATEGORY = 'NVIDIA/GPU resident'

    def load(self, name):
        device = torch.device('cuda:0')
        model = comfy.sd.load_diffusion_model(selected_file('diffusion_models', name),
            model_options={'load_device': device, 'offload_device': device}, disable_dynamic=True)
        return (model,)


class ResidentEncoder:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'name': (folder_paths.get_filename_list('text_encoders'),),
                             'type': (['qwen_image', 'flux3'],)}}
    RETURN_TYPES = ('CLIP',)
    FUNCTION = 'load'
    CATEGORY = 'NVIDIA/GPU resident'

    def load(self, name, type):
        device = torch.device('cuda:1')
        clip = comfy.sd.load_clip([selected_file('text_encoders', name)],
            clip_type=getattr(comfy.sd.CLIPType, type.upper()),
            model_options={'load_device': device, 'offload_device': device, 'initial_device': device},
            disable_dynamic=True)
        clip.encode_from_tokens_scheduled = timed('text_encoding', clip.encode_from_tokens_scheduled)
        return (clip,)


class ResidentVAE:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'name': (folder_paths.get_filename_list('vae'),)}}
    RETURN_TYPES = ('VAE',)
    FUNCTION = 'load'
    CATEGORY = 'NVIDIA/GPU resident'

    def load(self, name):
        sd, metadata = comfy.utils.load_torch_file(selected_file('vae', name), return_metadata=True)
        vae = comfy.sd.VAE(sd=sd, metadata=metadata, device=torch.device('cuda:1'))
        vae.patcher.offload_device = vae.device
        vae.patcher.model.to(vae.device)
        vae.decode = timed('vae_decode', vae.decode)
        return (vae,)


NODE_CLASS_MAPPINGS = {'NvidiaResidentDenoiser': ResidentDenoiser,
                       'NvidiaResidentEncoder': ResidentEncoder, 'NvidiaResidentVAE': ResidentVAE}
