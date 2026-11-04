"""Numeric-only timing tap for the first real DSH chat/tool request."""
import http.client,json,threading,time,urllib.request
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from benchmark_models import metric_delta
class ToolMetrics:
 def __init__(self,output,key,model):
  self.output=Path(output);self.key=key;self.model=model;self.claimed=False;self.lock=threading.Lock();self.completed=threading.Event()
  tap=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    if self.path!='/v1/chat/completions' or self.headers.get('Authorization')!='Bearer '+tap.key:
     self.send_error(403);return
    with tap.lock:
     first_request=not tap.claimed
     tap.claimed=True
    if not first_request:
     body=self.rfile.read(int(self.headers['Content-Length']))
     conn=http.client.HTTPConnection('127.0.0.1',10100,timeout=1200)
     try:
      conn.request('POST',self.path,body,{'Authorization':'Bearer '+tap.key,'Content-Type':'application/json'})
      response=conn.getresponse();self.send_response(response.status);self.send_header('Content-Type',response.getheader('Content-Type','text/event-stream'));self.end_headers()
      while line:=response.readline():self.wfile.write(line);self.wfile.flush()
     finally:conn.close()
     return
    body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));body['stream_options']={'include_usage':True};before=tap.metrics();record={'model':tap.model,'measurement':'first actual DSH tool-call generation','loading_excluded':True};usage={};native={};first=last=None;chunks=0;started=time.perf_counter();conn=http.client.HTTPConnection('127.0.0.1',10100,timeout=1200)
    try:
     conn.request('POST',self.path,json.dumps(body),{'Authorization':'Bearer '+tap.key,'Content-Type':'application/json'});response=conn.getresponse();self.send_response(response.status);self.send_header('Content-Type',response.getheader('Content-Type','text/event-stream'));self.end_headers()
     while line:=response.readline():
      if line.startswith(b'data:'):
       payload=line[5:].strip()
       if payload==b'[DONE]':
        after=tap.metrics();tap.finish(record,usage,native,first,last,chunks,started,before,after);self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush();break
       try:
        event=json.loads(payload);usage=event.get('usage') or usage;native=event.get('timings') or native
        if event.get('error'):record['backend_error']=True
        meaningful=False
        for choice in event.get('choices',[]):
         delta=choice.get('delta') or {};meaningful=meaningful or bool(delta.get('content') or delta.get('reasoning_content'))
         for tc in delta.get('tool_calls',[]):meaningful=meaningful or bool((tc.get('function') or {}).get('name') or (tc.get('function') or {}).get('arguments'))
        if meaningful:
         now=time.perf_counter()-started
         if first is None:first=now
         last=now;chunks+=1
       except (ValueError,TypeError):pass
      self.wfile.write(line);self.wfile.flush()
    except (OSError,ValueError) as e:record['capture_error']=type(e).__name__
    finally:
     conn.close()
     if not (tap.output/'tool-benchmark.json').exists():tap.finish(record,usage,native,first,last,chunks,started,before,tap.metrics())
  self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
  self.base_url=f'http://127.0.0.1:{self.server.server_port}/v1'
 def metrics(self):
  try:
   q=urllib.request.Request('http://127.0.0.1:10000/metrics',headers={'Authorization':'Bearer '+self.key})
   with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(q,timeout=3) as f:return f.read(2*1024*1024).decode()
  except (OSError,ValueError):return ''
 def finish(self,r,u,n,first,last,chunks,start,before,after):
  if self.model == 'qwen27b-tensorfold':
   before=before.replace('tensorfold:', 'vllm:');after=after.replace('tensorfold:', 'vllm:')
  # Preserve request evidence before optional backend metric interpretation.
  (self.output/'tool-benchmark-raw.json').write_text(json.dumps(dict(record=r,usage=u,native_timings=n,first=first,last=last,chunks=chunks,generation_wall_s=time.perf_counter()-start),indent=2)+'\n')
  (self.output/'benchmark-metrics-before.txt').write_text(before)
  (self.output/'benchmark-metrics-after.txt').write_text(after)
  def delta(metric,stage=None):
   try:return metric_delta(before,after,metric,stage)[0]
   except (ValueError,TypeError,IndexError):return 0
  prompt=u.get('prompt_tokens');count=u.get('completion_tokens');cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens',n.get('cache_n',0)) or 0
  r.update(prompt_tokens=prompt,output_tokens=count,cached_tokens=cached,native_timings=n,client_ttft_s=first,client_last_token_s=last,meaningful_sse_chunks=chunks,generation_wall_s=time.perf_counter()-start,usage=u)
  r['prefill_tps']=n.get('prompt_per_second');r['prefill_method']='native request timings' if r['prefill_tps'] else None
  if not r['prefill_tps'] and prompt is not None:
   metric='sglang:per_stage_req_latency_seconds' if self.model.endswith('sglang') else 'vllm:request_prefill_time_seconds';stage='prefill_forward' if self.model.endswith('sglang') else None
   seconds=delta(metric+'_sum',stage);requests=delta(metric+'_count',stage)
   if seconds>0 and requests==1:r.update(prefill_tps=max(0,prompt-cached)/seconds,prefill_method=metric+' one-request delta; cached tokens excluded')
  prefix='sglang:' if self.model.endswith('sglang') else 'vllm:';ttft=delta(prefix+'time_to_first_token_seconds_sum');requests=delta(prefix+'time_to_first_token_seconds_count')
  r['ttft_s']=ttft if ttft>0 and requests==1 else first;r['ttft_method']='engine first-token counter' if ttft>0 and requests==1 else 'client first delivered content/tool delta; parser buffering included'
  r['decode_tps']=n.get('predicted_per_second');r['decode_method']='native request timings' if r['decode_tps'] else None
  seconds=delta('vllm:request_decode_time_seconds_sum');requests=delta('vllm:request_decode_time_seconds_count')
  if not r['decode_tps'] and count and count>1 and seconds>0 and requests==1:r.update(decode_tps=(count-1)/seconds,decode_method='vLLM one-request decode counter')
  if not r['decode_tps'] and self.model.endswith('sglang') and count and count>1:
   seconds=delta('sglang:inter_token_latency_seconds_sum');intervals=delta('sglang:inter_token_latency_seconds_count')
   if seconds>0 and intervals==count-1:r.update(decode_tps=intervals/seconds,decode_method='SGLang one-request native inter-token intervals; parser buffering excluded')
  if self.model == 'qwen27b-tensorfold':
   seconds=delta('vllm:request_time_per_output_token_seconds_sum');requests=delta('vllm:request_time_per_output_token_seconds_count')
   if seconds>0 and requests==1:r.update(decode_tps=1/seconds,decode_method='TensorFold one-request native TPOT inverse; short speculative tool burst, not sustained prose')
  if not r['decode_tps']:r['decode_unavailable_reason']='No native decode timing or sufficiently granular client deltas; do not infer from buffered tool-call chunks'
  (self.output/'benchmark-metrics-before.txt').write_text(before);(self.output/'benchmark-metrics-after.txt').write_text(after);(self.output/'tool-benchmark.json').write_text(json.dumps(r,indent=2)+'\n')
  if hasattr(self,'completed'):self.completed.set()
 def close(self):
  if self.claimed:self.completed.wait(timeout=8)
  self.server.shutdown();self.server.server_close()
