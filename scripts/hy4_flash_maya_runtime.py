"""Check Maya's Hy4 binary, pack and two served weight receipts before launch."""
import json
from pathlib import Path
import re

from hy4_flash_strata_runtime import TOKENIZER_FILES, verify_hashes

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'hy4-flash-maya'
MANIFEST = 'config/maya-hy4-runtime.json'
MODEL = 'hy4-flash-maya-l'
CONFIG = 'runtimes/project-maya/maya-hy4-flash-maya-l.json'
WEIGHTS = {'Hy4-Flash-Maya-L-IQ4_XS-00001-of-00002.gguf', 'Hy4-Flash-Maya-L-IQ4_XS-00002-of-00002.gguf'}
PACK_FILES = {'engram.bin', 'hy4.txt', 'tensors.txt'} | {'tokenizer/' + name for name in TOKENIZER_FILES}


def prepare_config(profile, root=ROOT):
    root = Path(root).resolve()
    if (profile['id'] != PROFILE or profile['engine'] != 'Maya' or profile['allocated_context'] != 131072
            or profile['runtime_manifest'] != MANIFEST
            or profile['runtime_selector'] != {'kind': 'private-maya-config', 'path': CONFIG}):
        raise ValueError('Unexpected Maya Hy4 profile, context or runtime selector')
    pins = json.loads((root / MANIFEST).read_text())
    if (pins['schema'] != 1 or pins['profile'] != PROFILE
            or pins['checkpoint_directory'] != profile['storage']['checkpoint_directory']):
        raise ValueError('Maya Hy4 manifest differs from the registry')
    weights = root / pins['checkpoint_directory']
    if sorted(row['file'] for row in pins['files']) != sorted(WEIGHTS):
        raise ValueError('Expected the two served Hy4 shards')
    for row in pins['files']:
        if (row['publisher_sha256_matched'] is not True or not re.fullmatch('[0-9a-f]{64}', row['sha256'])
                or (weights / row['file']).stat().st_size != row['bytes']):
            raise ValueError('Invalid Maya Hy4 weight receipt or size')
    binary = root / pins['binary']['path']
    verify_hashes(binary.parent, {binary.name: pins['binary']['sha256']}, {'maya-hy4'})
    pack = root / pins['pack_directory']
    verify_hashes(pack, pins['pack_files_sha256'], PACK_FILES)
    settings = profile['selected_settings']
    if (settings['context'] != 131072 or settings['gpu'] != [0, 1] or settings['layer_split'] != 'auto'
            or settings['drafting'] != 'off' or settings['vision'] is not False or settings['reasoning_effort'] != 'none'):
        raise ValueError('Maya Hy4 registry settings differ from the trial')
    expected = dict(exe=str(binary), cwd=str(root / 'runtimes/project-maya'),
                    args=['--pack', str(pack), '--main-gpu', '0', '--tp', '0', '--max-context', '131072',
                          '--vision', 'off', '--kv', 'auto', '--reserve-gb', '0.75',
                          '--kv-spill-dir', str(root / 'data/hy4-maya-state'), '--drafting', 'off'],
                    tokenizer=str(pack / 'tokenizer'), model_name=MODEL, gpu=[0, 1],
                    reasoning_effort='none', web_ui=False)
    config = json.loads((root / CONFIG).read_text())
    if json.dumps(config, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError('Maya Hy4 private config differs from the selected settings')
    return config
