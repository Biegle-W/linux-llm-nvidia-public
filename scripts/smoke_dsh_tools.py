"""Short real DSH tool round trip, then owned unload. No context stress."""
from pathlib import Path
import argparse,json,os,time,uuid,tempfile,subprocess,urllib.request,urllib.error,shutil,sys
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--require-followup',action='store_true');p.add_argument('--keep-loaded-on-pass',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--updater-owner-file',type=Path);p.add_argument('--backend-model');p.add_argument('--fixture',type=Path);a=p.parse_args();os.umask(0o077)
R=Path(__file__).resolve().parents[1];H=R/'data/harness-smoke';O=a.output or H/(str(time.time_ns())+'-'+a.model);O.mkdir(parents=True,exist_ok=False);state={'phase':'preflight','model':a.model,'pid':os.getpid(),'started':time.time()};owned=None;timing_tap=None
k=(R/'data/local-api-key').read_text().strip();opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def save():(O/'state.json').write_text(json.dumps(state,indent=2)+'\n')
def req(path,body=None):
 q=urllib.request.Request('http://127.0.0.1:10100'+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+k,'Content-Type':'application/json'})
 with opener.open(q,timeout=1200) as f:return json.load(f)
def prop(n):return subprocess.check_output(['systemctl','--user','show',('llm-test-qwen27b.service' if a.model.startswith('qwen27b-') else 'llm-router-worker.service'),'-p',n,'--value'],text=True).strip()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
save()
try:
 updater_owner=None
 def verify_updater():
  from daily_update_owner import allowed_reservation
  assert a.updater_owner_file.resolve()==(R/'data/GPU-LOCK').resolve(), 'Unexpected updater owner file'
  assert allowed_reservation(a.updater_owner_file,updater_owner,R), 'Updater ownership changed'
  if owned:assert prop('InvocationID')==owned, 'Worker ownership changed'
 if a.updater_owner_file:
  updater_owner=json.loads(a.updater_owner_file.read_text());verify_updater();assert a.backend_model
  state['managed_by_updater']=True
 else:
  assert not a.backend_model
  health=req('/health');assert not (R/'data/GPU-LOCK').exists();assert not any(health.get(x) for x in ['busy','inflight','queued','loading_model','idle_unloading_model']),health
  state['phase']='selecting';save();req('/router/select',{'model':a.model})
 owned=prop('InvocationID');assert owned;state['invocation']=owned;state['ready_gpu_memory']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free','--format=csv,noheader,nounits'],text=True).strip()
 ready_free=[float(line.split(',')[1]) for line in state['ready_gpu_memory'].splitlines()]
 from inference_swap_guard import dense_gpu_free_mib
 gpu_floor=dense_gpu_free_mib(a.model)
 assert len(ready_free)==2 and all(value>=gpu_floor for value in ready_free),f'Readiness is below the selected two-GPU {gpu_floor} MiB free-memory floor'
 # Metadata readiness can precede SGLang's native warmup request completion.
 # Exclude that request before taking the first-tool counter baseline.
 if a.model=='qwen27b-sglang':
  from benchmark_models import wait_sglang_warmup
  wait_sglang_warmup(R/'data/qwen27b-server.log',timeout=60)
 transform_request=None
 if updater_owner:
  sys.path.insert(0,str(R/'network'))
  from router import apply_request_defaults
  from profile_catalog import get_profile
  selected_profile=get_profile(a.model)
  transform_request=lambda body:apply_request_defaults(body,selected_profile)
 from short_tool_metrics import ToolMetrics
 timing_tap=ToolMetrics(O,k,a.model,upstream_port=10000 if updater_owner else 10100,backend_model=a.backend_model,ownership_check=verify_updater if updater_owner else None,request_transform=transform_request)
 if a.fixture:
  assert updater_owner, 'Fixed fixtures are reserved for owned updater qualification'
  workspace=a.fixture.resolve();file=workspace/'proof.txt';assert file.is_file() and not file.is_symlink()
  nonce=file.read_text().strip();assert nonce.startswith('NVIDIA_TOOL_OK_') and len(nonce)==47
 else:
  workspace=Path(tempfile.mkdtemp(prefix='nvidia-dsh-short-'));nonce='NVIDIA_TOOL_OK_'+uuid.uuid4().hex;file=workspace/'proof.txt';file.write_text(nonce+'\n');file.chmod(0o600)
 import yaml
 entries=yaml.safe_load((R/'data/dsh/profiles/headless/cordis.patch.yml').read_text());provider=next(x['config']['providers']['nvidia-strata'] for x in entries if x['id']=='llm-pi-ai');m=next((x for x in provider['models'] if x['id']==a.model),None);m=m or dict(next(x for x in provider['models'] if x['id']==a.model+'-search'),id=a.model);provider=dict(provider,baseURL=timing_tap.base_url,models=[dict(m,maxTokens=128)]);overlay=O/'selection.yml';overlay.write_text(yaml.safe_dump([{'id':'session-title-llm','disabled':True},{'id':'llm-pi-ai','config':{'providers':{'nvidia-strata':provider}}},{'id':'agent-default-model','config':{'provider':'nvidia-strata','model':a.model}}],sort_keys=False))
 task=f'Use the read tool to read {file}. Then reply with only the exact file contents. Do not use bash or any other tools. Do not modify any files.'
 state.update(phase='short-harness-tool',workspace=str(workspace));save();t=time.monotonic()
 stopped_after_tool=False
 with (O/'events.jsonl').open('w') as out,(O/'stderr.txt').open('w') as err:
  run=subprocess.Popen([str(R/'dsh/run'),'--profile','headless','--patch',str(overlay),'--json',task],cwd=workspace,stdout=out,stderr=err)
  deadline=time.monotonic()+600
  while run.poll() is None:
   observed=[]
   for line in (O/'events.jsonl').read_text().splitlines():
    try:observed.append(json.loads(line))
    except ValueError:pass
   ids={e['callId'] for e in observed if e.get('type')=='tool_call' and e.get('tool')=='read'}
   if not a.require_followup and any(e.get('type')=='tool_result' and e.get('status')=='completed' and e.get('callId') in ids and nonce in str(e.get('result','')) for e in observed):
    stopped_after_tool=True;run.terminate();break
   if time.monotonic()>deadline:run.terminate();raise TimeoutError('Short harness tool call exceeded600s')
   time.sleep(.2)
  try:run.wait(timeout=15)
  except subprocess.TimeoutExpired:run.kill();run.wait(timeout=10)

 raw=(O/'events.jsonl').read_text();events=[]
 for line in raw.splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 read_records=[d for e in events for d in walk(e) if any(d.get(key)=='read' for key in ['name','toolName','tool_name','tool'])]
 calls=[e for e in events if e.get('type')=='tool_call' and e.get('tool')=='read']
 results=[e for e in events if e.get('type')=='tool_result' and e.get('status')=='completed' and e.get('callId') in {c['callId'] for c in calls} and nonce in str(e.get('result',''))]
 final=next((e.get('text','') for e in reversed(events) if e.get('type')=='final'),'')
 assert run.returncode==0 or stopped_after_tool or (calls and results),(run.returncode,(O/'stderr.txt').read_text()[-500:]);assert calls and results,'No completed actual read tool round trip';assert prop('InvocationID')==owned
 if a.require_followup:assert nonce in final, 'Missing assistant follow-up using actual tool result'
 state.update(followup_required=a.require_followup,followup_passed=nonce in final)
 state.update(phase='pass',wall_s=time.monotonic()-t,structured_read_records=len(calls),completed_tool_results=len(results),assistant_reply_not_required=True,stopped_after_tool_success=stopped_after_tool,final_marker_returned=nonce in final,strict_final_format=final.strip()==nonce if final else None,event_types=sorted({str(e.get('type')) for e in events if isinstance(e,dict)}),nonce_returned=True,output_cap=128,full_context_stress=False);save()
except BaseException as e:state.update(phase='failed',error=repr(e));save();raise
finally:
 if timing_tap:timing_tap.close()
 if a.updater_owner_file:
  state['unload_owner']='daily updater; child never releases parent reservation'
 elif a.keep_loaded_on_pass and state.get('phase')=='pass':
  state['kept_loaded_for_api_switch']=True
 elif owned and prop('InvocationID')==owned:
  deadline=time.monotonic()+90
  while True:
   try:
    if prop('InvocationID')!=owned:state['unload_deferred']='Worker ownership changed; preserved';break
    req('/router/unload',{});state['unloaded']=True;break
   except urllib.error.HTTPError as e:
    if e.code!=409 or time.monotonic()>deadline:state['unload_deferred']=str(e);break
    time.sleep(2)
   except Exception as e:state['unload_error']=repr(e);break
 state['finished']=time.time();save()
