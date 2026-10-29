"""Verify the optional Maya file-cache controller binary before a normal launch."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(config, profile, root=ROOT):
    root = Path(root).resolve()
    selected = config.get('cache_bound_runtime')
    binary = Path(config.get('exe', '')).resolve()
    controlled = root / 'runtimes/maya-ds4-file-cache-bound/maya-ds4'
    if selected is None:
        if binary == controlled:
            raise ValueError('Cache-bound runtime requires its pinned manifest.')
        return
    if profile['id'] != 'deepseek-maya':
        raise ValueError('The cache-bound runtime is qualified only for DeepSeek/Maya.')
    if selected != {'manifest': 'config/maya-cachebound-runtime.json'}:
        raise ValueError('Unexpected cache-bound runtime manifest selection.')
    manifest = json.loads((root / selected['manifest']).read_text())
    expected = manifest['binary']
    if (manifest.get('schema') != 1 or manifest.get('profile') != profile['id']
            or expected['path'] != 'runtimes/maya-ds4-file-cache-bound/maya-ds4'
            or binary != controlled or not binary.is_file()
            or hashlib.sha256(binary.read_bytes()).hexdigest() != expected['sha256']):
        raise ValueError('Cache-bound runtime identity/hash mismatch; refusing launch.')
