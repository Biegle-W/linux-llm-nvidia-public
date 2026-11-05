"""Bounded ComfyUI service with the existing dense resource guard thresholds."""
from pathlib import Path
import json
import hashlib
import math
import os
import signal
import subprocess
import sys
import time
import tempfile
import shutil
import urllib.request
from inference_swap_guard import SwapGuard, read_cgroup
from profile_catalog import comfy_worker_budget, budget_limit_string, require_host_capacity

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(sys.argv[1]).resolve()
config = json.loads((ROOT / 'config/comfy-runtime.json').read_text())
budget=comfy_worker_budget(config)
require_host_capacity(dict(id='comfy',minimum_usable_ram_gib=config['minimum_usable_ram_gib']))
video_trial = (WORK/'video-stage.json').exists()
if video_trial:
    video_pins=json.loads((ROOT/'config/comfy-video-trial.json').read_text())
    config=dict(config,python=video_pins['python'],runtime=video_pins['ComfyUI']['path'],commit=video_pins['ComfyUI']['commit'])
    for name in ('Raylight','Mesh','GGUF'):
        folder=ROOT/video_pins[name]['path']
        assert subprocess.check_output(['git','-C',str(folder),'rev-parse','HEAD'],text=True).strip()==video_pins[name]['commit']
        changed=subprocess.check_output(['git','-C',str(folder),'diff','--name-only'],text=True).splitlines()
        expected={'Raylight':['src/raylight/comfy_dist/model_patcher.py','src/raylight/distributed_worker/ray_worker.py'],'Mesh':['payload_ltx.py','server/payload_ltx.py'],'GGUF':[]}[name]
        assert changed==expected,'Unreviewed video source edits'
        if expected:
            patch=(ROOT/video_pins[name]['patch']).read_bytes()
            assert hashlib.sha256(patch).hexdigest()==video_pins[name]['patch_sha256'],'Reviewed patch hash changed'
            assert subprocess.check_output(['git','-C',str(folder),'diff','--',*expected])==patch,'Video patch drift'
model_id = json.loads((WORK/'state.json').read_text())['model']
group = Path('/sys/fs/cgroup') / next(x.split(':', 2)[2].lstrip('/') for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0:'))
assert (group/'memory.high').read_text().strip() == budget_limit_string(budget['high'])
assert (group/'memory.max').read_text().strip() == budget_limit_string(budget['max'])
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0,1', CUDA_DEVICE_ORDER='PCI_BUS_ID',
           NCCL_P2P_DISABLE='1', PYTHONUNBUFFERED='1', HF_HUB_OFFLINE='1',
           HF_HUB_DISABLE_TELEMETRY='1', DO_NOT_TRACK='1', COMFY_PLACEMENT_LOG=str(WORK/'placement.jsonl'), COMFY_MODEL_ID=model_id)
ray_temp = Path(tempfile.mkdtemp(prefix='nv-ray-')) if video_trial else None
entry_trial = video_trial and json.loads((WORK/'video-stage.json').read_text())['stage']=='entry'
mesh_trial = video_trial and json.loads((WORK/'video-stage.json').read_text())['stage']=='mesh'
if video_trial:
    env.update(COMFY_VIDEO_WORK=str(WORK),COMFY_VIDEO_AUDIT_DIR=str(WORK/'forward-audits'),
               PYTHONPATH=os.pathsep.join([str(ROOT/'scripts/comfy_video_hook'),str(ROOT/'scripts'),str(ROOT/'runtimes/raylight/src'),str(ROOT/config['runtime'])]),
               RAYLIGHT_RAY_TMPDIR=str(ray_temp),RAY_TMPDIR=str(ray_temp),RAY_USAGE_STATS_ENABLED='0',NCCL_P2P_DISABLE='1',NCCL_DEBUG='INFO',NCCL_LAUNCH_ORDER_IMPLICIT='1')
if video_trial and json.loads((WORK/'video-stage.json').read_text())['stage']=='raylight' and json.loads((WORK/'video-stage.json').read_text()).get('width',512)>=1920:env['NVIDIA_WAN_SEQUENTIAL_CFG']='1'
if entry_trial:
    env['COMFY_VIDEO_ENTRY']=model_id
    settings=json.loads((WORK/'video-stage.json').read_text())
    env['COMFY_VIDEO_RESOLUTION']={(1280,720):'720p',(1920,1080):'1080p'}.get((settings.get('width'),settings.get('height')),'512x288')
user_directory = ROOT/'data/comfy-user'/model_id if (WORK/'serve').exists() else WORK/'user'
output_directory = ROOT/'data/comfy-output'/model_id if (WORK/'serve').exists() else WORK/'images'
user_directory.mkdir(parents=True,exist_ok=True)
output_directory.mkdir(parents=True,exist_ok=True)
# The entry frontend only routes jobs. Avoid spending model VRAM on its CUDA
# contexts; comfy_video_job launches all model phases with --gpu-only.
command = [str(ROOT/config['python']), str(ROOT/config['runtime']/'main.py'), '--listen','127.0.0.1',
           '--port','8188','--disable-auto-launch',('--cpu' if entry_trial else '--gpu-only'),'--disable-dynamic-vram',
           '--disable-async-offload','--use-pytorch-cross-attention','--reserve-vram','0.5',
           '--offline','--disable-all-custom-nodes','--whitelist-custom-nodes',*(['nvidia_video'] if entry_trial else ['nvidia_video','comfyui_mesh'] if mesh_trial else ['nvidia_video','raylight'] if video_trial else ['nvidia_resident']),
           '--extra-model-paths-config',str(WORK/'extra-model-paths.yaml'),
           '--output-directory',str(output_directory),'--user-directory',str(user_directory)]
if video_trial:
    command.append('--disable-cuda-malloc')
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
subprocess.run([str(ROOT/config['python']),'-c',check,str(ROOT/('config/comfy-video-requirements.lock' if video_trial else 'config/comfy-requirements.lock'))],check=True)
mesh_child = None
if mesh_trial:
    mesh_env=dict(env,CUDA_VISIBLE_DEVICES='1',COMFYUI_PATH=str(ROOT/config['runtime']))
    weights=next(row['file'] for row in video_pins['models'][1]['files'] if row['file'].endswith('Q4_0.gguf'))
    mesh_child=subprocess.Popen([str(ROOT/config['python']),str(ROOT/'scripts/comfy_mesh_gguf.py'),'--weights',str(ROOT/video_pins['checkpoint_directory']/weights),'--bind','127.0.0.1','--port','7777','--device','cuda:0','--dtype','bfloat16','--n-blocks','20'],env=mesh_env,start_new_session=True,cwd=ROOT/config['runtime'])
child = subprocess.Popen(command, env=env, start_new_session=True, cwd=ROOT/config['runtime'])
stopping = False
def stop(*_):
    global stopping
    stopping = True
    for owned_child in (child,mesh_child):
        if owned_child is not None and owned_child.poll() is None:
            os.killpg(owned_child.pid, signal.SIGTERM)
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
guard = SwapGuard()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
bad = loading_bad = missing = telemetry_bad = 0
ready = False
last_activity = started = time.monotonic()
try:
    while child.poll() is None and not stopping:
        if mesh_child is not None and (WORK/'mesh-stop-request').exists():
            if mesh_child.poll() is None:os.killpg(mesh_child.pid,signal.SIGTERM)
            try:mesh_child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(mesh_child.pid,signal.SIGKILL);mesh_child.wait(timeout=5)
            mesh_child=None
            (WORK/'mesh-server-stopped').touch()
        reason = 'Mesh server exited unexpectedly' if mesh_child is not None and mesh_child.poll() is not None else None
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
        if mesh_trial and not (WORK/'mesh-server-ready').exists():phase='loading'
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
    for owned_child in (child,mesh_child):
        if owned_child is None:continue
        try:owned_child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(owned_child.pid,signal.SIGKILL);owned_child.wait(timeout=10)
    if ray_temp is not None:shutil.rmtree(ray_temp,ignore_errors=True)
