"""Validate the Hy4 preset and its separate signed-release engine before serving."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'hy4-flash-strata'
MANIFEST = 'config/hy4-flash-strata-runtime.json'
PRESET = '.local/state/strata/launch/hy4-flash-sq-96.json'
WEIGHTS = ('Hy4-Flash-SQ-96.strata', 'Hy4-Flash-Engram-Q8.strata', 'Hy4-Flash-Vision.strata')
ENGINE_FILES = {'strata-hy4', 'libcublas.so.13', 'libcublasLt.so.13', 'engine-component.json', 'BUILD.json'}
TOKENIZER_FILES = {'chat_template.jinja', 'merges.txt', 'tokenizer.json', 'token_type.json', 'vocab.json'}


def verify_hashes(folder, hashes, required):
    if set(hashes) != required:
        raise ValueError('Incomplete or unexpected Hy4 runtime hash list')
    for name, digest in hashes.items():
        with (folder / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                raise ValueError('Hy4 runtime hash mismatch: ' + name)


def prepare_config(profile, root=ROOT, home=None):
    root = Path(root).resolve()
    home = Path.home() if home is None else Path(home)
    if (profile['id'] != PROFILE or profile['engine'] != 'Strata' or profile['allocated_context'] != 32768
            or profile['runtime_manifest'] != MANIFEST):
        raise ValueError('Unexpected Hy4 profile, context or manifest')
    pins = json.loads((root / MANIFEST).read_text())
    if (pins['schema'] != 1 or pins['profile'] != PROFILE or pins['launch_preset'] != '~/' + PRESET
            or pins['checkpoint_directory'] != profile['storage']['checkpoint_directory']):
        raise ValueError('Hy4 runtime manifest differs from the registry')
    weights = root / pins['checkpoint_directory']
    files = pins['files']
    if sorted(row['file'] for row in files) != sorted(WEIGHTS):
        raise ValueError('Expected the three Hy4 weight receipts')
    for row in files:
        if (row['publisher_sha256_matched'] is not True or not re.fullmatch('[0-9a-f]{64}', row['sha256'])
                or (weights / row['file']).stat().st_size != row['bytes']):
            raise ValueError('Hy4 publisher receipt or file size mismatch: ' + row['file'])
    engine = root / pins['engine_directory']
    tokenizer = root / pins['tokenizer_directory']
    verify_hashes(engine, pins['engine_files_sha256'], ENGINE_FILES)
    verify_hashes(tokenizer, pins['tokenizer_files_sha256'], TOKENIZER_FILES)

    settings = profile['selected_settings']
    if (settings['context'] != 32768 or settings['session_reuse'] != 1 or settings['gpu'] != [0]
            or settings['drafting'] != 'dfly2' or settings['environment'] != {'HY4_ENGRAM_ODIRECT': '1'}
            or settings['reasoning_effort'] != 'none'):
        raise ValueError('Hy4 registry settings differ from the measured trial')
    native, engram, vision = (str(weights / name) for name in WEIGHTS)
    expected = dict(exe=str(engine / 'strata-hy4'), arch='hy4flash', cwd=str(root),
                    args=['--native', native, '--engram', engram, '--max-context', '32768',
                          '--vision', vision, '--session-reuse', '1'],
                    tokenizer=str(tokenizer), model_name='hy4-flash-sq-96', lib_dirs=[str(engine)],
                    gpu=[0], gpus_asked=True, drafting='dfly2', env=settings['environment'])
    config = json.loads((home / PRESET).read_text())
    # Exact object equality also excludes user_args, vision blocks, and duplicate flag forms.
    if (config != expected or config['gpus_asked'] is not True or type(config['gpu'][0]) is not int):
        raise ValueError('Hy4 launch preset differs from the selected settings')
    return config
