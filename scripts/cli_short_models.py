#!/usr/bin/env python3
"""Run one guarded real DSH tool call per selected model from a visible CLI TTY."""
import argparse,fcntl,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from profile_catalog import load_catalog,worker_budget,host_ram_reserve_gib
from inference_swap_guard import WorkerWatch,dense_gpu_free_mib
from pair_p2p_health import require_verified_pair
UNITS=('llm-test-qwen27b.service','llm-router-worker.service')
def property_of(unit,name):
 r=subprocess.run(['systemctl','--user','show',unit,'-p',name,'--value'],capture_output=True,text=True,timeout=10)
 if r.returncode:raise RuntimeError('Cannot access user service bus. Run this foreground command with approved host access; do not disable ownership checks.')
 value=r.stdout.strip()
 if name=='ActiveState' and value not in ('active','activating','inactive','failed','deactivating'):raise RuntimeError('Unknown worker state; preserve existing work.')
 return value
def inactive():return all(property_of(u,'ActiveState') in ('inactive','failed') for u in UNITS)
def guards(profile):
 watch=WorkerWatch('/unused',profile['id'],'not-used',latch=False);g=watch.guard
 return {'worker_RAM_GiB':worker_budget(profile),'host_available_reserve_GiB':host_ram_reserve_gib(profile),'explicit_GPU_free_floor_MiB':dense_gpu_free_mib(profile['id']) if profile['id'].startswith('qwen27b-') else 512 if profile['id'] in ('bolt-vllm','deepseek-unsloth-strata') else None,'native_cache_reserve_MiB':1024 if profile['id'] in ('flash-next-strata','glm-maya','deepseek-maya','deepseek-unsloth-strata') else None,'startup_free_MiB':profile.get('startup_gpu_free_mib'),'loading_PSI_percent':15 if profile['id'] in ('bolt-vllm','deepseek-unsloth-strata') else None,'resource_bad_samples':3,'swap_occupancy':'unlimited','swap_write_MiB_s':g.write_limit,'swap_read_plus_write_MiB_s':g.combined_limit,'swap_window_s':g.window_s,'active_PSI_percent':g.pressure_limit,'PSI_bad_samples':g.bad_samples}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profiles',nargs='+');parser.add_argument('--output',type=Path);args=parser.parse_args()
 if not sys.stdin.isatty() or not sys.stdout.isatty():raise RuntimeError('Run in your foreground terminal using visible_terminal.py foreground. No hidden fallback.')
 os.umask(0o077);profiles=load_catalog()['profiles'];known={p['id'] for p in profiles}
 if args.profiles and (len(args.profiles)!=len(set(args.profiles)) or not set(args.profiles)<=known):raise RuntimeError('Use distinct currently maintained profile IDs.')
 profiles=[p for p in profiles if not args.profiles or p['id'] in args.profiles]
 output=(args.output or ROOT/'data/short-cli-tests'/time.strftime('%Y%m%d-%H%M%S')).resolve();output.mkdir(parents=True,exist_ok=False)
 lock=(ROOT/'data/short-cli-tests.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 key=(ROOT/'data/local-api-key').read_text().strip();opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def request(path):
  q=urllib.request.Request('http://127.0.0.1:10100'+path,headers={'Authorization':'Bearer '+key})
  try:
   with opener.open(q,timeout=10) as response:return json.load(response)
  except OSError as e:raise RuntimeError('Local API unavailable. This process needs approved localhost access; no model was force-stopped.') from e
 def admission_idle():
  h=request('/health');return not any(h.get(k) for k in ('busy','inflight','queued','loading_model','idle_unloading_model'))
 state={'phase':'preflight','pid':os.getpid(),'output':str(output),'results':{},'scope':'one short DSH read tool per profile; loading excluded; no full-context/stress/reload/timed-idle tests; previous worker unload verified before next model selection'}
 def save():
  temporary=output/'state.tmp';temporary.write_text(json.dumps(state,indent=2)+'\n');temporary.replace(output/'state.json')
 save()
 try:
  if not inactive() or (ROOT/'data/GPU-LOCK').exists() or not admission_idle():raise RuntimeError('Existing worker, reservation or admission work preserved. Wait for its owner; do not clear locks.')
  subprocess.run(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],check=True,timeout=10)
  state['P2P']=require_verified_pair();health=subprocess.run(['gpu-unlock-health','status','--brief'],capture_output=True,text=True,check=True,timeout=30).stdout.strip();assert 'VERIFIED' in health;state['unlock']=health
  for p in profiles:
   model=p['id'];state.update(phase='testing',current=model);save()
   if not inactive() or (ROOT/'data/GPU-LOCK').exists() or not admission_idle():raise RuntimeError('New independent work preserved; sequence stopped before model selection.')
   print('\nTesting '+model+'; guards='+json.dumps(guards(p)),flush=True)
   with (output/(model+'.log')).open('x') as log:
    child=subprocess.run(['/usr/bin/python3',str(ROOT/'scripts/smoke_dsh_tools.py'),'--model',model,'--output',str(output/model)],stdout=log,stderr=subprocess.STDOUT)
   folder=output/model;check=json.loads((folder/'state.json').read_text());bench=json.loads((folder/'tool-benchmark.json').read_text()) if (folder/'tool-benchmark.json').exists() else None
   state['results'][model]={'exit_code':child.returncode,'check':check,'benchmark':bench,'guards':guards(p),'configured_context':p['allocated_context'],'worker_inactive_verified':inactive()};save()
   if child.returncode or check.get('phase')!='pass' or check.get('unloaded') is not True or not inactive():raise RuntimeError('Tool/unload check did not pass. Evidence retained; do not auto-retry or force-stop unknown work.')
   print(model+': tool PASS, owned unload PASS; '+json.dumps({k:bench.get(k) for k in ('prefill_tps','ttft_s','decode_tps')} if bench else {'metrics':'unavailable'}),flush=True)
  state.update(phase='complete',finished=time.time());save();print('\nAll selected short checks complete. Results: '+str(output),flush=True)
 except BaseException as e:
  state.update(phase='stopped',error=type(e).__name__+': '+str(e),finished=time.time());save();raise
if __name__=='__main__':main()
