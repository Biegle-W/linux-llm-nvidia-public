"""Bounded ComfyUI service with the existing dense resource guard thresholds."""
from pathlib import Path
import json
import math
import os
import signal
import subprocess
import sys
import time
import urllib.request
from inference_swap_guard import SwapGuard, read_cgroup

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(sys.argv[1]).resolve()
config = json.loads((ROOT / 'config/comfy-runtime.json').read_text())
model_id = json.loads((WORK/'state.json').read_text())['model']
group = Path('/sys/fs/cgroup') / next(x.split(':', 2)[2].lstrip('/') for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0:'))
assert (group/'memory.high').read_text().strip() == str(32*1024**3)
assert (group/'memory.max').read_text().strip() == str(36*1024**3)
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0,1', CUDA_DEVICE_ORDER='PCI_BUS_ID',
           NCCL_P2P_DISABLE='1', PYTHONUNBUFFERED='1', HF_HUB_OFFLINE='1',
           HF_HUB_DISABLE_TELEMETRY='1', DO_NOT_TRACK='1', COMFY_PLACEMENT_LOG=str(WORK/'placement.jsonl'), COMFY_MODEL_ID=model_id)
user_directory = ROOT/'data/comfy-user'/model_id if (WORK/'serve').exists() else WORK/'user'
output_directory = ROOT/'data/comfy-output'/model_id if (WORK/'serve').exists() else WORK/'images'
user_directory.mkdir(parents=True,exist_ok=True)
output_directory.mkdir(parents=True,exist_ok=True)
command = [str(ROOT/config['python']), str(ROOT/config['runtime']/'main.py'), '--listen','127.0.0.1',
           '--port','8188','--disable-auto-launch','--gpu-only','--disable-dynamic-vram',
           '--disable-async-offload','--use-pytorch-cross-attention','--reserve-vram','0.5',
           '--offline','--disable-all-custom-nodes','--whitelist-custom-nodes','nvidia_resident',
           '--extra-model-paths-config',str(WORK/'extra-model-paths.yaml'),
           '--output-directory',str(output_directory),'--user-directory',str(user_directory)]
assert subprocess.check_output(['git','-C',str(ROOT/config['runtime']),'rev-parse','HEAD'],text=True).strip() == config['commit']
assert not subprocess.check_output(['git','-C',str(ROOT/config['runtime']),'status','--porcelain','--untracked-files=no'],text=True).strip(), 'Pinned ComfyUI source changed'
check = """import importlib.metadata as metadata
from pathlib import Path
import sys
for row in Path(sys.argv[1]).read_text().splitlines():
    if row and not row.startswith('#'):
        name, version = row.split('==', 1)
        assert metadata.version(name) == version, 'Dependency pin changed: ' + name
"""
subprocess.run([str(ROOT/config['python']),'-c',check,str(ROOT/'config/comfy-requirements.lock')],check=True)
child = subprocess.Popen(command, env=env, start_new_session=True, cwd=ROOT/config['runtime'])
stopping = False
def stop(*_):
    global stopping
    stopping = True
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
guard = SwapGuard()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
bad = loading_bad = missing = telemetry_bad = 0
ready = False
last_activity = started = time.monotonic()
try:
    while child.poll() is None and not stopping:
        reason = None
        phase = 'loading'
        try:
            with opener.open('http://127.0.0.1:8188/queue',timeout=2) as response:
                queue = json.load(response)
            assert 'queue_running' in queue and 'queue_pending' in queue
            phase = 'inference' if queue['queue_running'] or queue['queue_pending'] else 'idle'
            ready = True
            missing = 0
        except (OSError,ValueError,AssertionError):
            missing += 1
            if ready and missing >= 3:
                reason = 'Comfy request-state telemetry unavailable'
        if phase != 'idle':
            last_activity = time.monotonic()
        try:
            counters = read_cgroup(group)
            assert math.isfinite(counters['pressure_pct']) and counters['pressure_pct'] >= 0
            reason = reason or guard.sample(time.monotonic(),phase,counters['swap_in_pages'],counters['swap_out_pages'],counters['pressure_pct'])
            available = next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
            cards = [[float(v) for v in line.split(',')] for line in subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,memory.free','--format=csv,noheader,nounits'],text=True,timeout=10).splitlines()]
            assert len(cards)==2 and all(math.isfinite(v) for card in cards for v in card)
            bad = bad+1 if available < 2*1024**2 or any(t>=config['guard_policy']['temperature_max_C'] or f<256 for t,f in cards) else 0
            loading_bad = loading_bad+1 if phase=='loading' and counters['pressure_pct']>15 else 0
            if bad>=3 or loading_bad>=3:
                reason = reason or 'Host/VRAM/temperature/loading-pressure guard reached'
            row = dict(time=time.time(),phase=phase,host_available_KiB=available,gpu_temp_free_MiB=cards,
                       bad_samples=bad,loading_bad_samples=loading_bad,violation=reason,rates=guard.last_rates,**counters)
            with (WORK/'resources.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
            telemetry_bad = 0
        except Exception as error:
            telemetry_bad += 1
            if telemetry_bad >= 3:
                reason = reason or 'Resource telemetry unavailable: '+str(error)
        if reason:
            (WORK/'guard-stop.json').write_text(json.dumps(dict(reason=reason,time=time.time()))+'\n')
            raise RuntimeError(reason)
        if not ready and time.monotonic()-started>180:
            raise TimeoutError('Comfy startup exceeded180seconds')
        if ready and phase=='idle' and time.monotonic()-last_activity>600:
            print('Owned ComfyUI idle600s unload',flush=True)
            stop()
        time.sleep(2)
    if not stopping:
        raise RuntimeError('ComfyUI exited unexpectedly: '+str(child.returncode))
finally:
    stop()
    try:child.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
