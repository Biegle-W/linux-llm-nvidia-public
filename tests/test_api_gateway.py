"""CPU-only API -> hub -> backend contracts; no model or GPU is loaded."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'network'))
import api as gateway
import test_router
import worker_manager as wm

class APIGatewayTests(test_router.RouterTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gateway=ThreadingHTTPServer(('127.0.0.1',0),gateway.Handler)
        cls.gateway.key=test_router.KEY;cls.gateway.allowed=[ipaddress.ip_network('127.0.0.0/8')];cls.gateway.hub_port=cls.server.server_port
        threading.Thread(target=cls.gateway.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown();cls.gateway.server_close();super().tearDownClass()
    def request(self,path,body=None,key=test_router.KEY,raw=None,headers=None):
        c=self.http('127.0.0.1',self.gateway.server_port,timeout=5)
        payload=raw if raw is not None else (json.dumps(body) if body is not None else None)
        h={'Authorization':'Bearer '+key}
        if headers:h.update(headers)
        c.request('POST' if payload is not None else 'GET',path,payload,h)
        r=c.getresponse();data=r.read();status=r.status;c.close();return status,data
    def test_duplicate_lengths_rejected_before_hub_admission(self):
        c=self.http('127.0.0.1',self.gateway.server_port,timeout=5)
        with patch.object(self.server.workers,'acquire') as acquire:
            c.putrequest('POST','/v1/chat/completions');c.putheader('Authorization','Bearer '+test_router.KEY);c.putheader('Content-Length','2');c.putheader('Content-Length','2');c.endheaders(b'{}');response=c.getresponse();self.assertEqual(response.status,400);response.read();c.close();acquire.assert_not_called()
    def test_non_ascii_credentials_return_unauthorized(self):
        status,_=self.request('/health',key='wrong-\xff');self.assertEqual(status,401)
    def test_gateway_has_no_model_owner(self):
        self.assertFalse(hasattr(self.gateway,'workers'))
        status,payload=self.request('/health');self.assertEqual(status,200);self.assertEqual(json.loads(payload)['idle_timeout_seconds'],600)
    def test_client_private_headers_do_not_cross_gateway(self):
        status,_=self.request('/v1/chat/completions',{'model':'qwen27b-hyperqwen','messages':[{'role':'user','content':'hello'}]},headers={'X-Private-Test':'do-not-forward'})
        self.assertEqual(status,200);self.assertNotIn('X-Private-Test',self.backend.forwarded_headers)
    def test_truncated_streams_emit_typed_errors(self):
        class Truncated(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']));self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                frame={'type':'response.created','response':{'id':'resp_partial'}} if self.path.endswith('responses') else {'choices':[{'delta':{'content':'partial'}}]}
                self.wfile.write(b'data: '+json.dumps(frame).encode()+b'\n\n')
        upstream=ThreadingHTTPServer(('127.0.0.1',0),Truncated);threading.Thread(target=upstream.serve_forever,daemon=True).start();old=self.gateway.hub_port;self.gateway.hub_port=upstream.server_port
        try:
            for path in ['/v1/chat/completions','/v1/responses']:
                status,raw=self.request(path,{'model':'qwen27b-hyperqwen','stream':True})
                self.assertEqual(status,200);self.assertIn(b'hub_unavailable',raw)
                self.assertEqual(raw.count(b'[DONE]'),0 if path.endswith('responses') else 1)
                if path.endswith('responses'):self.assertIn(b'event: error',raw)
        finally:self.gateway.hub_port=old;upstream.shutdown();upstream.server_close()
    def test_disconnect_releases_waiting_upstream_connection(self):
        closed=threading.Event()
        class Waiting(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']));self.connection.settimeout(3)
                if not self.connection.recv(1):closed.set()
        upstream=ThreadingHTTPServer(('127.0.0.1',0),Waiting);threading.Thread(target=upstream.serve_forever,daemon=True).start();old=self.gateway.hub_port;self.gateway.hub_port=upstream.server_port
        try:
            c=self.http('127.0.0.1',self.gateway.server_port,timeout=5);c.request('POST','/v1/chat/completions',b'{}',{'Authorization':'Bearer '+test_router.KEY});c.close();self.assertTrue(closed.wait(2))
        finally:self.gateway.hub_port=old;upstream.shutdown();upstream.server_close()

class APIServicePolicy(unittest.TestCase):
    def test_gateway_and_hub_units_are_headless_and_restart_independent(self):
        spec=importlib.util.spec_from_file_location('nvidia_network_install',ROOT/'network/install.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);units=m.api_service_units()
        self.assertEqual(set(units),{'nvidia-model-router','nvidia-model-hub'})
        for value in units.values():
            self.assertIn('KillMode=process',value);self.assertIn('NVIDIA_API_ONLY=1',value);self.assertNotIn('visible_terminal',value)
        self.assertIn('Wants=nvidia-model-hub.service',units['nvidia-model-router']);self.assertNotIn('PartOf=',units['nvidia-model-hub'])
    def test_api_launch_skips_monitor_and_preserves_worker_guards(self):
        profile=wm.all_profiles()['bolt-llamacpp']
        with tempfile.TemporaryDirectory() as folder,patch.object(wm,'ROOT',Path(folder)),patch.object(wm,'STATE',Path(folder)/'data/router/worker.json'),patch.object(wm,'profiles',return_value={'bolt-llamacpp':profile}),patch.dict(os.environ,{'NVIDIA_API_ONLY':'1'}),patch.object(wm,'open_monitor') as monitor,patch.object(wm.subprocess,'run',return_value=Mock(returncode=0)) as launch,patch.object(wm,'unit_property',side_effect=lambda unit,key:'active' if key=='ActiveState' else 'a'*32):
            manager=wm.Workers.__new__(wm.Workers);manager.wait_native_idle=Mock();manager.stop_owned=Mock();manager.backend_models=Mock(return_value=[{'id':'bolt'}]);manager.key=test_router.KEY;manager.timeout=2;manager.active=None
            manager.start('bolt-llamacpp');monitor.assert_not_called();cmd=launch.call_args.args[0]
            for guard in ['--property=MemoryHigh=94242156544','--property=MemoryMax=96389640192','--property=MemorySwapMax=infinity','--property=OOMPolicy=kill','--setenv=NVIDIA_API_ONLY=1']:self.assertIn(guard,cmd)
            self.assertEqual(cmd[-1],'bolt-llamacpp')

if __name__=='__main__':unittest.main()
