"""Serve the pinned Flash-Next IQ1_S entry with lazy NVMe table and normal ownership guards."""
import json,math,os,re,signal,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'data/router/flash-next-iq1s-llamacpp'
sys.path.insert(0,str(ROOT/'scripts'))
from inference_swap_guard import WorkerWatch
from lifecycle_telemetry import LifecycleLog
from gpu_transport_health import require_host_staged
UNIT='llm-router-worker.service';PORT=10000
def main():
 os.umask(0o077);WORK.mkdir(parents=True,exist_ok=True);require_host_staged();group=next(x.split('::',1)[1] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'));base=Path('/sys/fs/cgroup')/group.lstrip('/')
 assert group.endswith('/'+UNIT)
 for name,value in [('memory.high',str(26*1024**3)),('memory.max',str(28*1024**3)),('memory.swap.max','max')]:assert (base/name).read_text().strip()==value
 from profile_catalog import require_enabled,get_profile,worker_budget
 profile=require_enabled(get_profile('flash-next-iq1s-llamacpp'));assert profile['allocated_context']==12288 and worker_budget(profile)=={'high':26,'max':28,'swap':None}
 assert not (ROOT/'data/local-api-key').stat().st_mode & 0o077
 pins=json.loads((ROOT/'config/flash-iq1s-runtime.json').read_text());binary=ROOT/pins['binary'];key=(ROOT/'data/local-api-key').read_text().strip()
 if not key:raise RuntimeError('API key must not be empty')
 import hashlib
 assert hashlib.file_digest(binary.open('rb'),'sha256').hexdigest()==pins['binary_sha256']
 for name,digest in pins['runtime_files_sha256'].items():assert hashlib.file_digest((ROOT/name).open('rb'),'sha256').hexdigest()==digest
 from storage_policy import verify_storage
 verify_storage({'id':'flash-next-iq1s-llamacpp','storage':{'checkpoint_directory':pins['checkpoint_directory'],'access':'ssd-streaming','required_transport':'nvme'}})
 folder=ROOT/pins['checkpoint_directory']
 receipts=pins['files'];assert len(receipts)==3
 for row in receipts:assert (folder/row['file']).stat().st_size==row['bytes'] and row['publisher_sha256_matched'] is True
 from serve_qwen27b_engines import wait_for_gpu_memory
 wait_for_gpu_memory(profile)
 with socket.socket() as probe:
  if probe.connect_ex(('127.0.0.1',PORT))==0:raise RuntimeError('Backend port occupied; preserve owner')
 watch=WorkerWatch(base,'flash-next-iq1s-llamacpp',key)
 life=LifecycleLog('flash-next-iq1s-llamacpp',interval=2);life.start()
 command=[str(binary),'-m',str(folder/pins['first_shard']),'--alias','flash-next-iq1s-llamacpp',
  '--host','127.0.0.1','--port',str(PORT),'--api-key-file',str(ROOT/'data/local-api-key'),
  '--verbosity','4','--load-mode','mmap','--lazy-mode','on','--fit','on','--fit-target','1536,1536',
  '--ctx-size','12288','--parallel','1','--batch-size','256','--ubatch-size','128',
  '--threads','8','--metrics','--no-webui','--cache-ram','0','--jinja','--reasoning','off',
  '--chat-template-kwargs','{"enable_thinking":false}','--temp','0','--top-k','1','--top-p','1',
  '--repeat-penalty','1','--n-predict','128']
 print('Pinned command: '+json.dumps(command),flush=True)
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1',CUDA_DEVICE_ORDER='PCI_BUS_ID',NCCL_P2P_DISABLE='1',GGML_CUDA_P2P='0',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1')
 engine_log=(WORK/'engine.log').open('w');os.chmod(WORK/'engine.log',0o600)
 child=subprocess.Popen(command,env=env,start_new_session=True,stdout=engine_log,stderr=subprocess.STDOUT);stopping=False;reason=None;bad=0
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
   available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
   raw=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,memory.free','--format=csv,noheader,nounits'],text=True,timeout=10);cards=[[float(v) for v in x.split(',')] for x in raw.splitlines()]
   if len(cards)!=2 or any(not math.isfinite(v) for card in cards for v in card):raise ValueError('Invalid GPU resource telemetry')
   bad=bad+1 if available<2*1024**2 or any(c[0]>=82 for c in cards) or watch.ready and any(c[1]<256 for c in cards) else 0
   if watch.ready:
    log=(WORK/'engine.log').read_text()
    if not any('per_layer_token_embd.weight' in line and 'lazy read enabled' in line for line in log.splitlines()) or not re.search(r'n_ctx(?:_slot)?\s*=\s*12288\b',log):reason='Missing native lazy SSD table/context proof'
    maps=Path('/proc')/str(child.pid)/'maps'
    mapping_lines=[line for line in maps.read_text().splitlines() if pins['ngram_table'] in line]
    if not mapping_lines:reason='Ngram SSD shard mapping missing'
    proof=WORK/'table-mapping-proof.json'
    if mapping_lines and not proof.exists():
     regions=[]
     for line in mapping_lines:
      fields=line.split();a,b=fields[0].split('-');regions.append({'mapped_bytes':int(b,16)-int(a,16),'permissions':fields[1],'file_offset':int(fields[2],16),'shard':pins['ngram_table']})
     proof.write_text(json.dumps({'native_lazy_log':[line for line in log.splitlines() if 'per_layer_token_embd.weight' in line and 'lazy read enabled' in line],'mappings':regions,'physical_transport':'nvme verified before launch'},indent=2)+'\n')
    residency=WORK/'table-residency-during-inference.json'
    if watch.last_phase=='inference' and not residency.exists():
     chunks=re.split(r'(?=^[0-9a-f]+-[0-9a-f]+ )',(Path('/proc')/str(child.pid)/'smaps').read_text(),flags=re.M);samples=[]
     for chunk in chunks:
      lines=chunk.splitlines()
      if lines and pins['ngram_table'] in lines[0]:samples.append({line.split(':')[0]+'_KiB':int(line.split(':')[1].split()[0]) for line in lines[1:] if line.split(':')[0] in ['Size','Rss','Pss','Swap']})
     residency.write_text(json.dumps({'phase':watch.last_phase,'table_mappings':samples,'scope':'one point-in-time mapped residency; no cold-cache claim'},indent=2)+'\n')
   state={'phase':watch.last_phase,'ready':watch.ready,'child_pid':child.pid,'guard_reason':reason,'host_available_KiB':available,'GPU_temp_free_MiB':cards,'bad_samples':bad,'time':time.time()};tmp=WORK/'worker-status.tmp';tmp.write_text(json.dumps(state));tmp.replace(WORK/'worker-status.json')
   if reason or bad>=3:
    reason=reason or 'Flash-Next host/temperature/GPU-headroom guard reached'
    latch=ROOT/'data/router/guard-stops/flash-next-iq1s-llamacpp.json';latch.parent.mkdir(parents=True,exist_ok=True);latch.write_text(json.dumps({'time':time.time(),'profile':profile['id'],'violation':reason})+'\n')
    print(reason,flush=True);stop();raise SystemExit(1)
   time.sleep(2)
  raise SystemExit(0 if stopping else child.returncode)
 finally:
  stop()
  try:child.wait(timeout=20)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
  life.stop(child.returncode,reason)
if __name__=='__main__':main()
