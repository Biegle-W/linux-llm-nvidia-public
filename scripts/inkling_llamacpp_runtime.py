"""Launch Inkling with the pinned Unsloth llama.cpp build and native worker guards."""
from pathlib import Path

from bolt_iq2_worker import main as serve
from profile_catalog import get_profile

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'inkling-llamacpp'
MANIFEST = 'config/inkling-llamacpp-runtime.json'
RUNTIME = Path('runtimes/llama.cpp-unsloth/b12588-mix-c0c3de8')
CUDA_LIB = Path('runtimes/engine-tools/lib/python3.12/site-packages/nvidia/cu13/lib')
MODEL = 'Inkling-2-Mini-UD-Q4_K_M.gguf'
PROJECTOR = 'mmproj-F16.gguf'
LIBRARIES = ('libggml-base.so.1.0.0', 'libggml.so.1.0.0', 'libggml-cuda.so',
             'libggml-cpu-alderlake.so', 'libggml-cpu-haswell.so', 'libllama.so.1.0.0',
             'libllama-common.so.1.0.0', 'libllama-server-impl.so', 'libmtmd.so.1.0.0')


def build_command(pins, *, port=10000, alias='inkling'):
    if pins['planned_context'] != 32768 or pins['tensor_split'] != [13, 12]:
        raise ValueError('Unreviewed Inkling context or tensor split')
    if (pins['binary'] != str(RUNTIME / 'llama-server')
            or set(pins['runtime_files_sha256']) != {str(RUNTIME / name) for name in LIBRARIES}
            or (pins['first_shard'], pins['mmproj']) != (MODEL, PROJECTOR)):
        raise ValueError('Unexpected Inkling runtime or checkpoint files')
    folder = ROOT / pins['checkpoint_directory']
    return [str(ROOT / pins['binary']), '-m', str(folder / MODEL), '--mmproj', str(folder / PROJECTOR),
            '--alias', alias, '--host', '127.0.0.1', '--port', str(port),
            '--api-key-file', str(ROOT / 'data/local-api-key'),
            # Verbosity 4 prints the per-GPU model buffer lines the placement guard reads.
            '--verbosity', '4', '--jinja', '--split-mode', 'layer',
            '-ngl', '99', '--tensor-split', '13,12', '-fa', 'on', '--ctx-size', '32768',
            '--parallel', '1', '--threads', '8', '--metrics', '--no-webui', '--temp', '1.0',
            '--top-p', '1.0', '--top-k', '0', '--min-p', '0']


def main():
    profile = get_profile(PROFILE)
    if (profile['runtime_manifest'] != MANIFEST or profile['allocated_context'] != 32768
            or profile['selected_settings']['tensor_split'] != [13, 12]
            or profile['engine'] != 'llama.cpp (Unsloth build)' or profile['weight_quant'] != 'UD-Q4_K_M'):
        raise ValueError('Maintained Inkling profile/manifest mismatch')
    return serve(work=ROOT / 'data/router/inkling', unit='llm-router-worker.service', port=10000,
                 alias='inkling', manifest=ROOT / MANIFEST, capture_engine_log=True, profile_id=PROFILE,
                 latch=True, command_builder=build_command, receipt_files=(MODEL, PROJECTOR),
                 library_dirs=(ROOT / RUNTIME, ROOT / CUDA_LIB))
