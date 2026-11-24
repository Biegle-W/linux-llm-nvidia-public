"""Validate the two-card SQ-10 preset before Strata control opens it."""
import argparse
import json
import tempfile
from pathlib import Path
import re

from hy4_flash_strata_runtime import TOKENIZER_FILES, verify_hashes

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'inkling-strata'
MANIFEST = 'config/inkling-strata-runtime.json'
MODEL = 'inkling-2-mini-sq-10'
PRESET = '.local/state/strata/launch/' + MODEL + '.json'
WEIGHT = 'Inkling-2-Mini-SQ-10.strata'
ENGINE_FILES = {'strata-inkling', 'libcublas.so.13', 'libcublasLt.so.13', 'libcudart.so.13',
                'libgomp.so.1', 'engine-component.json', 'BUILD.json'}


def expected_config(profile, root):
    root = Path(root).resolve()
    if (profile['id'] != PROFILE or profile['engine'] != 'Strata' or profile['allocated_context'] != 131072
            or profile['runtime_manifest'] != MANIFEST
            or profile['runtime_selector'] != {'kind': 'strata-launch-preset', 'name': MODEL}):
        raise ValueError('Unexpected Inkling profile, context or runtime selector')
    pins = json.loads((root / MANIFEST).read_text())
    if (pins['schema'] != 1 or pins['profile'] != PROFILE or pins['launch_preset'] != '~/' + PRESET
            or pins['checkpoint_directory'] != profile['storage']['checkpoint_directory']):
        raise ValueError('Inkling manifest differs from the registry')
    weight = root / pins['checkpoint_directory'] / WEIGHT
    receipt, = pins['files']
    if (receipt['file'] != WEIGHT or receipt['publisher_sha256_matched'] is not True
            or not re.fullmatch('[0-9a-f]{64}', receipt['sha256']) or weight.stat().st_size != receipt['bytes']):
        raise ValueError('Invalid Inkling weight receipt or size')
    engine = root / pins['engine_directory']
    tokenizer = root / pins['tokenizer_directory']
    verify_hashes(engine, pins['engine_files_sha256'], ENGINE_FILES)
    verify_hashes(tokenizer, pins['tokenizer_files_sha256'], TOKENIZER_FILES)
    settings = profile['selected_settings']
    if (settings['context'] != 131072 or settings['gpu'] != [0, 1]
            or any(type(index) is not int for index in settings['gpu'])
            or settings['layer_split'] != 'auto'
            or settings['drafting'] != 'off' or type(settings['parallel']) is not int
            or settings['parallel'] != 1 or settings['thinking'] != 'hidden'):
        raise ValueError('Inkling registry settings differ from the trial')
    return dict(exe=str(engine / 'strata-inkling'), arch='inkling2_loop', cwd=str(root),
                args=['--native', str(weight), '--max-context', '131072', '--draft', 'off', '--layer-split', 'auto'],
                tokenizer=str(tokenizer), model_name=MODEL, lib_dirs=[str(engine)],
                gpu=[0, 1], gpu_order='as_given', gpus_asked=True, drafting='off', parallel=1)


def prepare_config(profile, root=ROOT, home=None):
    expected = expected_config(profile, root)
    home = Path.home() if home is None else Path(home)
    config = json.loads((home / PRESET).read_text())
    # JSON serialization distinguishes boolean, integer and floating point GPU selectors.
    if json.dumps(config, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError('Inkling launch preset differs from the selected settings')
    return config


def write_preset(profile, root=ROOT, home=None):
    config = expected_config(profile, root)
    target = (Path.home() if home is None else Path(home)) / PRESET
    target.parent.mkdir(parents=True, exist_ok=True)
    stream = tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            json.dump(config, stream, indent=2)
            stream.write('\n')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    from profile_catalog import get_profile
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-preset', action='store_true', required=True)
    parser.parse_args()
    write_preset(get_profile(PROFILE))
