"""Resolve and verify the pinned, qualified heterogeneous SGLang runtime."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tree_digest(directory):
    digest = hashlib.sha256()
    for path in sorted(Path(directory).rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        digest.update(path.relative_to(directory).as_posix().encode() + b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def local_path(root, relative, interpreter=False):
    value = Path(relative)
    if value.is_absolute() or '..' in value.parts:
        raise ValueError('SGLang runtime paths must be project-relative')
    path = root / value
    checked = path.parent.resolve() if interpreter else path.resolve()
    if not checked.is_relative_to(root.resolve()):
        raise ValueError('SGLang runtime path escapes the project')
    return path


def prepare_environment(env, root=ROOT):
    config = json.loads((root / 'config/sglang-runtime.json').read_text())
    if config['schema'] != 1:
        raise ValueError('Unsupported SGLang runtime manifest')
    package = local_path(root, config['package_directory'])
    python = local_path(root, config['python'], interpreter=True)
    patch = local_path(root, config['patch'])
    if not python.is_file() or not package.is_dir():
        raise RuntimeError('Qualified SGLang runtime is not installed')
    if hashlib.sha256(patch.read_bytes()).hexdigest() != config['patch_sha256']:
        raise RuntimeError('Qualified SGLang patch hash changed')
    if tree_digest(package / 'sglang') != config['package_tree_sha256']:
        raise RuntimeError('Qualified SGLang source hash changed')
    cache = local_path(root, config['cache_directory'])
    cache.mkdir(parents=True, exist_ok=True)
    env = dict(env)
    env.pop('SGLANG_PP_LAYER_PARTITION', None)
    env.update(PYTHONPATH=str(package), LOCAL_SGLANG_MLP_W4A8='1', MAX_JOBS='2',
               SGLANG_CACHE_DIR=str(cache), SGLANG_JIT_CACHE_DIR=str(cache / 'jit'),
               TRITON_CACHE_DIR=str(cache / 'triton'), CUDA_CACHE_PATH=str(cache / 'cuda'),
               TVM_FFI_CACHE_DIR=str(cache / 'tvmffi'), FLASHINFER_CACHE_DIR=str(cache / 'flashinfer'),
               TORCHINDUCTOR_CACHE_DIR=str(cache / 'inductor'), CUDA_PATH=env['CUDA_HOME'])
    invocation = env.get('INVOCATION_ID') or str(os.getpid())
    audit = root / 'data/router/sglang-placement' / invocation
    env['LOCAL_GPU_WEIGHT_AUDIT_DIR'] = str(audit)
    return python, env, config


def verify_loaded_runtime(config, module_file):
    package = local_path(ROOT, config['package_directory'])
    if not Path(module_file).resolve().is_relative_to(package):
        raise RuntimeError('SGLang imported from an unqualified package')
    for name, expected in config['runtime_versions'].items():
        actual = importlib.metadata.version(name)
        if actual != expected:
            raise RuntimeError(f'Qualified SGLang dependency changed: {name} {actual} != {expected}')
