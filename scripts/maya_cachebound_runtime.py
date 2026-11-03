"""Verify pinned Maya engine binaries before a normal launch."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(config, profile, root=ROOT):
    root = Path(root).resolve()
    if 'pinned_runtime' in config and 'cache_bound_runtime' in config:
        raise ValueError('Ambiguous Maya runtime manifest selection.')
    selected = config.get('pinned_runtime', config.get('cache_bound_runtime'))
    binary = Path(config.get('exe', '')).resolve()
    allowed = {'config/maya-cachebound-runtime.json': 'runtimes/maya-ds4-file-cache-bound/maya-ds4',
               'config/maya-unsloth-runtime.json': 'runtimes/maya-unsloth-v1146/maya-ds4',
               'config/maya-glm-runtime.json': 'runtimes/maya-glm-v1150/maya'}
    controlled_paths = {root / value for value in allowed.values()}
    if selected is None:
        if binary in controlled_paths:
            raise ValueError('Cache-bound runtime requires its pinned manifest.')
        return
    if not isinstance(selected, dict) or set(selected) != {'manifest'} or selected['manifest'] not in allowed:
        raise ValueError('Unexpected cache-bound runtime manifest selection.')
    expected_profile = 'glm-maya' if selected['manifest'] == 'config/maya-glm-runtime.json' else 'deepseek-maya'
    if profile['id'] != expected_profile:
        raise ValueError('Pinned Maya runtime profile mismatch.')
    controlled = root / allowed[selected['manifest']]
    manifest = json.loads((root / selected['manifest']).read_text())
    expected = manifest['binary']
    if (manifest.get('schema') != 1 or manifest.get('profile') != profile['id']
            or expected['path'] != allowed[selected['manifest']]
            or binary != controlled or not binary.is_file()
            or hashlib.sha256(binary.read_bytes()).hexdigest() != expected['sha256']):
        raise ValueError('Cache-bound runtime identity/hash mismatch; refusing launch.')
