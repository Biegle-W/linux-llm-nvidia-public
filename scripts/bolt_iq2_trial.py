"""One isolated protected native IQ2 Bolt tool trial; preserves all maintained profiles."""
from pathlib import Path
import importlib.util,json,os,shutil,signal,socket,subprocess,sys,tempfile,time,urllib.request,uuid,threading
ROOT=Path(__file__).resolve().parents[1];WORK=Path(sys.argv[1]).resolve();OUT=WORK/'trial';UNIT='llm-bolt-iq2-test.service';MODEL='bolt-iq2-candidate'
sys.path.insert(0,str(ROOT/'scripts'))
from cli_short_models import inactive,property_of
from gpu_transport_health import require_host_staged
from benchmark_models import metric_delta
import yaml

def prop(name):
 p=subprocess.run(['systemctl','--user','show',UNIT,'-p',name,'--value'],text=True,capture_output=True,timeout=10)
 if p.returncode:raise RuntimeError('Candidate unit state unavailable')
 return p.stdout.strip()
def gpus():
 return [[float(v) for v in x.split(',')] for x in subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free,temperature.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).splitlines()]
def main():
 assert sys.stdin.isatty() and sys.stdout.isatty(),'Use visible_terminal.py foreground'
 os.umask(0o077);OUT.mkdir(exist_ok=False);key=(ROOT/'data/local-api-key').read_text().strip();op=urllib.request.build_opener(urllib.request.ProxyHandler({}));state={'phase':'preflight','model':MODEL,'started':time.time(),'pid':os.getpid()};owned=None;lock=None;tap=None;tail_stop=None;tail_thread=None
 def save():
  tmp=OUT/'state.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(OUT/'state.json')
 def request(url):
  q=urllib.request.Request(url,headers={'Authorization':'Bearer '+key})
  with op.open(q,timeout=3) as response:return json.load(response)
 save()
 try:
  from pair_p2p_health import require_verified_pair
  require_verified_pair();assert 'VERIFIED' in subprocess.check_output(['gpu-unlock-health','status','--brief'],text=True)
  require_host_staged();assert inactive() and not (ROOT/'data/GPU-LOCK').exists(),'Independent worker or reservation preserved'
  health=request('http://127.0.0.1:10100/health');assert not any(health.get(k) for k in ('busy','inflight','queued','loading_model','idle_unloading_model'))
  with socket.socket() as probe:
   probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
   probe.bind(('127.0.0.1',10002))
  baseline=gpus();assert baseline[0][1]>=11520 and baseline[1][1]>=9472,'Insufficient startup headroom on the reserved GPU pair'
  assert subprocess.run(['systemctl','--user','is-active','--quiet',UNIT]).returncode!=0,'Candidate name already active'
  lock={'owner':'isolated-bolt-native-iq2-test','pid':os.getpid(),'unit':UNIT,'nonce':uuid.uuid4().hex,'started':time.time()};fd=os.open(ROOT/'data/GPU-LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as stream:stream.write(json.dumps(lock)+'\n')
  assert inactive(),'Independent worker appeared; preserve it'
  pins=json.loads((WORK/'pins.json').read_text());state.update(phase='loading',pins=pins,baseline_gpu=baseline,reservation_owned=True);save()
  from profile_catalog import get_profile,worker_budget,budget_systemd_size,require_host_capacity
  profile=get_profile('bolt-llamacpp');require_host_capacity(profile);budget=worker_budget(profile);state['guards']={'worker_RAM_GiB':budget,'host_available_GiB':2,'GPU_free_MiB':256,'temperature_C':100,'swap_write_combined_MiB_s':[1,8],'active_PSI_percent':10,'loading_PSI_percent':15,'window_s':30,'bad_samples':3};save()
  from visible_terminal import open_monitor
  if '--foreground-backend' in sys.argv[2:]:
   print('Backend log shares this visible foreground terminal explicitly.',flush=True)
   tail_stop=threading.Event()
   def tail_backend():
    position=0
    while not tail_stop.wait(0.5):
     log=WORK/'engine.log'
     if log.exists():
      with log.open(errors='replace') as stream:
       stream.seek(position);text=stream.read();position=stream.tell()
      if text:print(text,end='',flush=True)
   tail_thread=threading.Thread(target=tail_backend,daemon=True);tail_thread.start()
  else:open_monitor('Native IQ2 Bolt worker',UNIT,[WORK/'engine.log'])
  command=['systemd-run','--user','--collect','--unit='+UNIT,'--property=MemoryHigh='+budget_systemd_size(budget['high']),'--property=MemoryMax='+budget_systemd_size(budget['max']),'--property=MemorySwapMax=infinity','--property=OOMPolicy=kill','--property=KillMode=control-group','--property=TimeoutStopSec=30','--property=NoNewPrivileges=yes','--property=UMask=0077','--property=WorkingDirectory='+str(ROOT),'--property=StandardOutput=append:'+str(WORK/'engine.log'),'--property=StandardError=append:'+str(WORK/'engine.log'),'/usr/bin/python3',str(ROOT/'scripts/bolt_iq2_worker.py'),str(WORK)]
  subprocess.run(command,check=True);owned=prop('InvocationID');assert owned;state['invocation']=owned;save();deadline=time.monotonic()+600;last_print=0
  while True:
   status=prop('ActiveState')
   if status not in ('active','activating'):raise RuntimeError('Candidate worker stopped before readiness; inspect retained private engine/guard logs')
   assert prop('InvocationID')==owned,'Candidate ownership changed'
   try:
    models=request('http://127.0.0.1:10002/v1/models')
    if models.get('data') and any(x.get('id')==MODEL for x in models['data']):
     worker_path=WORK/'worker-status.json'
     if worker_path.exists() and json.loads(worker_path.read_text()).get('ready') is True and json.loads(worker_path.read_text()).get('time',0)>=state['started']:break
   except (OSError,ValueError):pass
   if time.monotonic()>deadline:raise TimeoutError('Candidate startup exceeded bounded600seconds')
   if time.monotonic()-last_print>20:
    print('Native IQ2 Bolt loading; GPU used/free/temp='+json.dumps(gpus()),flush=True);last_print=time.monotonic()
   time.sleep(1)
  state.update(phase='ready',ready_gpu=gpus());save();assert all(x[1]>=256 for x in state['ready_gpu'])
  source=(ROOT/'scripts/short_tool_metrics.py').read_text().replace("'127.0.0.1',10100","'127.0.0.1',10002").replace("127.0.0.1:10000","127.0.0.1:10002")
  path=WORK/'timing_tap.py';path.write_text(source)
  spec=importlib.util.spec_from_file_location('tf_timing',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  tap=module.ToolMetrics(OUT,key,MODEL);entries=yaml.safe_load((ROOT/'data/dsh/profiles/headless/cordis.patch.yml').read_text());provider=next(e['config']['providers']['nvidia-strata'] for e in entries if e['id']=='llm-pi-ai');model=dict(provider['models'][0],id=MODEL,contextWindow=pins['planned_context'],maxTokens=128);provider=dict(provider,baseURL=tap.base_url,models=[model]);overlay=OUT/'selection.yml';overlay.write_text(yaml.safe_dump([{'id':'session-title-llm','disabled':True},{'id':'llm-pi-ai','config':{'providers':{'nvidia-strata':provider}}},{'id':'agent-default-model','config':{'provider':'nvidia-strata','model':MODEL}}],sort_keys=False))
  workspace=Path(tempfile.mkdtemp(prefix='nvidia-bolt-iq2-tool-'));nonce='NVIDIA_TOOL_OK_'+uuid.uuid4().hex;fixture=workspace/'proof.txt';fixture.write_text(nonce+'\n');state.update(phase='short-harness-tool',tool_started=time.time());save()
  task=f'Use the read tool to read {fixture}. Then reply with only the exact file contents. Do not use bash or any other tools. Do not modify any files.';started=time.monotonic()
  with (OUT/'events.jsonl').open('w') as stdout,(OUT/'stderr.txt').open('w') as stderr:
   run=subprocess.Popen([str(ROOT/'dsh/run'),'--profile','headless','--patch',str(overlay),'--json',task],cwd=workspace,stdout=stdout,stderr=stderr)
   try:code=run.wait(timeout=600)
   except BaseException:
    if run.poll() is None:run.terminate();run.wait(timeout=15)
    raise
  events=[]
  for line in (OUT/'events.jsonl').read_text().splitlines():
   try:events.append(json.loads(line))
   except ValueError:pass
  calls=[e for e in events if e.get('type')=='tool_call' and e.get('tool')=='read'];results=[e for e in events if e.get('type')=='tool_result' and e.get('status')=='completed' and e.get('callId') in {c['callId'] for c in calls} and nonce in str(e.get('result',''))];final=next((e.get('text','') for e in reversed(events) if e.get('type')=='final'),'')
  state.update(tool_exit_code=code,tool_wall_s=time.monotonic()-started,tool_calls=len(calls),matching_tool_results=len(results),followup_passed=nonce in final,strict_final_format=final.strip()==nonce)
  assert code==0 and calls and results and final.strip()==nonce,'Actual read tool/result/exact follow-up did not pass'
  assert prop('InvocationID')==owned;state['phase']='pass';save();print('Native IQ2 Bolt actual DSH tool/result/follow-up PASS',flush=True)
 except BaseException as error:
  state.update(phase='failed',error=type(error).__name__+': '+str(error));save();print('Trial stopped: '+state['error'],flush=True)
 finally:
  if tap:tap.close()
  released=False
  if owned:
   current=prop('InvocationID')
   if current==owned and str(ROOT/'scripts/bolt_iq2_worker.py') in prop('ExecStart'):
    begin=time.monotonic();subprocess.run(['systemctl','--user','stop',UNIT],check=True,timeout=45);deadline=time.monotonic()+60
    while time.monotonic()<deadline:
     after=gpus()
     if prop('ActiveState') in ('inactive','failed') and all(a[0]<=b[0]+64 for a,b in zip(after,baseline)):released=True;break
     time.sleep(1)
    state.update(unloaded=released,unload_duration_s=time.monotonic()-begin,after_gpu=after)
   elif not current and prop('ActiveState')=='inactive' and prop('MainPID')=='0':
    after=gpus();released=all(a[0]<=b[0]+64 for a,b in zip(after,baseline))
    state.update(unloaded=released,after_gpu=after,cleanup_collected_unit_verified=True)
   else:state['cleanup_deferred']='Candidate invocation or executable ownership changed; preserved'
  elif lock:
   released=inactive() and prop('ActiveState') in ('inactive','failed') and all(a[0]<=b[0]+64 for a,b in zip(gpus(),baseline))
  if lock and released and json.loads((ROOT/'data/GPU-LOCK').read_text())==lock:(ROOT/'data/GPU-LOCK').unlink();state['reservation_released']=True
  if tail_stop:
   tail_stop.set();tail_thread.join(timeout=2)
  if released:
   from visible_terminal import close_backend_monitor
   close_backend_monitor(UNIT)
  state['finished']=time.time();save()
  print('Owned unload/release:',released,flush=True)
 if state.get('phase')!='pass' or state.get('unloaded') is not True:raise SystemExit(1)
if __name__=='__main__':main()
