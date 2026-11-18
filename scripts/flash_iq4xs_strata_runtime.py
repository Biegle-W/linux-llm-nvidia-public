"""Verify the separate Strata preset of Flash-Next UD-IQ4_XS-v31 before guarded serving.

The registry entry holds the selected launch settings; config/flash-iq4xs-strata-runtime.json pins the
weights and the pack. The engine binary is not pinned here: it must be the one the installed
flash-next-strata preset uses, so both quants always run the same engine."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'flash-next-iq4xs-strata'
MANIFEST = 'config/flash-iq4xs-strata-runtime.json'
PRESET = '.local/state/strata/launch/qwen-flash-next-iq4xs.json'
INSTALLED = '.local/state/strata/launch/qwen-flash-next.json'
SHARD_PREFIX = 'Qwen3.8-Flash-Next-UD-IQ4_XS-'
# Settings the registry decides; none may be set a second way.
PINNED = ('--layer-split', '--trim-stage-weights', '--ple-io', '--kv-resident', '--pool-workers', '--kv',
          '--max-context', '--pack', '--native', '--vram-reserve-mib')


def one(args, flag):
    """The value of a flag that must appear exactly once in its plain two-item form."""
    at = [i for i, a in enumerate(args) if a == flag]
    if len(at) != 1 or at[0] + 1 >= len(args):
        raise ValueError('UD-IQ4_XS preset differs from the selected setting: ' + flag)
    return str(args[at[0] + 1])


def prepare_config(profile, root=ROOT, home=None):
    root = Path(root)
    home = Path.home() if home is None else Path(home)
    selected = profile.get('selected_settings', {})
    if (profile['id'] != PROFILE or profile['allocated_context'] != 131072
            or profile.get('runtime_manifest') != MANIFEST):
        raise ValueError('Unexpected UD-IQ4_XS profile, context or manifest')
    pins = json.loads((root / MANIFEST).read_text())
    files = pins['files']
    if len(files) != 4 or any(not row['file'].startswith(SHARD_PREFIX) for row in files):
        raise ValueError('Expected four pinned UD-IQ4_XS shards')
    directory = root / profile['storage']['checkpoint_directory']
    if pins['checkpoint_directory'] != profile['storage']['checkpoint_directory']:
        raise ValueError('UD-IQ4_XS manifest and registry name different weight folders')
    for row in files:
        if row['publisher_sha256_matched'] is not True or (directory / row['file']).stat().st_size != row['bytes']:
            raise ValueError('UD-IQ4_XS checkpoint receipt/size mismatch: ' + row['file'])
    for name, digest in pins['pack_files_sha256'].items():
        if not name.startswith(pins['pack_directory'] + '/'):
            raise ValueError('UD-IQ4_XS pack hash outside the pack folder: ' + name)
        with (root / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                raise ValueError('UD-IQ4_XS pack hash mismatch: ' + name)
    source = home / PRESET
    config = json.loads(source.read_text())
    user_args = config.get('user_args') if isinstance(config, dict) else None
    if (not isinstance(config, dict) or not isinstance(config.get('args'), list)
            or any(type(a) is not str for a in config['args'])
            or not (user_args is None or (isinstance(user_args, list) and all(type(a) is str for a in user_args)))
            or not isinstance(config.get('gpu'), list) or any(type(g) is not int for g in config['gpu'])
            or type(config.get('exe')) is not str or not isinstance(config.get('lib_dirs'), list)):
        raise ValueError('UD-IQ4_XS preset is malformed; refusing launch.')
    args = config['args']
    # Strata applies user_args over args and splits joined forms ('--kv-resident=0'), so neither may carry these.
    if any(a.startswith(PINNED) for a in user_args or []) or any(
            a.startswith(PINNED) and a not in PINNED for a in args):
        raise ValueError('UD-IQ4_XS launch settings are overridden outside the selected registry; refusing launch.')
    pack = root / pins['pack_directory']
    for flag, expected in [('--pack', str(pack)), ('--native', str(directory / files[0]['file'])),
                           ('--max-context', str(profile['allocated_context'])),
                           ('--kv', str(selected['kv'])), ('--kv-resident', str(selected['kv_resident'])),
                           ('--pool-workers', str(selected['pool_workers']))]:
        if one(args, flag) != expected:
            raise ValueError('UD-IQ4_XS preset differs from the selected setting: ' + flag)
    if (config.get('gpu') != selected['gpu'] or str(config.get('layer_split')) != str(selected['layer_split'])
            or config.get('gpu_order') != selected.get('gpu_order')
            or any(flag in args for flag in ('--layer-split', '--trim-stage-weights', '--ple-io', '--vram-reserve-mib'))
            or config.get('tokenizer') != str(pack / 'tokenizer')):
        raise ValueError('UD-IQ4_XS layout differs from the selected registry; refusing launch.')
    installed = json.loads((home / INSTALLED).read_text())
    if (config.get('exe') != installed.get('exe') or config.get('lib_dirs') != installed.get('lib_dirs')
            or not Path(config['exe']).is_file()):
        raise ValueError('UD-IQ4_XS preset must use the same engine as the installed Flash-Next preset.')
    return source
