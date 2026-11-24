import sys,unittest
from pathlib import Path
from unittest.mock import patch
import io,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'network'),str(ROOT/'scripts')]
import worker_manager as manager
from worker_manager import vllm_requests_busy
class RequestState(unittest.TestCase):
 def test_running_or_queued_blocks_unloading(self):
  for a,b in [(1,0),(0,1),(1,1)]:self.assertTrue(vllm_requests_busy(f'vllm:num_requests_running {a}\nvllm:num_requests_waiting {b}'))
  self.assertFalse(vllm_requests_busy('vllm:num_requests_running 0\nvllm:num_requests_waiting 0'))
 def test_unknown_gauges_cannot_claim_idle(self):
  for t in ['', 'vllm:num_requests_running 0','vllm:num_requests_running nan\nvllm:num_requests_waiting 0','vllm:num_requests_running -1\nvllm:num_requests_waiting 0']:
   with self.assertRaises(ValueError):vllm_requests_busy(t)
class ManagedUnload(unittest.TestCase):
 def test_hy4_native_unload_without_loading_field(self):
  for status,code in [('{"busy":true,"queued":0}', 'backend_busy'), ('{"busy":false,"queued":1}', 'backend_busy'),
                      ('{"busy":false,"queued":0}', None), ('{"queued":0}', 'backend_state_unknown')]:
   for profile in ('inkling-strata', 'hy4-flash-strata', 'hy4-flash-maya'):
    with self.subTest(profile=profile,status=status):self.exercise_one(profile,status,code,False,'/status')
 def exercise_one(self,profile,metrics,error_code,unavailable,endpoint='/metrics'):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);w=manager.Workers.__new__(manager.Workers);w.active=profile;w.key='fixture'
   def prop(unit,name):
    if unit!=manager.MOE_UNIT:return 'inactive'
    return {'ActiveState':'active','ExecStart':str(root/'scripts/serve_router_moe.py'),'InvocationID':'owned-fixture','ControlGroup':''}.get(name,'')
   response=io.BytesIO(metrics.encode())
   with patch.object(manager,'ROOT',root),patch.object(manager,'STATE',root/'state.json'),patch.object(manager,'unit_property',side_effect=prop),patch.object(manager.OPENER,'open',side_effect=OSError('unavailable') if unavailable else None,return_value=response) as api,patch.object(manager.subprocess,'run') as stop,patch.object(manager,'close_backend_monitor'),patch.object(manager.subprocess,'check_output',return_value=''),patch.object(manager.socket,'socket') as socket:
    socket.return_value.__enter__.return_value.connect_ex.return_value=1
    if error_code:
     with self.assertRaises(manager.RouterError) as caught:w.stop_owned()
     self.assertEqual(caught.exception.code,error_code);stop.assert_not_called();self.assertEqual(w.active,profile)
    else:
     w.stop_owned();stop.assert_called_once_with(['systemctl','--user','stop',manager.MOE_UNIT],check=True,timeout=90);self.assertIsNone(w.active)
    req=api.call_args.args[0];self.assertTrue(req.full_url.endswith(endpoint));self.assertEqual(req.get_header('Authorization'),'Bearer fixture')
 def test_unknown_request_state_preserves_owned_worker(self):
  self.exercise_one('inkling-strata','','backend_state_unknown',True,'/status')
if __name__=='__main__':unittest.main()
