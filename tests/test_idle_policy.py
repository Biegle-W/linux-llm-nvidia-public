"""Idle boundaries, reservation ownership and native FIFO adapter regressions."""
import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'network'),str(ROOT/'scripts')]
from worker_manager import Workers
from idle_control import claim,release,owned_native_idle
from native_idle_policy import transform, vision_phases


class VisionPhaseTest(unittest.TestCase):
    def test_loading_compute_and_error_depths_are_distinct(self):
        source = '''class Vision:
    def _start(self):
        self.observed.append(('load', self._managed_loading_depth, self._managed_encoding_depth))
    def encode(self, fail=False):
        self._start()
        self.observed.append(('compute', self._managed_loading_depth, self._managed_encoding_depth))
        if fail:
            raise ValueError('fixture')
        return 'encoded'
'''
        namespace = {}
        exec(vision_phases(source), namespace)
        vision = namespace['Vision']()
        vision.observed = []
        self.assertEqual(vision.encode(), 'encoded')
        self.assertEqual(vision.observed, [('load', 1, 1), ('compute', 0, 1)])
        with self.assertRaises(ValueError):
            vision.encode(fail=True)
        self.assertEqual(vision._managed_loading_depth, 0)
        self.assertEqual(vision._managed_encoding_depth, 0)


class DenseIdleTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'data').mkdir()
        mock=patch('worker_manager.ROOT',self.root);mock.start();self.addCleanup(mock.stop)
        w=Workers.__new__(Workers);w.key='fixture';w.idle_timeout=600;w.active='qwen27b-hyperqwen'
        w.busy=False;w.loading=None;w.lock=threading.Lock();w.last_activity=0;w.idle_unloading=None
        self.phase='idle';w._idle_probe=SimpleNamespace(profile=w.active,phase=lambda:self.phase)
        self.stops=[]
        def stop(**kw):self.stops.append(kw);w.active=None
        w.stop_owned=stop;self.worker=w
    def test_expiry_is_not_early_and_stops_only_dense(self):
        self.assertFalse(self.worker.idle_tick(599))
        self.assertTrue(self.worker.idle_tick(600))
        self.assertEqual(self.stops[0]['only_unit'],'llm-test-qwen27b.service')
        self.assertFalse((self.root/'data/GPU-LOCK').exists())
    def test_busy_loading_and_existing_reservation_defer(self):
        for field in ['busy','loading']:
            setattr(self.worker,field,True)
            self.assertFalse(self.worker.idle_tick(1000))
            setattr(self.worker,field,False if field=='busy' else None)
        path=self.root/'data/GPU-LOCK';path.write_text('{"owner":"benchmark"}')
        self.assertFalse(self.worker.idle_tick(1000));self.assertEqual(json.loads(path.read_text())['owner'],'benchmark')
        self.assertFalse(self.stops)
    def test_direct_running_gauge_and_router_lock_defer(self):
        self.phase='inference';self.assertFalse(self.worker.idle_tick(1000))
        self.assertEqual(self.worker.last_activity,1000)
        self.phase='idle';self.worker.lock.acquire()
        self.assertFalse(self.worker.idle_tick(2000));self.worker.lock.release()
    def test_request_start_on_final_recheck_preserves_worker(self):
        phases=iter(['idle','inference']);self.worker._idle_probe.phase=lambda:next(phases)
        self.assertFalse(self.worker.idle_tick(1000));self.assertFalse(self.stops)
        self.assertFalse((self.root/'data/GPU-LOCK').exists())
    def test_missing_telemetry_never_justifies_unload(self):
        self.worker._idle_probe.phase=lambda:(_ for _ in ()).throw(OSError('missing'))
        self.assertFalse(self.worker.idle_tick(1000));self.assertFalse(self.stops)
    def test_reservation_release_does_not_delete_another_owner(self):
        path=self.root/'data/GPU-LOCK';owner=claim(path,'fixture')
        path.write_text('{"owner":"other"}');release(path,owner)
        self.assertTrue(path.exists())
    def test_native_idle_claim_requires_owned_cgroup(self):
        path=self.root/'data/GPU-LOCK';path.write_text('{"owner":"native-idle","pid":123}')
        self.assertTrue(owned_native_idle(path,lambda _: '0::/user/llm-router-worker.service'))
        self.assertFalse(owned_native_idle(path,lambda _: '0::/unrelated.service'))


class NativeAdapterTest(unittest.TestCase):
    def _method(self,family):
        source=ROOT/('runtimes/project-maya/serve/server.py' if family=='maya' else 'runtimes/strata-terminal/terminal/0.1.51/serve/server.py')
        if not source.exists():self.skipTest('Installed native source is not part of a public checkout.')
        raw=source.read_bytes().decode();patched=transform(raw,family)
        self.assertEqual(transform(patched,family),patched)
        if '\r\n' in raw:self.assertEqual(patched.count('\r\n'),patched.count('\n'))
        tree=ast.parse(patched);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Service')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='unload')
        ns={'os':os,'Path':Path,'json':json,'time':SimpleNamespace(time=lambda:1000,monotonic_ns=lambda:123),'wait_gpu_release':lambda _pid:None}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'<native-idle-fixture>','exec'),ns)
        return ns['unload']
    def _exercise(self,family):
        method=self._method(family)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'GPU-LOCK';activity=Path(directory)/'activity';activity.write_text('1')
            calls=[]
            class Fifo:
                busy=False
                def acquire(self,blocking=False):return not self.busy
                def release(self):pass
            class Engine:
                ended=False;proc=None
                def alive(self):return not self.ended
                def restart(self):self.ended=False
                def close(self):calls.append('engine');self.ended=True
                unload=close
            vision=SimpleNamespace(lock=threading.RLock(),_stop=lambda:calls.append('vision'),unload=lambda:calls.append('vision'))
            svc=SimpleNamespace(fifo=Fifo(),engine=Engine(),vision=vision,status_lock=threading.Lock(),status={'busy':False,'queued':0},active=0,reload=None,last_request_at=1,started_at=1,idle_lock_path=str(path),idle_activity_path=str(activity))
            path.write_text('{"owner":"benchmark"}')
            self.assertEqual(method(svc,600),'busy');self.assertFalse(calls)
            path.unlink();svc.fifo.busy=True
            self.assertEqual(method(svc,600),'busy');self.assertFalse(calls)
            svc.fifo.busy=False;activity.write_text('900')
            self.assertEqual(method(svc,600),'busy');self.assertFalse(calls)
            activity.write_text('1')
            self.assertEqual(method(svc,600),'unloaded');self.assertFalse(path.exists())
            if family=='maya':self.assertEqual(calls,['vision','engine'])
    def test_maya_fifo_reservation_and_vision_cleanup(self):self._exercise('maya')
    def test_strata_fifo_reservation_and_vision_cleanup(self):self._exercise('strata')


if __name__=='__main__':unittest.main()
