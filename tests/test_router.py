"""CPU-only routing checks: auth, framing, tool transport and safe switching."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
import io
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'network'))
import router
from worker_manager import Workers, RouterError

KEY='test-router-key-'+'x'*40

class Backend(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.body=body
        if body.get('stream'):
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            chunk={'model':'worker-name','choices':[{'delta':{'tool_calls':[{'index':0,'id':'call_1','type':'function','function':{'name':'read_file','arguments':'{"path":"check.txt"}'}}]}}]}
            self.wfile.write(b'data: '+json.dumps(chunk).encode()+b'\n\ndata: [DONE]\n\n')
        else:
            payload=json.dumps({'model':'worker-name','choices':[{'message':{'content':'ok'}}]}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

class FakeWorkers:
    active=None;loading=None;busy=False
    def acquire(self,name,progress=lambda:None):self.active=name;self.busy=True
    def release(self):self.busy=False
    def backend_models(self):return [{'id':'worker-name'}]

class RouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend=ThreadingHTTPServer(('127.0.0.1',0),Backend)
        threading.Thread(target=cls.backend.serve_forever,daemon=True).start()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),router.Handler)
        cls.server.key=KEY;cls.server.workers=FakeWorkers()
        cls.server.allowed=[router.ipaddress.ip_network('127.0.0.0/8')]
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.http=router.http.client.HTTPConnection
        cls.redirect=patch.object(router.http.client,'HTTPConnection',side_effect=lambda host,port,**kw:cls.http(host,cls.backend.server_port if port==10000 else port,**kw))
        cls.redirect.start()
    @classmethod
    def tearDownClass(cls):
        cls.redirect.stop()
        for s in [cls.server,cls.backend]:s.shutdown();s.server_close()
    def request(self,path,body=None,key=KEY,raw=None,headers=None):
        c=self.http('127.0.0.1',self.server.server_port,timeout=3)
        payload=raw if raw is not None else (json.dumps(body) if body is not None else None)
        h={'Authorization':'Bearer '+key}
        if headers:h.update(headers)
        c.request('POST' if payload is not None else 'GET',path,payload,h)
        r=c.getresponse();data=r.read();status=r.status;c.close();return status,data
    def test_auth(self):
        for key in ['', 'wrong']:
            self.assertEqual(self.request('/v1/models',key=key)[0],401)
    def test_catalog(self):
        status,data=self.request('/v1/models');self.assertEqual(status,200)
        models=json.loads(data)['data'];self.assertEqual(len(models),6)
        self.assertEqual(next(m for m in models if m['id']=='deepseek-strata')['context_window'],65536)
    def test_unknown_model_never_loads(self):
        before=self.server.workers.active
        self.assertEqual(self.request('/v1/chat/completions',{'model':'qwen27b-llama'})[0],404)
        self.assertEqual(self.server.workers.active,before)
    def test_bad_framing(self):
        self.assertEqual(self.request('/v1/chat/completions',raw='{}',headers={'Transfer-Encoding':'chunked'})[0],400)
        self.assertEqual(self.request('/v1/chat/completions',raw='[]')[0],400)
        self.assertEqual(self.request('/v1/chat/completions',raw='bad')[0],400)
    def test_nonstream_alias(self):
        status,data=self.request('/v1/chat/completions',{'model':'qwen27b-hyperqwen','messages':[]})
        self.assertEqual(status,200);self.assertEqual(json.loads(data)['model'],'qwen27b-hyperqwen')
        self.assertEqual(self.backend.body['model'],'worker-name')
    def test_stream_tool_calls_preserved(self):
        status,data=self.request('/v1/chat/completions',{'model':'qwen27b-hyperqwen','messages':[],'stream':True,'tools':[{'type':'function','function':{'name':'read_file'}}]})
        self.assertEqual(status,200);self.assertIn(b'[DONE]',data)
        events=[json.loads(l[5:]) for l in data.splitlines() if l.startswith(b'data:') and b'[DONE]' not in l]
        self.assertEqual(events[0]['model'],'qwen27b-hyperqwen')
        self.assertEqual(events[0]['choices'][0]['delta']['tool_calls'][0]['function']['arguments'],'{"path":"check.txt"}')
        self.assertEqual(self.backend.body['tools'][0]['function']['name'],'read_file')
        self.assertFalse(self.server.workers.busy)
    def test_unsupported_completion(self):
        self.assertEqual(self.request('/v1/completions',{'model':'deepseek-strata','prompt':'x'})[0],400)

class SwitchTest(unittest.TestCase):
    def worker(self):
        w=Workers.__new__(Workers);w.lock=threading.Lock();w.busy=False;w.started=[]
        w.start=lambda name,progress=lambda:None:w.started.append(name)
        return w
    def test_switch_waits_for_reply(self):
        w=self.worker();w.acquire('first');acquired=threading.Event()
        def second():w.acquire('second');acquired.set();w.release()
        t=threading.Thread(target=second);t.start()
        self.assertFalse(acquired.wait(.1));self.assertEqual(w.started,['first'])
        w.release();t.join(2);self.assertTrue(acquired.is_set());self.assertEqual(w.started,['first','second'])
    def test_failed_load_releases_lock(self):
        w=self.worker()
        def fail(*_):raise RouterError('failed')
        w.start=fail
        with self.assertRaises(RouterError):w.acquire('first')
        self.assertFalse(w.busy);self.assertTrue(w.lock.acquire(blocking=False));w.lock.release()
    def test_desktop_gpu_context_is_preserved(self):
        w=self.worker()
        with tempfile.TemporaryDirectory() as directory, patch('worker_manager.STATE',Path(directory)/'state.json'), patch('worker_manager.unit_property',return_value='inactive'), patch('worker_manager.subprocess.check_output',return_value='12345\n'), patch('worker_manager.socket.socket') as sock, patch('worker_manager.subprocess.run') as run:
            sock.return_value.__enter__.return_value.connect_ex.return_value=1
            w.stop_owned()
            run.assert_not_called()
    def test_native_reply_is_observed_before_switch(self):
        w=self.worker();w.active='flash-next-strata';w.key=KEY
        w.stop_owned=unittest.mock.Mock(side_effect=RouterError('stop marker'))
        responses=[io.BytesIO(b'{"busy":true}'),io.BytesIO(b'{"busy":false}')]
        progress=unittest.mock.Mock()
        with patch('worker_manager.OPENER.open',side_effect=responses),patch('worker_manager.time.sleep'):
            with self.assertRaisesRegex(RouterError,'stop marker'):
                Workers.start(w,'qwen27b-hyperqwen',progress)
        progress.assert_called_once();w.stop_owned.assert_called_once()
    def test_gpu_reservation_blocks_unload(self):
        w=self.worker()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir();(root/'data/GPU-LOCK').write_text('reserved')
            with patch('worker_manager.ROOT',root),patch('worker_manager.subprocess.run') as run:
                with self.assertRaisesRegex(RouterError,'reserved'):w.stop_owned()
                run.assert_not_called()
    def test_unrecognized_unit_preserved(self):
        w=self.worker()
        with patch('worker_manager.unit_property',side_effect=lambda unit,prop:'active' if prop=='ActiveState' else '/unrelated/app'),patch('worker_manager.subprocess.run') as run:
            with self.assertRaises(RouterError):w.stop_owned()
            run.assert_not_called()

if __name__=='__main__':unittest.main()
