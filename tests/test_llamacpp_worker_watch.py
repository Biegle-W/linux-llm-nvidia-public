import io,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'network')]
from inference_swap_guard import llama_requests_busy,TelemetryError,WorkerWatch
from profile_catalog import get_profile,worker_budget
import llamacpp_worker as worker
import worker_manager as m
class LlamaCppWorkerWatch(unittest.TestCase):
 def test_native_busy_gauges_require_complete_finite_telemetry(self):
  for a,b,expect in [(0,0,False),(1,0,True),(0,1,True)]:self.assertEqual(llama_requests_busy(f'llamacpp:requests_processing {a}\nllamacpp:requests_deferred {b}\n'),expect)
  for text in ['', 'llamacpp:requests_processing 0','llamacpp:requests_processing nan\nllamacpp:requests_deferred 0','llamacpp:requests_processing 0\nllamacpp:requests_deferred -1','x'*(2*1024*1024+1)]:
   with self.subTest(text=text[:60]),self.assertRaises((ValueError,TelemetryError)):llama_requests_busy(text)
 def test_selected_budget_and_watch_are_scoped(self):
  for retired in ('flash-next-iq1m-strata','flash-next-iq1s-llamacpp'):
   with self.assertRaises(ValueError):get_profile(retired)
  p=get_profile('kolibri-llamacpp');self.assertEqual(worker_budget(p),{'high':87.76984786987305,'max':89.76984786987305,'swap':None})
  w=WorkerWatch('/unused','kolibri-llamacpp','fixture',latch=False)
  self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.pressure_limit),(1,8,10))
  with patch.object(w,'get',return_value='llamacpp:requests_processing 0\nllamacpp:requests_deferred 1'):self.assertEqual(w.phase(),'inference')
  with patch.object(w,'get',return_value='vllm:num_requests_running 0'):
   with self.assertRaises(TelemetryError):w.phase()
 def test_busy_or_unknown_owned_worker_is_preserved_on_unload(self):
  for text,code in [('llamacpp:requests_processing 1\nllamacpp:requests_deferred 0','backend_busy'),('', 'backend_state_unknown')]:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);w=m.Workers.__new__(m.Workers);w.active='kolibri-llamacpp';w.key='fixture'
    def prop(unit,key):
     if unit!=m.MOE_UNIT:return 'inactive'
     return {'ActiveState':'active','ExecStart':str(root/'scripts/serve_router_moe.py'),'InvocationID':'owned'}.get(key,'')
    with patch.object(m,'ROOT',root),patch.object(m,'unit_property',side_effect=prop),patch.object(m.OPENER,'open',return_value=io.BytesIO(text.encode())),patch.object(m.subprocess,'run') as stop:
     with self.assertRaises(m.RouterError) as e:w.stop_owned()
     self.assertEqual(e.exception.code,code);stop.assert_not_called()
 def test_native_request_queue_blocks_idle(self):
  w=WorkerWatch('/unused','kolibri-llamacpp','fake',latch=False)
  for running,queued,phase in [(0,0,'idle'),(1,0,'inference'),(0,1,'inference')]:
   with patch.object(w,'get',return_value=f'llamacpp:requests_processing {running}\nllamacpp:requests_deferred {queued}\n'):self.assertEqual(w.phase(),phase)
  with patch.object(w,'get',side_effect=OSError):
   with self.assertRaises(TelemetryError):w.phase()
 def test_invalid_telemetry_fails_closed(self):
  w=WorkerWatch('/unused','kolibri-llamacpp','fake',latch=False)
  for text in ['', 'llamacpp:requests_processing NaN\nllamacpp:requests_deferred 0\n','llamacpp:requests_processing 0\nllamacpp:requests_deferred -1\n']:
   with patch.object(w,'get',return_value=text),self.assertRaises(TelemetryError):w.phase()
 def test_native_swap_pressure_policy(self):
  w=WorkerWatch('/unused','kolibri-llamacpp','fake',latch=False)
  self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.window_s,w.guard.pressure_limit,w.guard.bad_samples),(1,8,30,10,3))
 def test_non_utf8_model_log_keeps_strict_placement_checks(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'engine.log';p.write_bytes(b'token: \xc4\xff\nCUDA0 model buffer size = 10000 MiB\nCUDA1 model buffer size = 8000 MiB\nn_ctx = 32768\n')
   self.assertTrue(worker.native_placement_proof(p,32768))
   self.assertFalse(worker.native_placement_proof(p,4096))
   p.write_bytes(b'CUDA0 model buffer size = 10000 MiB\nn_ctx = 32768\n')
   self.assertFalse(worker.native_placement_proof(p,32768))

 def test_key_permissions_and_empty_keys_fail_before_launch(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'key';p.write_text('fixture');p.chmod(0o600)
   self.assertEqual(worker.read_private_key(p),'fixture')
   p.chmod(0o644)
   with self.assertRaises(RuntimeError):worker.read_private_key(p)
   p.chmod(0o600);p.write_text('  ')
   with self.assertRaises(RuntimeError):worker.read_private_key(p)
if __name__=='__main__':unittest.main()
