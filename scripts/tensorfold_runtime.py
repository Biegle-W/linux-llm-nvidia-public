"""Pinned single-device TensorFold launch under the normal dense supervisor."""
import hashlib
import json
import os
from pathlib import Path
import socket
from profile_catalog import worker_budget
from storage_policy import verify_storage
ROOT = Path(__file__).resolve().parents[1]

def command(profile):
    if profile['allocated_context'] != 12288 or profile['drafter_bits'] != 4:
        raise ValueError('TensorFold requires the qualified 12K / 4-bit drafter setting')
    return [str(ROOT / profile['runtime']), 'serve', str(ROOT / profile['storage']['checkpoint_directory']),
            '--backend', 'cuda', '--device', '0', '--host', '127.0.0.1', '--port', '10000',
            '--name', 'qwen27b-tensorfold', '--context', '12288', '--parallel', '1',
            '--max-tokens', '4096', '--temperature', '0', '--no-thinking', '--prompt-cache-gib', '0',
            '--idle-unload', '600', '--api-key-file', str(ROOT / 'data/local-api-key'),
            '--no-update-check', '--drafter', str(ROOT / profile['drafter_directory']), '--drafter-bits', '4']

def require_admission(log):
    required = ('CUDA sm_86 device 0 (NVIDIA GeForce RTX 3080 Ti)',
                '1 stream at once', '12288-token window', '1.0 GiB reserve',
                'drafts: DFlash2', '+ copies; context: 12288;')
    if not all(x in log for x in required):
        raise ValueError('Missing native single-GPU / context / reserve / DFlash2 + copies proof')

def serve(profile):
    if os.environ.get('LOCAL_LLM_GUARDED_WORKER') != '1':
        raise RuntimeError('Use the guarded dense launcher')
    group = next(x.split('::', 1)[1] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    if not group.endswith('/llm-test-qwen27b.service'):
        raise RuntimeError('Wrong worker cgroup')
    budget = worker_budget(profile)
    for name, value in [('memory.high', str(budget['high'] * 1024**3)), ('memory.max', str(budget['max'] * 1024**3)), ('memory.swap.max', 'max')]:
        if (base / name).read_text().strip() != value:
            raise RuntimeError('Incorrect worker memory limit: ' + name)
    from gpu_transport_health import require_host_staged
    require_host_staged()  # Current boot/unlock proof still required; one visible GPU needs no NCCL channels.
    verify_storage(profile)
    drafter = dict(profile, storage=dict(profile['storage'], checkpoint_directory=profile['drafter_directory']))
    verify_storage(drafter)
    manifest = json.loads((ROOT / 'config/tensorfold-runtime.json').read_text())
    for name, expected in manifest['files'].items():
        path = ROOT / name
        if path.stat().st_size != expected['bytes'] or hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() != expected['sha256']:
            raise RuntimeError('Pinned TensorFold file changed: ' + name)
    key = ROOT / 'data/local-api-key'
    if key.stat().st_mode & 0o077 or not key.read_text().strip():
        raise RuntimeError('Missing or nonprivate API key')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 10000)) == 0:
            raise RuntimeError('Backend port occupied')
    from serve_qwen27b_engines import wait_for_gpu_memory
    wait_for_gpu_memory(profile)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', CUDA_DEVICE_ORDER='PCI_BUS_ID', NCCL_P2P_DISABLE='1',
               PYTHONUNBUFFERED='1', HF_HUB_OFFLINE='1', TENSORFOLD_NO_UPDATE_CHECK='1', TENSORFOLD_NO_LIVE='1')
    args = command(profile)
    fd = os.open(ROOT / 'data/qwen27b-server.log', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600); os.dup2(fd, 1); os.dup2(fd, 2); os.close(fd)
    os.execve(args[0], args, env)
