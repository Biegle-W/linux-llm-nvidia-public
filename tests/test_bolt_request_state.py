import sys,unittest
from pathlib import Path
from unittest.mock import patch
import io,tempfile
import worker_manager as manager
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'network'),str(ROOT/'scripts')]
from worker_manager import vllm_requests_busy
from inference_swap_guard import WorkerWatch,TelemetryError
class RequestState(unittest.TestCase):
 def test_running_or_queued_blocks_unloading(self):
  for a,b in [(1,0),(0,1),(1,1)]:self.assertTrue(vllm_requests_busy(f'vllm:num_requests_running {a}\nvllm:num_requests_waiting {b}'))
  self.assertFalse(vllm_requests_busy('vllm:num_requests_running 0\nvllm:num_requests_waiting 0'))
 def test_unknown_gauges_cannot_claim_idle(self):
  for t in ['', 'vllm:num_requests_running 0','vllm:num_requests_running nan\nvllm:num_requests_waiting 0','vllm:num_requests_running -1\nvllm:num_requests_waiting 0']:
   with self.assertRaises(ValueError):vllm_requests_busy(t)
 def test_bolt_vllm_phase_and_strict_defaults(self):
  w=WorkerWatch('/fixture','bolt-vllm','fixture');self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.pressure_limit),(1,8,10))
  with patch.object(w,'get',return_value='vllm:num_requests_running 1') as get:self.assertEqual(w.phase(),'inference');get.assert_called_with('/metrics')
  with patch.object(w,'get',return_value='vllm:num_requests_running 0'):self.assertEqual(w.phase(),'idle')
 def test_missing_phase_gauge_fails_closed(self):
  w=WorkerWatch('/fixture','bolt-vllm','fixture')
  with patch.object(w,'get',return_value='unrelated 0'):
   with self.assertRaises(TelemetryError):w.phase()
class ManagedUnload(unittest.TestCase):
 def exercise(self,metrics,error_code=None,unavailable=False):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);w=manager.Workers.__new__(manager.Workers);w.active='bolt-vllm';w.key='fixture'
   def prop(unit,name):
    if unit!=manager.MOE_UNIT:return 'inactive'
    return {'ActiveState':'active','ExecStart':str(root/'scripts/serve_router_moe.py'),'InvocationID':'owned-fixture','ControlGroup':''}.get(name,'')
   response=io.BytesIO(metrics.encode())
   with patch.object(manager,'ROOT',root),patch.object(manager,'STATE',root/'state.json'),patch.object(manager,'unit_property',side_effect=prop),patch.object(manager.OPENER,'open',side_effect=OSError('unavailable') if unavailable else None,return_value=response) as api,patch.object(manager.subprocess,'run') as stop,patch.object(manager,'close_backend_monitor'),patch.object(manager.subprocess,'check_output',return_value=''),patch.object(manager.socket,'socket') as socket:
    socket.return_value.__enter__.return_value.connect_ex.return_value=1
    if error_code:
     with self.assertRaises(manager.RouterError) as caught:w.stop_owned()
     self.assertEqual(caught.exception.code,error_code);stop.assert_not_called();self.assertEqual(w.active,'bolt-vllm')
    else:
     w.stop_owned();stop.assert_called_once_with(['systemctl','--user','stop',manager.MOE_UNIT],check=True,timeout=90);self.assertIsNone(w.active)
    req=api.call_args.args[0];self.assertTrue(req.full_url.endswith('/metrics'));self.assertEqual(req.get_header('Authorization'),'Bearer fixture')
 def test_running_and_waiting_requests_preserve_owned_worker(self):
  for a,b in [(1,0),(0,1)]:
   with self.subTest(running=a,waiting=b):self.exercise(f'vllm:num_requests_running {a}\nvllm:num_requests_waiting {b}',error_code='backend_busy')
 def test_unknown_request_state_preserves_owned_worker(self):
  self.exercise('',error_code='backend_state_unknown');self.exercise('',error_code='backend_state_unknown',unavailable=True)
 def test_confirmed_idle_stops_only_owned_unit(self):
  self.exercise('vllm:num_requests_running 0\nvllm:num_requests_waiting 0')
if __name__=='__main__':unittest.main()
