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
import backend_proxy
from request_admission import RequestAdmission
from worker_manager import Workers, RouterError

KEY='test-router-key-'+'x'*40

class Backend(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.body=body
        self.server.forwarded_headers=dict(self.headers)
        self.server.path=self.path
        if self.path == '/v1/responses' and not body.get('mock_error'):
            response={'id':'resp_test','object':'response','status':'completed','model':'worker-name',
                      'output':[{'id':'msg_test','type':'message','role':'assistant','status':'completed',
                                 'content':[{'type':'output_text','text':'ok','annotations':[]}]}]}
            if body.get('stream'):
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                for event in [{'type':'response.created','response':dict(response,status='in_progress',output=[])},
                              {'type':'response.output_text.delta','delta':'ok','item_id':'msg_test','output_index':0,'content_index':0},
                              {'type':'response.completed','response':response}]:
                    self.wfile.write(('event: '+event['type']+'\ndata: '+json.dumps(event)+'\n\n').encode())
            else:
                payload=json.dumps(response).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            return
        if body.get('mock_error'):
            payload=('backend overloaded '+KEY).encode()
            self.send_response(503);self.send_header('Content-Type','text/plain')
            self.send_header('Content-Length',str(len(payload)));self.end_headers()
            self.wfile.write(payload);return
        if body.get('stream'):
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            chunk={'model':'worker-name','choices':[{'delta':{'tool_calls':[{'index':0,'id':'call_1','type':'function','function':{'name':'read_file','arguments':'{"path":"check.txt"}'}}]}}]}
            self.wfile.write(b'data: '+json.dumps(chunk).encode()+b'\n\ndata: [DONE]\n\n')
        else:
            payload=json.dumps({'model':'worker-name','choices':[{'message':{'content':'ok'}}]}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

class FakeWorkers:
    active=None;loading=None;busy=False;idle_timeout=600;last_activity=time.monotonic()
    def request_status(self):return dict(queued=0,inflight=int(self.busy),max_inflight=1,max_queued=8,same_model_concurrency=False)
    def acquire(self,name,progress=lambda:None,clear_guard=False):self.active=name;self.busy=True;self.clear_guard=clear_guard
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
        cls.http=backend_proxy.http.client.HTTPConnection
        cls.redirect=patch.object(backend_proxy.http.client,'HTTPConnection',side_effect=lambda host,port,**kw:cls.http(host,cls.backend.server_port if port==10000 else port,**kw))
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
        self.assertEqual(next(m for m in models if m['id']=='deepseek-strata')['context_window'],router.profiles()['deepseek-strata']['allocated_context'])
    def test_explicit_selection_requests_guard_reload(self):
        status,_=self.request('/router/select',{'model':'qwen27b-hyperqwen'})
        self.assertEqual(status,200)
        self.assertTrue(self.server.workers.clear_guard)
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

    def test_sglang_profile_applies_non_thinking_default(self):
        status,_=self.request('/v1/chat/completions',{'model':'qwen27b-sglang','messages':[]})
        self.assertEqual(status,200)
        self.assertEqual(self.backend.body['chat_template_kwargs']['enable_thinking'],False)
    def test_explicit_thinking_override_survives_streaming(self):
        status,_=self.request('/v1/chat/completions',{'model':'qwen27b-sglang','messages':[],'stream':True,'chat_template_kwargs':{'enable_thinking':True,'custom':'preserved'}})
        self.assertEqual(status,200)
        self.assertEqual(self.backend.body['chat_template_kwargs'],{'enable_thinking':True,'custom':'preserved'})
    def test_bad_template_options_rejected_before_forwarding(self):
        self.assertEqual(self.request('/v1/chat/completions',{'model':'qwen27b-sglang','messages':[],'chat_template_kwargs':[]})[0],400)

    def test_health_exposes_capacity_and_request_state(self):
        status,data=self.request('/health');self.assertEqual(status,200)
        state=json.loads(data)
        self.assertEqual(state['max_inflight'],1)
        self.assertEqual(state['max_queued'],8)
        self.assertEqual(state['idle_timeout_seconds'],600)
        self.assertGreaterEqual(state['idle_for_s'],0)
        self.assertFalse(state['same_model_concurrency'])

    def test_plain_backend_error_preserves_status_and_redacts_key(self):
        status,data=self.request('/v1/chat/completions',{'model':'qwen27b-sglang','mock_error':True})
        self.assertEqual(status,503);self.assertIn(b'backend overloaded',data)
        self.assertNotIn(KEY.encode(),data);self.assertIn(b'[redacted]',data)
        self.assertFalse(self.server.workers.busy)

    def test_stream_backend_error_carries_original_status(self):
        status,data=self.request('/v1/chat/completions',{'model':'qwen27b-sglang','mock_error':True,'stream':True})
        self.assertEqual(status,200)  # SSE headers precede loading and backend response
        event=next(json.loads(line[5:]) for line in data.splitlines() if line.startswith(b'data:') and line[5:].strip()!=b'[DONE]')
        self.assertEqual(event['error']['status'],503)
        self.assertIn('backend overloaded',event['error']['message'])
        self.assertNotIn(KEY.encode(),data);self.assertFalse(self.server.workers.busy)

    def test_transport_does_not_forward_client_cookies_or_headers(self):
        self.request('/v1/chat/completions',{'model':'qwen27b-sglang'},headers={'Cookie':'private-client-session','X-Client-Secret':'not-for-backend'})
        headers=self.backend.forwarded_headers
        self.assertEqual(headers['Authorization'],'Bearer '+KEY)
        self.assertNotIn('Cookie',headers);self.assertNotIn('X-Client-Secret',headers)

    def test_full_queue_returns_retryable_error_before_backend(self):
        with patch.object(self.server.workers,'acquire',side_effect=RouterError('Queue full','router_queue_full',429)):
            client=self.http('127.0.0.1',self.server.server_port,timeout=3)
            client.request('POST','/v1/chat/completions',json.dumps({'model':'qwen27b-sglang'}),{'Authorization':'Bearer '+KEY})
            response=client.getresponse()
            self.assertEqual(response.status,429);self.assertEqual(response.getheader('Retry-After'),'5')
            self.assertEqual(json.loads(response.read())['error']['code'],'router_queue_full');client.close()

    def test_responses_nonstream_preserves_input_and_alias(self):
        body={'model':'qwen27b-hyperqwen','input':[{'role':'user','content':[{'type':'input_text','text':'hello'}]}],
              'max_output_tokens':32,'store':False,'tools':[{'type':'function','name':'check','parameters':{'type':'object'}}]}
        status,data=self.request('/v1/responses',body);row=json.loads(data)
        self.assertEqual(status,200);self.assertEqual(row['object'],'response');self.assertEqual(row['model'],'qwen27b-hyperqwen')
        self.assertEqual(self.backend.path,'/v1/responses');self.assertEqual(self.backend.body['input'],body['input'])
        self.assertEqual(self.backend.body['max_output_tokens'],32);self.assertEqual(self.backend.body['tools'],body['tools'])
        self.assertEqual(self.backend.body['model'],'worker-name')

    def test_responses_stream_keeps_typed_events_and_nested_alias(self):
        status,data=self.request('/v1/responses',{'model':'qwen27b-hyperqwen','input':'hello','stream':True})
        self.assertEqual(status,200);self.assertIn(b'event: response.output_text.delta',data);self.assertNotIn(b'[DONE]',data)
        events=[json.loads(line[5:]) for line in data.splitlines() if line.startswith(b'data:')]
        self.assertEqual([x['type'] for x in events],['response.created','response.output_text.delta','response.completed'])
        self.assertEqual(events[0]['response']['model'],'qwen27b-hyperqwen');self.assertEqual(events[-1]['response']['model'],'qwen27b-hyperqwen')
        self.assertEqual(events[1]['delta'],'ok')

    def test_responses_stream_error_is_typed_and_redacts_backend_key(self):
        status,data=self.request('/v1/responses',{'model':'qwen27b-hyperqwen','input':'hello','stream':True,'mock_error':True})
        self.assertEqual(status,200);self.assertIn(b'event: error',data);self.assertNotIn(KEY.encode(),data)
        event=next(json.loads(line[5:]) for line in data.splitlines() if line.startswith(b'data:'))
        self.assertEqual(event['type'],'error');self.assertEqual(event['code'],'backend_error');self.assertNotIn(b'[DONE]',data)

    def test_responses_unknown_model_rejected_before_acquire(self):
        with patch.object(self.server.workers,'acquire') as acquire:
            status,_=self.request('/v1/responses',{'model':'not-a-model','input':'hello'})
        self.assertEqual(status,404);acquire.assert_not_called()


class SwitchTest(unittest.TestCase):
    def test_latched_worker_does_not_auto_restart(self):
        from worker_manager import ROOT as active_root
        latch=active_root/'data/router/guard-stops/qwen27b-hyperqwen.json'
        latch.parent.mkdir(parents=True,exist_ok=True)
        latch.write_text('{}')
        worker=Workers.__new__(Workers)
        with self.assertRaises(RouterError) as error:
            worker.start('qwen27b-hyperqwen')
        self.assertEqual(error.exception.code,'safety_guard_latched')
    def test_explicit_reload_clears_only_its_latch(self):
        from worker_manager import ROOT as active_root
        latch=active_root/'data/router/guard-stops/qwen27b-hyperqwen.json'
        other=active_root/'data/router/guard-stops/glm-maya.json'
        latch.parent.mkdir(parents=True,exist_ok=True)
        latch.write_text('{}');other.write_text('{}')
        worker=Workers.__new__(Workers)
        worker.lock=RequestAdmission();worker.busy=False
        worker.start=lambda _name,_progress: self.assertFalse(latch.exists())
        worker.acquire('qwen27b-hyperqwen',clear_guard=True)
        worker.release()
        self.assertTrue(other.exists())
    def test_gpu_lock_preserves_latch_during_explicit_reload(self):
        from worker_manager import ROOT as active_root
        latch=active_root/'data/router/guard-stops/qwen27b-hyperqwen.json'
        latch.parent.mkdir(parents=True,exist_ok=True)
        latch.write_text('{}');(active_root/'data/GPU-LOCK').write_text('{}')
        worker=Workers.__new__(Workers)
        worker.lock=RequestAdmission();worker.busy=False
        with self.assertRaises(RouterError):
            worker.acquire('qwen27b-hyperqwen',clear_guard=True)
        self.assertTrue(latch.exists())
        self.assertFalse(worker.busy)
    def setUp(self):
        # Switching tests must not inspect the live worker's GPU reservation or state.
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root=Path(directory.name)
        for name,value in [('ROOT',root),('STATE',root/'data/router/worker.json')]:
            mock=patch('worker_manager.'+name,value)
            mock.start();self.addCleanup(mock.stop)
    def worker(self):
        w=Workers.__new__(Workers);w.lock=RequestAdmission();w.busy=False;w.started=[]
        w.detect=unittest.mock.Mock(return_value=None)  # Never inspect a live GPU worker from a CPU fixture.
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
        for field in ['busy', 'loading', 'compute_active']:
            with self.subTest(field=field):
                w=self.worker();w.active='flash-next-strata';w.key=KEY
                w.stop_owned=unittest.mock.Mock(side_effect=RouterError('stop marker'))
                responses=[io.BytesIO(json.dumps({'busy':False,field:True}).encode()),
                           io.BytesIO(b'{"busy":false}')]
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
    def test_native_loading_and_compute_block_manual_unload(self):
        from worker_manager import ROOT as active_root
        w=self.worker();w.key=KEY
        def properties(unit,prop):
            if unit != 'llm-router-worker.service':return 'inactive'
            return 'active' if prop=='ActiveState' else str(active_root/'scripts/serve_router_moe.py')
        for field in ['busy','queued','loading','compute_active']:
            with self.subTest(field=field),patch('worker_manager.unit_property',side_effect=properties), \
                 patch('worker_manager.OPENER.open',return_value=io.BytesIO(json.dumps({'busy':False,field:True}).encode())), \
                 patch('worker_manager.subprocess.run') as run:
                with self.assertRaises(RouterError) as result:w.stop_owned()
                self.assertEqual(result.exception.code,'backend_busy');run.assert_not_called()
    def test_unknown_native_state_preserves_worker(self):
        from worker_manager import ROOT as active_root
        w=self.worker();w.key=KEY
        def properties(unit,prop):
            if unit != 'llm-router-worker.service':return 'inactive'
            return 'active' if prop=='ActiveState' else str(active_root/'scripts/serve_router_moe.py')
        with patch('worker_manager.unit_property',side_effect=properties), \
             patch('worker_manager.OPENER.open',side_effect=OSError('unavailable')), \
             patch('worker_manager.subprocess.run') as run:
            with self.assertRaises(RouterError):w.stop_owned()
            run.assert_not_called()



class WorkerReattachmentTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import Mock
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'data/router').mkdir(parents=True)
        self.state=self.root/'data/router/worker.json'
        self.state.write_text(json.dumps({'profile':'flash-next-strata','unit':'llm-router-worker.service','invocation':'owned-invocation'}))
        for name,value in [('ROOT',self.root),('STATE',self.state)]:
            p=patch('worker_manager.'+name,value);p.start();self.addCleanup(p.stop)
        self.w=Workers.__new__(Workers);self.w.active=None;self.w.loading=None;self.w.key=KEY;self.w.timeout=5
        self.w.wait_native_idle=Mock();self.w.touch_activity=Mock()
        self.w.detect=Mock(return_value='flash-next-strata')
        self.w.backend_models=Mock(return_value=[{'id':'native-model'}])
        self.w.stop_owned=Mock(side_effect=AssertionError('Existing worker must not restart'))
        native=patch('worker_manager.OPENER.open',side_effect=lambda *a,**k:io.BytesIO(b'{"busy":false}'))
        native.start();self.addCleanup(native.stop)
        def prop(unit,name):
            if unit!='llm-router-worker.service':return '0' if name=='MainPID' else 'inactive'
            return {'ActiveState':'active','InvocationID':'owned-invocation','ExecStart':str(self.root/'scripts/serve_router_moe.py')+' flash-next-strata'}.get(name,'')
        p=patch('worker_manager.unit_property',side_effect=prop);p.start();self.addCleanup(p.stop)

    def test_ready_external_worker_is_adopted_without_restart(self):
        self.w.start('flash-next-strata')
        self.assertEqual(self.w.active,'flash-next-strata');self.w.stop_owned.assert_not_called()

    def test_retry_waits_for_existing_cold_load(self):
        self.w.backend_models.side_effect=[[],[],[{'id':'native-model'}]]
        with patch('worker_manager.time.sleep'):
            self.w.start('flash-next-strata')
        self.assertEqual(self.w.active,'flash-next-strata');self.assertIsNone(self.w.loading)
        self.w.stop_owned.assert_not_called()

    def test_disconnected_retry_preserves_loader_and_can_resume(self):
        from unittest.mock import Mock
        self.w.backend_models.side_effect=[[],[{'id':'native-model'}]]
        progress=Mock(side_effect=BrokenPipeError('Client disconnected'))
        with self.assertRaises(BrokenPipeError):self.w.start('flash-next-strata',progress)
        self.assertIsNone(self.w.loading);self.w.stop_owned.assert_not_called()
        self.w.start('flash-next-strata');self.w.stop_owned.assert_not_called()

    def test_invocation_change_during_wait_preserves_replacement(self):
        self.w.backend_models.return_value=[]
        def progress():self.state.write_text(json.dumps({'profile':'flash-next-strata','unit':'llm-router-worker.service','invocation':'replacement'}))
        with self.assertRaises(RouterError):self.w.start('flash-next-strata',progress)
        self.w.stop_owned.assert_not_called()

    def test_ready_listener_without_verified_owner_is_not_adopted(self):
        self.w.active='flash-next-strata';self.w.detect.return_value=None
        self.w.stop_owned.side_effect=RouterError('Unrecognized worker preserved','ownership_conflict')
        with self.assertRaises(RouterError):self.w.start('flash-next-strata')
        self.w.stop_owned.assert_called_once()

    def test_reservation_still_blocks_adoption(self):
        (self.root/'data/GPU-LOCK').write_text('{}')
        with self.assertRaises(RouterError):self.w.start('flash-next-strata')
        self.w.detect.assert_not_called();self.w.stop_owned.assert_not_called()

    def test_detection_rejects_forged_unit_record(self):
        self.state.write_text(json.dumps({'profile':'flash-next-strata','unit':'other.service','invocation':'owned-invocation'}))
        with patch('worker_manager.unit_property',side_effect=lambda unit,key:'0' if key=='MainPID' else 'owned-invocation' if key=='InvocationID' else 'active'):
            self.assertIsNone(Workers.detect(self.w))


    def test_other_model_waits_for_owned_loader_before_safe_switch(self):
        self.w.backend_models.side_effect=[[],[],[{'id':'native-model'}]]
        self.w.stop_owned.side_effect=RouterError('safe-switch-marker')
        with patch('worker_manager.time.sleep'):
            with self.assertRaisesRegex(RouterError,'safe-switch-marker'):
                self.w.start('qwen27b-hyperqwen')
        self.assertEqual(self.w.backend_models.call_count,3)
        self.w.stop_owned.assert_called_once();self.assertIsNone(self.w.loading)

    def test_existing_loader_timeout_does_not_stop_or_replace_it(self):
        self.w.backend_models.return_value=[]
        with patch('worker_manager.time.monotonic',side_effect=[0,0,10]),patch('worker_manager.time.sleep'):
            with self.assertRaises(RouterError) as error:self.w.start('flash-next-strata')
        self.assertEqual(error.exception.code,'load_timeout');self.w.stop_owned.assert_not_called()

    def test_guard_latch_appearing_during_loading_remains_latched(self):
        self.w.backend_models.return_value=[]
        latch=self.root/'data/router/guard-stops/flash-next-strata.json'
        def progress():latch.parent.mkdir(exist_ok=True);latch.write_text('{}')
        with self.assertRaises(RouterError) as error:self.w.start('flash-next-strata',progress)
        self.assertEqual(error.exception.code,'safety_guard_latched');self.assertTrue(latch.exists())
        self.w.stop_owned.assert_not_called()

    def test_new_reservation_during_loading_preserves_worker(self):
        self.w.backend_models.return_value=[]
        def progress():(self.root/'data/GPU-LOCK').write_text('{}')
        with self.assertRaises(RouterError) as error:self.w.start('flash-next-strata',progress)
        self.assertEqual(error.exception.code,'gpu_reserved');self.w.stop_owned.assert_not_called()

    def test_native_idle_unloaded_model_uses_existing_reload_path(self):
        self.w.backend_models.return_value=[{'id':'native-model','status':{'value':'unloaded'}}]
        self.w.stop_owned.side_effect=RouterError('guarded-reload-marker')
        with self.assertRaisesRegex(RouterError,'guarded-reload-marker'):self.w.start('flash-next-strata')
        self.w.stop_owned.assert_called_once()




class ProtocolDiagnosticsTests(unittest.TestCase):
    def handler(self, enabled=True, path='/v1/chat/completions?key=private-query'):
        from types import SimpleNamespace
        h=router.Handler.__new__(router.Handler);h.server=SimpleNamespace(protocol_diagnostics=enabled)
        h.command='POST';h.path=path;return h
    def test_default_disabled_logs_nothing(self):
        with patch('builtins.print') as output:self.handler(False).log_message('"%s" %s %s','secret',200,'-')
        output.assert_not_called()
    def test_enabled_logs_only_protocol_metadata(self):
        with patch('builtins.print') as output:self.handler().log_message('"%s" %s %s',KEY,400,'-')
        value=json.loads(output.call_args.args[0]);self.assertEqual(value,{'event':'api_protocol','method':'POST','path':'/v1/chat/completions','status':400})
        self.assertNotIn(KEY,output.call_args.args[0]);self.assertNotIn('private-query',output.call_args.args[0])
    def test_unknown_paths_and_malformed_urls_are_hidden(self):
        for path in ['/secret/'+KEY,'http://[invalid']:
            self.assertEqual(router.protocol_path(path),'<other>')
    def test_common_endpoint_mismatches_are_visible_without_query(self):
        for path in ['/v1/responses','/v1/v1/chat/completions','/v1/chat/completions/','/chat/completions']:
            self.assertEqual(router.protocol_path(path+'?secret=x'),path)

if __name__=='__main__':unittest.main()
