#!/usr/bin/env python3
"""Serve one qualified GPU-only Qwen profile in the bounded model service."""
import csv
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'models/engine-tests/qwen38-27b-hyperqwen-fast'
KEY = ROOT / 'data/local-api-key'
CONFIG_HASHES = {
    'config.json': '5a3e7312dee3a6c5909beb854b05ac818be836683730e4facba81f547b77fd62',
    'model.safetensors.index.json': 'f09d9ddfe84617f6a8bd196838b00a4cc0e78159b18dd09883d43d36ce2d436a',
}
SHARD_SIZES = {
    'model-00001-of-00007.safetensors': 3211003472,
    'model-00002-of-00007.safetensors': 3195027104,
    'model-00003-of-00007.safetensors': 3195027104,
    'model-00004-of-00007.safetensors': 3217442568,
    'model-00005-of-00007.safetensors': 699275200,
    'model-00006-of-00007.safetensors': 1291274752,
    'model-00007-of-00007.safetensors': 655565120,
    'model_extra_tensors.safetensors': 327162544,
}


class RedactedKey(str):
    def __repr__(self):
        return repr('[REDACTED]')


def preflight():
    group = next(line.split('::', 1)[1] for line in
                 Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
    limit = (Path('/sys/fs/cgroup') / group.lstrip('/') / 'memory.max').read_text().strip()
    if (not group.endswith('/llm-test-qwen27b.service')
            or limit == 'max' or int(limit) > 36 * 1024 ** 3):
        sys.exit('Use scripts/start_model.sh qwen27b [hyperqwen|sglang].')
    if not KEY.is_file() or KEY.stat().st_mode & 0o077:
        sys.exit('The local API-key file must exist and be readable only by its owner.')
    if not KEY.read_text().strip():
        sys.exit('The local API-key file must not be empty.')
    for name, expected in CONFIG_HASHES.items():
        path = MODEL / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            sys.exit(f'Unqualified checkpoint metadata: {name}. See the engine optimization report.')
    for name, size in SHARD_SIZES.items():
        path = MODEL / name
        if not path.is_file() or path.stat().st_size != size:
            sys.exit(f'Missing or incomplete qualified checkpoint shard: {name}.')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 10000)) == 0:
            sys.exit('Port 10000 is occupied; stop the current model first.')
    inventory = subprocess.check_output([
        'nvidia-smi', '--query-gpu=name,memory.free', '--format=csv,noheader,nounits'], text=True)
    cards = list(csv.reader(inventory.splitlines()))
    requirements = [('NVIDIA GeForce RTX 3080 Ti', 10240),
                    ('NVIDIA GeForce RTX 3080', 9728)]
    if len(cards) < 2:
        sys.exit('Both qualified NVIDIA cards are required.')
    for index, (name, minimum) in enumerate(requirements):
        actual, free = (value.strip() for value in cards[index])
        if actual != name or int(free) < minimum:
            sys.exit(f'GPU {index} needs {name} with at least {minimum} MiB free. '
                     'Preserve other applications; retry when sufficient VRAM is available.')


def main():
    engine = sys.argv[1] if len(sys.argv) == 2 else 'hyperqwen'
    if engine not in ('hyperqwen', 'sglang') or len(sys.argv) > 2:
        sys.exit('Usage: serve_qwen27b_engines.py hyperqwen|sglang')
    preflight()
    cuda = ROOT / 'runtimes/engine-tools/lib/python3.12/site-packages/nvidia/cu13'
    env = dict(os.environ, CUDA_HOME=str(cuda), CUDA_DEVICE_ORDER='PCI_BUS_ID',
               CUDA_VISIBLE_DEVICES='0,1', NCCL_P2P_DISABLE='1', OMP_NUM_THREADS='1',
               PYTORCH_CUDA_ALLOC_CONF='expandable_segments:False',
               SGLANG_ENABLE_TP_MEMORY_INBALANCE_CHECK='1',
               CC='gcc-13', CXX='g++-13')
    env['PATH'] = str(cuda / 'bin') + ':' + env['PATH']
    if engine == 'sglang':
        python = ROOT / 'runtimes/env-sglang/bin/python'
        if Path(sys.prefix).resolve() != python.parent.parent.resolve():
            if not python.is_file():
                sys.exit('Missing qualified SGLang environment.')
            os.execve(python, [str(python), str(Path(__file__).resolve()), engine], env)
    else:
        binary = ROOT / 'runtimes/env-hyperqwen/bin/vllm'
        if not binary.is_file():
            sys.exit('Missing qualified HyperQwen environment.')
    log = ROOT / 'data/qwen27b-server.log'
    fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    if engine == 'sglang':
        os.environ.update(env)
        from sglang.srt.entrypoints.http_server import launch_server
        from sglang.srt.server_args import ServerArgs
        launch_server(ServerArgs(
            model_path=str(MODEL), host='127.0.0.1', port=10000,
            api_key=RedactedKey(KEY.read_text().strip()), served_model_name='qwen3.8-27b',
            tp_size=1, pp_size=2, disable_custom_all_reduce=True,
            mem_fraction_static=0.88, context_length=16384, max_running_requests=1,
            chunked_prefill_size=512, disable_cuda_graph=False, cuda_graph_max_bs_decode=1,
            enable_multimodal=False, json_model_override_args='{"language_model_only":true}',
            max_mamba_cache_size=2, mamba_ssm_dtype='float32', cpu_offload_gb=0,
            attention_backend='triton', disable_radix_cache=True,
            default_chat_template_kwargs={'enable_thinking': False},
        ))
        return
    env.update(VLLM_API_KEY=KEY.read_text().strip(), VLLM_USE_V2_MODEL_RUNNER='1',
               VLLM_USE_FLASHINFER_SAMPLER='0', VLLM_EMBED_UVA='0',
               VLLM_LOCAL_DFLASH_META_SHARE='0', MTP_DRAFT_VOCAB='1',
               VLLM_SPEC_DECODE_ATTN='1', VLLM_SPEC_DECODE_ATTN_QMAX='4',
               VLLM_MARLIN_INPUT_DTYPE='int8', VLLM_MARLIN_INT8_INCLUDE_RE='mlp',
               VLLM_MARLIN_INT8_EXCLUDE_RE='lm_head|mtp')
    args = [str(binary), 'serve', str(MODEL), '--host', '127.0.0.1', '--port', '10000',
            '--served-model-name', 'qwen3.8-27b', '--tensor-parallel-size', '2',
            '--disable-custom-all-reduce', '--gpu-memory-utilization', '0.76',
            '--kv-cache-memory-bytes', '603979776', '--max-model-len', '32768',
            '--max-num-seqs', '1', '--max-num-batched-tokens', '128',
            '--language-model-only', '--mamba-ssm-cache-dtype', 'bfloat16',
            '--reasoning-parser', 'qwen3', '--attention-backend', 'TRITON_ATTN',
            '--kv-cache-dtype', 'int4_per_token_head', '--cpu-offload-gb', '0',
            '--no-enable-prefix-caching', '--default-chat-template-kwargs',
            '{"enable_thinking":false}', '--speculative-config',
            json.dumps({'method': 'mtp', 'num_speculative_tokens': 3,
                        'draft_sample_method': 'probabilistic'}),
            '--compilation-config', json.dumps({'max_cudagraph_capture_size': 4,
                                               'custom_ops': ['+rms_norm', '+silu_and_mul']})]
    os.execve(binary, args, env)


if __name__ == '__main__':
    main()
