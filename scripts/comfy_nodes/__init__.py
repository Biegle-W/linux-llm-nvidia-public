"""Explicit GPU-resident loaders for the maintained, isolated ComfyUI runtime."""
import importlib
import importlib.util
import json
import os
import sys
import weakref
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

GiB = 1024 ** 3
CPU = torch.device('cpu')
GPU1 = torch.device('cuda:1')
# MiniMax H3 Image only (owner decision 2026-11-15): its 25 GiB text encoder cannot fit a card, so
# its weights stay in system RAM and are streamed through cuda:1 (or run on CPU). Only the exact
# patcher registered by NvidiaH3RAMEncoder gets this exception; every other model keeps the
# all-on-GPU rule above.
ENCODER_BUDGET = int(float(os.environ.get('NVIDIA_H3_ENCODER_GIB', '4')) * GiB)
ENCODER_RESERVE = int(1.85 * GiB)   # VAE decode allowance + 256 MiB kept free on cuda:1
_resident_audit = audit
_encoder_policy = {}  # id(patcher) -> (weak reference, mode)


def encoder_mode(patcher):
    entry = _encoder_policy.get(id(patcher))
    return entry[1] if entry and entry[0]() is patcher else None


def register_encoder(patcher, mode):
    key = id(patcher)
    _encoder_policy[key] = (weakref.ref(patcher, lambda ref, key=key: _encoder_policy.pop(key, None)), mode)


def audit(patcher):
    mode = encoder_mode(patcher)
    if mode is None:
        return _resident_audit(patcher)
    assert patcher.offload_device == CPU
    assert patcher.load_device == (CPU if mode == 'cpu' else GPU1)
    devices = {}
    for tensor in patcher.model.parameters():
        device = str(tensor.device)
        devices[device] = devices.get(device, 0) + tensor.numel()
    assert devices
    if mode == 'cpu':
        assert set(devices) == {'cpu'}, f'CPU encoder weights on a GPU: {devices}'
    else:
        assert set(devices) <= {'cpu', 'cuda:1'} and 'cpu' in devices, f'Unexpected encoder placement: {devices}'
        assert patcher.loaded_size() <= ENCODER_BUDGET + GiB / 4, 'RAM-streamed encoder exceeded its GPU budget'
    row = dict(time=time.time(), model=type(patcher.model).__name__, expected=str(patcher.load_device),
               parameter_elements_by_device=devices, offload_device='cpu', encoder_exception=mode,
               loaded_bytes=patcher.loaded_size())
    with Path(os.environ['COMFY_PLACEMENT_LOG']).open('a') as stream:
        stream.write(json.dumps(row) + '\n')


def release_encoder(patcher):
    if encoder_mode(patcher) == 'stream':
        mm.unload_model_and_clones(patcher, unload_additional_models=False, all_devices=True)
        mm.soft_empty_cache()


def load_models_gpu(models, *args, **kwargs):
    models = list(models)
    exceptional = [p for p in models if encoder_mode(p) is not None]
    if exceptional:
        # Fail closed for clones, LoRA patches and mixed requests.
        assert len(models) == 1 and not args, 'The H3 encoder loads alone'
        patcher = models[0]
        assert not patcher.model_patches_models() and not patcher.patches
        assert not kwargs.get('force_patch_weights', False)
        if encoder_mode(patcher) == 'cpu':
            result = _load_models_gpu([patcher], force_full_load=True)
        else:
            release_encoder(patcher)
            activation = max(float(kwargs.get('memory_required', 0)), float(kwargs.get('minimum_memory_required') or 0),
                             mm.minimum_inference_memory())
            required = ENCODER_BUDGET + activation + ENCODER_RESERVE
            mm.free_memory(required, GPU1)
            assert mm.get_free_memory(GPU1) >= required, 'Insufficient cuda:1 headroom for the H3 encoder'
            loaded = mm.LoadedModel(patcher)
            try:
                loaded.model_load(lowvram_model_memory=ENCODER_BUDGET, force_patch_weights=False)
            except BaseException:
                patcher.detach()
                raise
            mm.current_loaded_models.insert(0, loaded)
            result = None
    else:
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


def gguf_modules():
    # Private package name: keeps ComfyUI-GGUF's relative imports working without whitelisting it
    # as a custom node (its nodes.py would otherwise shadow nothing but still register loaders
    # that ignore the placement rules here).
    package = '_nvidia_city96_gguf'
    if package not in sys.modules:
        directory = Path(__file__).resolve().parents[2] / 'runtimes/ComfyUI-GGUF'
        spec = importlib.util.spec_from_file_location(package, directory / '__init__.py',
                                                      submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(package, None)
            raise
    return tuple(importlib.import_module(package + name) for name in ('.nodes', '.loader', '.ops'))


def gguf_names():
    return sorted({path.name for folder in folder_paths.get_folder_paths('diffusion_models')
                   for path in Path(folder).glob('*.gguf')})


class ResidentDenoiserGGUF:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'name': (gguf_names(),)}}
    RETURN_TYPES = ('MODEL',)
    FUNCTION = 'load'
    CATEGORY = 'NVIDIA/GPU resident'

    def load(self, name):
        gguf_nodes, gguf_loader, gguf_ops = gguf_modules()
        device = torch.device('cuda:0')
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root/'config/comfy-runtime.json').read_text())
        selected = next(model for model in config['models'] if model['id'] == os.environ['COMFY_MODEL_ID'])
        assert 'diffusion_models/'+name in {row['file'] for row in selected['files']}, 'Use the matching model launcher; stop this instance before switching models'
        path = next(Path(folder)/name for folder in folder_paths.get_folder_paths('diffusion_models') if (Path(folder)/name).is_file())
        state, extra = gguf_loader.gguf_sd_loader(str(path))
        ops = gguf_ops.GGMLOps()
        ops.Linear.dequant_dtype = None
        ops.Linear.patch_dtype = None
        model = comfy.sd.load_diffusion_model_state_dict(state, metadata=extra.get('metadata', {}),
            model_options={'custom_operations': ops, 'load_device': device, 'offload_device': device}, disable_dynamic=True)
        assert model is not None, 'Unsupported GGUF denoiser'
        model = gguf_nodes.GGUFModelPatcher.clone(model)
        model.patch_on_device = False
        mm.load_models_gpu([model])  # full load on cuda:0, then audited
        return (model,)


class H3RAMEncoder:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'name': (folder_paths.get_filename_list('text_encoders'),), 'mode': (['stream', 'cpu'],)}}
    RETURN_TYPES = ('CLIP',)
    FUNCTION = 'load'
    CATEGORY = 'NVIDIA/RAM-streamed encoder'

    def load(self, name, mode):
        assert os.environ['COMFY_MODEL_ID'] == 'minimax-h3-image', 'The RAM-streamed encoder is approved for MiniMax H3 Image only'
        clip = comfy.sd.load_clip([selected_file('text_encoders', name)], clip_type=comfy.sd.CLIPType.MINIMAX,
            model_options={'load_device': GPU1, 'offload_device': CPU, 'initial_device': CPU}, disable_dynamic=True)
        assert clip.patcher.load_device == GPU1 and clip.patcher.offload_device == CPU
        if mode == 'cpu':
            clip.patcher.load_device = CPU
        register_encoder(clip.patcher, mode)
        encode = timed('text_encoding', clip.encode_from_tokens_scheduled)

        def encode_and_release(*args, **kwargs):
            try:
                return encode(*args, **kwargs)
            finally:
                release_encoder(clip.patcher)
        clip.encode_from_tokens_scheduled = encode_and_release
        return (clip,)


NODE_CLASS_MAPPINGS = {'NvidiaResidentDenoiserGGUF': ResidentDenoiserGGUF, 'NvidiaH3RAMEncoder': H3RAMEncoder,
                       'NvidiaResidentDenoiser': ResidentDenoiser,
                       'NvidiaResidentEncoder': ResidentEncoder, 'NvidiaResidentVAE': ResidentVAE}
