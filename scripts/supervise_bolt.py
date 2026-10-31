#!/usr/bin/env python3
"""Run the pinned Bolt profile inside the normal router's bounded owned unit."""
import os,signal,subprocess,time
from pathlib import Path
from profile_catalog import get_profile,worker_budget,host_ram_reserve_gib
from storage_policy import verify_storage
from inference_swap_guard import WorkerWatch,read_cgroup,ROOT
from lifecycle_telemetry import LifecycleLog,enabled as telemetry_enabled
from bolt_runtime import build_launch

def resource_fault(available_kib,cards,floor_kib):
 import math
 if any(not math.isfinite(v) or v<0 for card in cards for v in card):raise ValueError('Invalid GPU telemetry')
 if len(cards)!=3 or any(len(c)!=2 for c in cards):raise ValueError('Three-card telemetry required')
 return available_kib<floor_kib or any(c[0]>=82 or c[1]<512 for c in cards)

def main():
 os.umask(0o077);profile=get_profile('bolt-vllm');budget=worker_budget(profile)
 group=next(x.split('::',1)[1] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
 base=Path('/sys/fs/cgroup')/group.lstrip('/')
 if (not group.endswith('/llm-router-worker.service') or (base/'memory.max').read_text().strip()!=str(budget['max']*2**30)
     or (base/'memory.high').read_text().strip()!=str(budget['high']*2**30) or (base/'memory.swap.max').read_text().strip()!='max'):raise SystemExit('Start Bolt through the normal bounded model router')
 verify_storage(profile);key_path=ROOT/'data/local-api-key'
 if key_path.stat().st_mode&0o077:raise SystemExit('API key must be owner-only')
 key=key_path.read_text().strip();command,env=build_launch(profile,key)
 watch=WorkerWatch(base,profile['id'],key);lifecycle=LifecycleLog(profile['id']) if telemetry_enabled() else None
 if lifecycle:lifecycle.start()
 log=ROOT/'data/router/bolt-vllm-engine.log';log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('w') as stream:child=subprocess.Popen(command,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 stopping=False;reason=None
 def stop(*_):
  nonlocal stopping
  stopping=True
  if lifecycle:lifecycle.set_phase('stopping')
  if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 bad=loading_bad=missing=0;floor=host_ram_reserve_gib(profile)*2**20
 try:
  while child.poll() is None and not stopping:
   reason=watch.step()
   if lifecycle:lifecycle.set_phase(watch.last_phase)
   try:
    available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    raw=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,memory.free','--format=csv,noheader,nounits'],text=True,timeout=5)
    cards=[[float(x) for x in line.split(',')] for line in raw.splitlines()];bad=bad+1 if resource_fault(available,cards,floor) else 0
    counters=read_cgroup(base);loading_bad=loading_bad+1 if watch.last_phase=='loading' and counters['pressure_pct']>15 else 0;missing=0
   except (OSError,ValueError,subprocess.SubprocessError):
    missing+=1
   if reason or bad>=3 or loading_bad>=3 or missing>=3:
    reason=reason or ('Bolt resource telemetry unavailable' if missing>=3 else 'Bolt sustained loading pressure' if loading_bad>=3 else 'Bolt host/temperature/VRAM reserve guard')
    print(reason,flush=True);stop();raise SystemExit(1)
   time.sleep(2)
  raise SystemExit(0 if stopping else child.returncode)
 finally:
  stop()
  try:child.wait(timeout=20)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
  if lifecycle:lifecycle.stop(child.returncode,reason)
if __name__=='__main__':main()
