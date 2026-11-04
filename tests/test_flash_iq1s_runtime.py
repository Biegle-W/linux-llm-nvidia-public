import io,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'network')]
from inference_swap_guard import llama_requests_busy,TelemetryError,WorkerWatch
from profile_catalog import get_profile,worker_budget
import worker_manager as m
class FlashEntry(unittest.TestCase):
 def test_native_busy_gauges_require_complete_finite_telemetry(self):
  for a,b,expect in [(0,0,False),(1,0,True),(0,1,True)]:self.assertEqual(llama_requests_busy(f'llamacpp:requests_processing {a}\nllamacpp:requests_deferred {b}\n'),expect)
  for text in ['', 'llamacpp:requests_processing 0','llamacpp:requests_processing nan\nllamacpp:requests_deferred 0','llamacpp:requests_processing 0\nllamacpp:requests_deferred -1','x'*(2*1024*1024+1)]:
   with self.subTest(text=text[:60]),self.assertRaises((ValueError,TelemetryError)):llama_requests_busy(text)
 def test_selected_budget_and_watch_are_scoped(self):
  p=get_profile('flash-next-iq1s-llamacpp');self.assertEqual(worker_budget(p),{'high':87.76984786987305,'max':89.76984786987305,'swap':None});self.assertEqual(p['allocated_context'],12288)
  w=WorkerWatch('/unused',p['id'],'fixture',latch=False)
  self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.pressure_limit),(128,160,15))
  with patch.object(w,'get',return_value='llamacpp:requests_processing 0\nllamacpp:requests_deferred 1'):self.assertEqual(w.phase(),'inference')
  with patch.object(w,'get',return_value='vllm:num_requests_running 0'):
   with self.assertRaises(TelemetryError):w.phase()
 def test_busy_or_unknown_owned_worker_is_preserved_on_unload(self):
  for text,code in [('llamacpp:requests_processing 1\nllamacpp:requests_deferred 0','backend_busy'),('', 'backend_state_unknown')]:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);w=m.Workers.__new__(m.Workers);w.active='flash-next-iq1s-llamacpp';w.key='fixture'
    def prop(unit,key):
     if unit!=m.MOE_UNIT:return 'inactive'
     return {'ActiveState':'active','ExecStart':str(root/'scripts/serve_router_moe.py'),'InvocationID':'owned'}.get(key,'')
    with patch.object(m,'ROOT',root),patch.object(m,'unit_property',side_effect=prop),patch.object(m.OPENER,'open',return_value=io.BytesIO(text.encode())),patch.object(m.subprocess,'run') as stop:
     with self.assertRaises(m.RouterError) as e:w.stop_owned()
     self.assertEqual(e.exception.code,code);stop.assert_not_called()
if __name__=='__main__':unittest.main()
