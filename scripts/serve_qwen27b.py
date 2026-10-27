#!/usr/bin/env python3
"""Serve the validated dense Qwen3.8-27B profile with GPU-resident weights."""
import csv
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'models/qwen3.8-27b-iq4-xs/Qwen3.8-27B-IQ4_XS.gguf'
SERVER = ROOT / 'runtimes/llama.cpp/build/bin/llama-server'
KEY = ROOT / 'data/local-api-key'


def main():
    group = next(line.split('::', 1)[1] for line in
                 Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
    limit = (Path('/sys/fs/cgroup') / group.lstrip('/') / 'memory.max').read_text().strip()
    if (not group.endswith('/llm-test-qwen27b.service')
            or limit == 'max' or int(limit) > 36 * 1024 ** 3):
        sys.exit('Use scripts/start_model.sh qwen27b to enforce the worker memory boundary.')
    if not SERVER.is_file() or not MODEL.is_file() or not KEY.is_file():
        sys.exit('Missing runtime, IQ4_XS checkpoint, or local API-key file; see the dense Qwen setup report.')
    if MODEL.stat().st_size != 15475951328:
        sys.exit('Checkpoint size differs from the verified IQ4_XS artifact; refusing startup.')
    if KEY.stat().st_mode & 0o077:
        sys.exit('The local API-key file must be readable only by its owner.')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 10000)) == 0:
            sys.exit('Port 10000 is occupied; stop the current model first.')
    inventory = subprocess.check_output([
        'nvidia-smi', '--query-gpu=name,memory.free',
        '--format=csv,noheader,nounits'], text=True)
    cards = list(csv.reader(inventory.splitlines()))
    requirements = [('NVIDIA GeForce RTX 3080 Ti', 11520),
                    ('NVIDIA GeForce RTX 3080', 8704)]
    if len(cards) < 2:
        sys.exit('The validated profile requires both NVIDIA cards.')
    for index, (name, minimum) in enumerate(requirements):
        actual, free = (value.strip() for value in cards[index])
        if actual != name or int(free) < minimum:
            sys.exit(f'GPU {index} needs {name} with at least {minimum} MiB free. '
                     'Preserve other applications; retry when sufficient VRAM is available.')
    args = [str(SERVER), '-m', str(MODEL), '--host', '127.0.0.1', '--port', '10000',
            '--api-key-file', str(KEY), '--alias', 'qwen3.8-27b',
            '--n-gpu-layers', '999', '--override-tensor', '^token_embd[.]weight$=CUDA0',
            '--lazy-mode', 'off', '--load-mode', 'none', '--verbosity', '4',
            '--split-mode', 'layer', '--tensor-split', '0.61,0.39', '--fit', 'off',
            '--ctx-size', '32768', '--parallel', '1', '--batch-size', '512',
            '--ubatch-size', '512', '--threads', '6', '--threads-batch', '6',
            '--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0', '--flash-attn', 'on',
            '--jinja', '--reasoning', 'off', '--spec-type', 'draft-mtp',
            '--spec-draft-n-max', '2', '--spec-draft-ngl', '999']
    env = dict(os.environ, CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES='0,1')
    log = ROOT / 'data/qwen27b-server.log'
    fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    os.execve(SERVER, args, env)


if __name__ == '__main__':
    main()
