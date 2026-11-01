"""Pinned, independent Strata 0.2.9 runtime for Unsloth Dynamic3.1 DeepSeek."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'deepseek-unsloth-strata'
RUNTIME = 'runtimes/strata-unsloth-029'


def verify(profile, root=ROOT):
    manifest = json.loads((root / 'config/deepseek-unsloth-runtime.json').read_text())
    if (profile['id'] != PROFILE or profile.get('engine') != 'Strata'
            or manifest.get('schema') != 1
            or manifest.get('profile') != PROFILE or manifest.get('runtime_directory') != RUNTIME
            or manifest.get('engine_version') != '0.1.55' or not manifest.get('signature_verified')):
        raise ValueError('Unsloth Strata runtime identity mismatch')
    hashes = manifest.get('sha256', {})
    required = {RUNTIME + '/engine/strata-dsv41', RUNTIME + '/source/serve/server.py',
                RUNTIME + '/pack/ds4.txt', RUNTIME + '/pack/tensors.txt',
                RUNTIME + '/pack/engram.bin', RUNTIME + '/pack/tokenizer/vocab.json',
                RUNTIME + '/profile-2.00.bin'}
    if not required <= set(hashes):
        raise ValueError('Unsloth Strata runtime manifest is incomplete')
    for relative, expected in hashes.items():
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to((root / RUNTIME).resolve()) or not path.is_file():
            raise ValueError('Unsloth Strata runtime file/hash mismatch: ' + relative)
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('Unsloth Strata runtime file/hash mismatch: ' + relative)
    if 'storage' in profile:
        folder = root / profile['storage']['checkpoint_directory']
        files = manifest.get('model_files', {})
        if len(files) != 5 or set(files) != set(profile['storage']['file_transports']):
            raise ValueError('Unsloth model shard manifest mismatch')
        for name, record in files.items():
            if Path(name).name != name or (folder / name).stat().st_size != record['bytes']:
                raise ValueError('Unsloth model shard size/name mismatch')
    return root / RUNTIME


def build_config(profile, runtime):
    selected = profile['selected_settings']
    if (selected.get('gpu') != [0, 1] or selected.get('experts') != 6
            or selected.get('cpu_store_decimal_gb') != 36):
        raise ValueError('Unqualified Unsloth placement/expert/cache setting')
    args = ['--pack', str(runtime / 'pack'), '--max-context', str(profile['allocated_context']),
            '--eos', '1', '--dspark', 'none', '--tp', '2', '--reserve-mib', str(selected.get('internal_gpu_reserve_mib',768)),
            '--experts', '6', '--vision', 'off', '--cpu-threads', '14', '--prefill-chunk', '128',
            '--mmap-experts', 'on', '--expert-profile', str(runtime / 'profile-2.00.bin'),
            '--profile-readonly']
    return {'exe': str(runtime / 'engine/strata-dsv41'), 'args': args,
            'cwd': str(runtime / 'source'), 'tokenizer': str(runtime / 'pack/tokenizer'),
            'model_name': PROFILE, 'arch': 'deepseek41', 'lib_dirs': [str(runtime / 'engine')],
            'engine_ready_s': 900, 'gpu': [0, 1], 'gpus_asked': True, 'host': '127.0.0.1',
            'open_browser': False, 'layer_split': 'auto', 'reasoning_effort': 'none', 'parallel': 1,
            'env': {'DS4_STORE_GB': '36', 'DS4_STORE_POLICY': '1', 'DS4_NO_VIEW': '1',
                    'STRATA_DS4_SLOT_DIR': str(runtime.parents[1] / 'data/strata-unsloth/ds4-slots')}}


def prepare_config(profile, root=ROOT):
    runtime = verify(profile, root)
    inventory = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=index,name', '--format=csv,noheader,nounits'], text=True)
    cards = [tuple(part.strip() for part in line.split(',', 1))
             for line in inventory.splitlines()]
    main_pair = [('0', 'NVIDIA GeForce RTX 3080 Ti'), ('1', 'NVIDIA GeForce RTX 3080')]
    if cards not in [main_pair, main_pair + [('2', 'NVIDIA GeForce RTX 3060')]]:
        raise ValueError('GPU identities/order changed; rediscover the main pair before launch')
    config = build_config(profile, runtime)
    target = root / 'data/router/unsloth-source.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + '\n')
    target.chmod(0o600)
    return target
