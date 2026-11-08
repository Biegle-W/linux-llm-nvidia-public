"""Isolated native IQ2 Bolt worker; preserves the AWQ guard policy and pair ownership."""
import json,math,os,signal,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'data/bolt-iq2-20261104'
sys.path.insert(0,str(ROOT/'scripts'))
from inference_swap_guard import WorkerWatch,read_cgroup
from lifecycle_telemetry import LifecycleLog
from gpu_transport_health import require_host_staged
UNIT='llm-bolt-iq2-test.service';PORT=10002
class BoltWatch(WorkerWatch):
 def __init__(self,*args,port=PORT,**kwargs):
  super().__init__(*args,**kwargs);self.port=port
 def get(self,path):
  q=urllib.request.Request('http://127.0.0.1:'+str(self.port)+path,headers={'Authorization':'Bearer '+self.key})
  with self.opener.open(q,timeout=1.5) as r:raw=r.read(2*1024*1024+1)
  if len(raw)>2*1024*1024:raise ValueError('Oversized llama.cpp telemetry')
  return raw.decode()
 def phase(self):
  from inference_swap_guard import TelemetryError
  import math
  try:
   text=self.get('/metrics');values=[]
   for name in ('llamacpp:requests_processing','llamacpp:requests_deferred'):
    found=[float(x.rsplit(' ',1)[1]) for x in text.splitlines() if x.startswith(name+' ') or x.startswith(name+'{')]
    if not found or any(not math.isfinite(x) or x<0 for x in found):raise TelemetryError('Missing or invalid llama.cpp request gauge')
    values+=found
   self.ready=True
   return 'inference' if any(x>0 for x in values) else 'idle'
  except (OSError,ValueError):
   if not self.ready:return 'loading'
   raise TelemetryError('Owned llama.cpp request telemetry unavailable')
def build_command(pins,*,port=PORT,alias='bolt-iq2-candidate'):
 if pins['planned_context']!=163840 or pins['fit_target_MiB'] not in ([512,512],[384,384],[256,256]):raise ValueError('Unreviewed native Bolt context or fit margin')
 cache_ram=pins.get('cache_ram_MiB',0)
 if type(cache_ram) is not int or cache_ram not in (0,8192):raise ValueError('Unreviewed native Bolt RAM prompt-cache budget')
 return [str(ROOT/pins['binary']),'-m',str(ROOT/pins['checkpoint_directory']/pins['first_shard']),'--alias',alias,
  '--host','127.0.0.1','--port',str(port),'--api-key-file',str(ROOT/'data/local-api-key'),
  '--verbosity','4','--load-mode','mmap','--lazy-mode','off','--fit','on','--fit-target',','.join(str(x) for x in pins['fit_target_MiB']),'--fit-ctx',str(pins['planned_context']),'--split-mode','layer','--cache-type-k','q8_0','--cache-type-v','q8_0',
  '--ctx-size',str(pins['planned_context']),'--parallel','1','--batch-size','256','--ubatch-size','128',
  '--threads','8','--metrics','--no-webui','--cache-ram',str(cache_ram),'--jinja','--reasoning','off',
  '--chat-template-kwargs','{"enable_thinking":false}','--temp','0','--top-k','1','--top-p','1',
  '--repeat-penalty','1','--n-predict','128']


def read_private_key(path):
 path=Path(path)
 if path.stat().st_mode & 0o077:raise RuntimeError('API key must be owner-only')
 key=path.read_text().strip()
 if not key:raise RuntimeError('API key must not be empty')
 return key

def native_placement_proof(path,context):
 import re
 log=Path(path).read_text(errors='replace')
 return bool(re.search(r'n_ctx(?:_slot)?\s*=\s*'+str(context)+r'\b',log)) and all(re.search(r'CUDA'+str(i)+r'.*model buffer size',log) for i in [0,1])

def main(*,work=WORK,unit=UNIT,port=PORT,alias='bolt-iq2-candidate',manifest=None,capture_engine_log=False,profile_id='bolt-iq2-candidate',latch=False):
 os.umask(0o077);work.mkdir(parents=True,exist_ok=True);require_host_staged();group=next(x.split('::',1)[1] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'));base=Path('/sys/fs/cgroup')/group.lstrip('/')
 assert group.endswith('/'+unit)
 from profile_catalog import get_profile,worker_budget,budget_limit_string,require_host_capacity
 profile=get_profile('bolt-llamacpp');require_host_capacity(profile);budget=worker_budget(profile)
 for name,value in [('memory.high',budget_limit_string(budget['high'])),('memory.max',budget_limit_string(budget['max'])),('memory.swap.max','max')]:assert (base/name).read_text().strip()==value
 pins=json.loads((Path(manifest) if manifest else work/'pins.json').read_text());binary=ROOT/pins['binary'];key=read_private_key(ROOT/'data/local-api-key')
 import hashlib
 assert hashlib.file_digest(binary.open('rb'),'sha256').hexdigest()==pins['binary_sha256']
 for name,digest in pins['runtime_files_sha256'].items():assert hashlib.file_digest((ROOT/name).open('rb'),'sha256').hexdigest()==digest
 from storage_policy import verify_storage
 verify_storage({'id':'bolt-iq2-candidate','storage':{'checkpoint_directory':pins['checkpoint_directory'],'access':'ram-resident','required_transport':'sata'}})
 folder=ROOT/pins['checkpoint_directory']
 receipts=pins['files'] if manifest else json.loads((work/'download-receipts.json').read_text());assert len(receipts)==1 and receipts==pins['files']
 for row in receipts:assert (folder/row['file']).stat().st_size==row['bytes'] and row['publisher_sha256_matched'] is True
 watch=BoltWatch(base,'bolt-llamacpp',key,evidence=work/'swap-guard.jsonl',latch=latch,port=port)
 life=LifecycleLog(profile_id,path=None if manifest else work/'lifecycle.jsonl',interval=2);life.start()
 command=build_command(pins,port=port,alias=alias)
 print('Pinned command: '+json.dumps(command),flush=True)
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1',CUDA_DEVICE_ORDER='PCI_BUS_ID',NCCL_P2P_DISABLE='1',GGML_CUDA_P2P='0',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1')
 engine_log=(work/'engine.log').open('w') if capture_engine_log else None
 child=subprocess.Popen(command,env=env,start_new_session=True,stdout=engine_log,stderr=subprocess.STDOUT if engine_log else None);stopping=False;reason=None;bad=0;loading_bad=0
 def stop(*args):
  nonlocal stopping
  stopping=True;life.set_phase('stopping')
  if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:
  while child.poll() is None and not stopping:
   reason=watch.step()
   if stopping:break
   life.set_phase(watch.last_phase)
   pressure=read_cgroup(base)['pressure_pct']
   if not math.isfinite(pressure):raise ValueError('Invalid pressure telemetry')
   loading_bad=loading_bad+1 if watch.last_phase=='loading' and pressure>15 else 0
   available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
   raw=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,memory.free','--format=csv,noheader,nounits'],text=True,timeout=10);cards=[[float(v) for v in x.split(',')] for x in raw.splitlines()]
   bad=bad+1 if available<2*1024**2 or any(c[0]>=100 for c in cards) or (manifest is not None or watch.ready) and any(c[1]<256 for c in cards) else 0
   if len(cards)!=2 or any(not math.isfinite(v) for c in cards for v in c):raise ValueError('Invalid pair resource telemetry')
   if watch.ready and not native_placement_proof(work/'engine.log',pins['planned_context']):reason='Native two-GPU placement/configured context proof missing'
   if bad>=3 or loading_bad>=3:reason=reason or ('Bolt sustained loading pressure' if loading_bad>=3 else 'Bolt host/temperature/GPU-headroom guard reached')
   state={'phase':watch.last_phase,'ready':watch.ready,'child_pid':child.pid,'guard_reason':reason,'host_available_KiB':available,'GPU_temp_free_MiB':cards,'bad_samples':bad,'loading_bad_samples':loading_bad,'loading_PSI_percent':pressure,'time':time.time()};tmp=work/'worker-status.tmp';tmp.write_text(json.dumps(state));tmp.replace(work/'worker-status.json')
   if reason or bad>=3 or loading_bad>=3:
    reason=reason or ('Bolt sustained loading pressure' if loading_bad>=3 else 'Bolt host/temperature/GPU-headroom guard reached');print(reason,flush=True);stop();raise SystemExit(1)
   time.sleep(2)
  raise SystemExit(0 if stopping else child.returncode)
 finally:
  stop()
  try:child.wait(timeout=20)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
  life.stop(child.returncode,reason)
  if engine_log:engine_log.close()
if __name__=='__main__':main(work=Path(sys.argv[1]).resolve())
