"""Super must share vLLM busy detection while retaining its own bounded I/O policy."""
import sys,unittest,io,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'network'),str(ROOT/'scripts')]
import worker_manager as manager
from inference_swap_guard import WorkerWatch,TelemetryError
class SuperState(unittest.TestCase):
 def test_scoped_policy_and_phase_detection(self):
  w=WorkerWatch('/fixture','super-vllm','fixture');self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.pressure_limit),(64,96,10))
  bolt=WorkerWatch('/fixture','bolt-vllm','fixture');self.assertEqual((bolt.guard.write_limit,bolt.guard.combined_limit),(1,8))
  for gauge,phase in [('vllm:num_requests_running 1','inference'),('vllm:num_requests_running 0','idle')]:
   with patch.object(w,'get',return_value=gauge) as get:self.assertEqual(w.phase(),phase);get.assert_called_with('/metrics')
  with patch.object(w,'get',return_value='unknown 0'),self.assertRaises(TelemetryError):w.phase()
 def test_busy_and_unknown_preserve_exact_owned_unit(self):
  for metrics in ['vllm:num_requests_running 1\nvllm:num_requests_waiting 0','vllm:num_requests_running 0\nvllm:num_requests_waiting 1','']:
   with self.subTest(metrics=metrics),tempfile.TemporaryDirectory() as d:
    r=Path(d);w=manager.Workers.__new__(manager.Workers);w.active='super-vllm';w.key='fixture'
    def prop(unit,name):
     if unit!=manager.MOE_UNIT:return 'inactive'
     return {'ActiveState':'active','ExecStart':str(r/'scripts/serve_router_moe.py'),'InvocationID':'owned-fixture','ControlGroup':''}.get(name,'')
    with patch.object(manager,'ROOT',r),patch.object(manager,'STATE',r/'state.json'),patch.object(manager,'unit_property',side_effect=prop),patch.object(manager.OPENER,'open',return_value=io.BytesIO(metrics.encode())),patch.object(manager.subprocess,'run') as stop:
     with self.assertRaises(manager.RouterError):w.stop_owned()
     stop.assert_not_called();self.assertEqual(w.active,'super-vllm')
if __name__=='__main__':unittest.main()
