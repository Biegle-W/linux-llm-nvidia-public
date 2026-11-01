import sys,io,json,tempfile,unittest,http.client
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from short_tool_metrics import ToolMetrics
RealConnection=http.client.HTTPConnection
class Upstream:
 def request(self,*a,**k):pass
 def getresponse(self):
  event={'choices':[{'delta':{'tool_calls':[{'function':{'name':'read','arguments':'{}'}}]},'finish_reason':'tool_calls'}],'usage':{'prompt_tokens':100,'completion_tokens':10},'timings':{'prompt_per_second':50,'predicted_per_second':10}}
  r=io.BytesIO(('data: '+json.dumps(event)+'\n\ndata: [DONE]\n\n').encode());r.status=200;r.getheader=lambda *a:'text/event-stream';return r
 def close(self):pass
class Completion(unittest.TestCase):
 def test_final_frame_and_capture_before_cleanup(self):
  with tempfile.TemporaryDirectory() as folder:
   tap=ToolMetrics(folder,'fixture','test');tap.metrics=lambda:'  \n{\n  "native": true\n}\n'
   try:
    with patch('short_tool_metrics.http.client.HTTPConnection',return_value=Upstream()):
     c=RealConnection('127.0.0.1',tap.server.server_port);c.request('POST','/v1/chat/completions',json.dumps({'stream':True}),{'Authorization':'Bearer fixture','Content-Type':'application/json'});response=c.getresponse();payload=response.read();c.close()
    self.assertTrue(payload.endswith(b'data: [DONE]\n\n'));self.assertTrue((Path(folder)/'tool-benchmark.json').exists())
   finally:tap.close()
if __name__=='__main__':unittest.main()
