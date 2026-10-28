"""Backend viewer closure is separate from router, harness and worker ownership."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'network')]
import visible_terminal as console
import worker_manager as workers


class BackendConsole(unittest.TestCase):
    def test_only_backend_viewers_end_when_a_worker_stops_or_changes(self):
        for unit in console.BACKEND_UNITS:
            self.assertTrue(console.backend_finished(unit,'first',{'ActiveState':'inactive'}))
            self.assertTrue(console.backend_finished(unit,'first',{'ActiveState':'active','InvocationID':'second'}))
            self.assertFalse(console.backend_finished(unit,'first',{'ActiveState':'active','InvocationID':'first'}))
            self.assertFalse(console.backend_finished(unit,None,{'ActiveState':'inactive'}))
        for unit in ['nvidia-model-router.service','nvidia-dsh.service','benchmark.service']:
            self.assertFalse(console.backend_finished(unit,'first',{'ActiveState':'inactive'}))

    def test_no_router_or_harness_monitor_can_be_closed(self):
        with patch.object(console.os,'kill') as kill:
            for unit in ['nvidia-model-router.service','nvidia-dsh.service','benchmark.service']:
                console.close_backend_monitor(unit)
            kill.assert_not_called()

    def test_reused_pid_or_other_project_viewer_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(console,'STATE',Path(directory)):
            unit='llm-test-qwen27b.service'
            (Path(directory)/(unit+'.json')).write_text(json.dumps({'pid':12345}))
            for command in [b'python\0/unrelated.py\0watch\0'+unit.encode(),
                            str(Path(console.__file__).resolve()).encode()+b'\0foreground\0'+unit.encode()]:
                with patch.object(Path,'read_bytes',return_value=command),patch.object(console.os,'kill') as kill:
                    console.close_backend_monitor(unit)
                    kill.assert_not_called()

    def test_only_registered_backend_viewer_gets_signal(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(console,'STATE',Path(directory)):
            unit='llm-test-qwen27b.service'
            (Path(directory)/(unit+'.json')).write_text(json.dumps({'pid':12345}))
            command=b'python\0'+str(Path(console.__file__).resolve()).encode()+b'\0watch\0--unit\0'+unit.encode()+b'\0'
            with patch.object(Path,'read_bytes',return_value=command),patch.object(Path,'exists',return_value=False),patch.object(console.os,'kill') as kill:
                console.close_backend_monitor(unit)
                kill.assert_called_once_with(12345,console.signal.SIGTERM)


class StopOwnership(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        for name,value in [('ROOT',self.root),('STATE',self.root/'data/router/worker.json')]:
            mocked=patch.object(workers,name,value);mocked.start();self.addCleanup(mocked.stop)
        self.worker=workers.Workers.__new__(workers.Workers);self.worker.active='qwen27b-sglang';self.worker.key='fixture'

    def properties(self,unit,name):
        if unit!=workers.DENSE_UNIT:return 'inactive'
        return {'ActiveState':'active','ExecStart':str(self.root/'scripts/supervise_dense.py')+' sglang',
                'InvocationID':'owned-invocation','ControlGroup':''}.get(name,'')

    def test_switch_stops_only_the_owned_worker_and_its_viewer(self):
        with patch.object(workers,'unit_property',side_effect=self.properties),patch.object(workers.subprocess,'run') as run,patch.object(workers,'close_backend_monitor') as close,patch.object(workers.subprocess,'check_output',return_value=''),patch.object(workers.socket,'socket') as socket:
            socket.return_value.__enter__.return_value.connect_ex.return_value=1
            self.worker.stop_owned()
            run.assert_called_once_with(['systemctl','--user','stop',workers.DENSE_UNIT],check=True,timeout=90)
            close.assert_called_once_with(workers.DENSE_UNIT)
            self.assertIsNone(self.worker.active)

    def test_replaced_worker_invocation_is_never_stopped(self):
        invocations=iter(['first','replacement'])
        def props(unit,name):return next(invocations) if unit==workers.DENSE_UNIT and name=='InvocationID' else self.properties(unit,name)
        with patch.object(workers,'unit_property',side_effect=props),patch.object(workers.subprocess,'run') as run,patch.object(workers,'close_backend_monitor') as close:
            with self.assertRaises(workers.RouterError) as error:self.worker.stop_owned()
            self.assertEqual(error.exception.code,'ownership_conflict');run.assert_not_called();close.assert_not_called()

    def test_idle_native_switch_stops_only_native_worker_and_viewer(self):
        import io
        self.worker.active='glm-maya'
        def props(unit,name):
            if unit!=workers.MOE_UNIT:return 'inactive'
            return {'ActiveState':'active','ExecStart':str(self.root/'scripts/serve_router_moe.py'),
                    'InvocationID':'native-owned','ControlGroup':''}.get(name,'')
        with patch.object(workers,'unit_property',side_effect=props),patch.object(workers.OPENER,'open',return_value=io.BytesIO(b'{"busy":false}')),patch.object(workers.subprocess,'run') as run,patch.object(workers,'close_backend_monitor') as close,patch.object(workers.subprocess,'check_output',return_value=''),patch.object(workers.socket,'socket') as socket:
            socket.return_value.__enter__.return_value.connect_ex.return_value=1
            self.worker.stop_owned()
            run.assert_called_once_with(['systemctl','--user','stop',workers.MOE_UNIT],check=True,timeout=90)
            close.assert_called_once_with(workers.MOE_UNIT)

    def test_harness_reservation_preserves_worker_and_viewer(self):
        (self.root/'data').mkdir();(self.root/'data/GPU-LOCK').write_text('{"owner":"experiment"}')
        with patch.object(workers.subprocess,'run') as run,patch.object(workers,'close_backend_monitor') as close:
            with self.assertRaises(workers.RouterError):self.worker.stop_owned()
            run.assert_not_called();close.assert_not_called()


if __name__=='__main__':unittest.main()
