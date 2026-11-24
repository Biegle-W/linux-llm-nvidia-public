"""Launch Kolibri with its pinned PR build and trial-qualified registry settings."""
import json
from pathlib import Path

from llamacpp_worker import main as serve

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'kolibri-llamacpp'
MANIFEST = 'config/kolibri-llamacpp-runtime.json'
RUNTIME = Path('runtimes/llamacpp-manual/kolibri-pr32891-5f4d222-20261124/source/build/bin')
MODEL = 'Kolibri-1.1-Q5_K_M.gguf'
LIBRARIES = ('libllama-server-impl.so', 'libllama-common.so.1.0.0', 'libmtmd.so.1.0.0',
             'libllama.so.1.0.0', 'libggml.so.1.0.0', 'libggml-base.so.1.0.0',
             'libggml-cpu.so.1.0.0', 'libggml-cuda.so.1.0.0')


def build_command(profile, pins, *, port=10000, alias='kolibri'):
    settings = profile['selected_settings']
    if (profile['runtime_manifest'] != MANIFEST or profile['engine'] != 'llama.cpp'
            or profile['weight_quant'] != 'Q5_K_M' or settings['gpu'] != [0, 1]
            or settings['context'] != profile['allocated_context']):
        raise ValueError('Kolibri registry and runtime settings disagree')
    if (pins['binary'] != str(RUNTIME / 'llama-server')
            or set(pins['runtime_files_sha256']) != {str(RUNTIME / name) for name in LIBRARIES}):
        raise ValueError('Incomplete or unexpected Kolibri runtime')
    return [
        str(ROOT / pins['binary']), '-m', str(ROOT / pins['checkpoint_directory'] / MODEL),
        '-ngl', str(settings['gpu_layers']), '-sm', settings['split_mode'],
        '--tensor-split', ','.join(map(str, settings['tensor_split'])), '-ot', settings['override_tensor'],
        '-c', str(settings['context']), '-np', str(settings['parallel']),
        '-b', str(settings['batch']), '-ub', str(settings['ubatch']), '-fa', settings['flash_attention'],
        '-ctk', settings['cache_type_k'], '-ctv', settings['cache_type_v'],
        '--jinja' if settings['jinja'] else '--no-jinja', '--reasoning-format', settings['reasoning_format'],
        '--temp', str(settings['temperature']), '--top-p', str(settings['top_p']),
        '--top-k', str(settings['top_k']), '--min-p', str(settings['min_p']),
        '--chat-template-kwargs', json.dumps(settings['chat_template_kwargs'], separators=(',', ':')),
        '--no-webui', '--host', '127.0.0.1', '--port', str(port), '--alias', alias,
        '--api-key-file', str(ROOT / 'data/local-api-key'), '--metrics', '--verbosity', '4',
    ]


def main(profile):
    return serve(work=ROOT / 'data/router/kolibri', profile=profile, manifest=ROOT / MANIFEST,
                 command_builder=build_command, receipt_files=(MODEL,),
                 library_dirs=(ROOT / RUNTIME, Path('/usr/lib/x86_64-linux-gnu')))
