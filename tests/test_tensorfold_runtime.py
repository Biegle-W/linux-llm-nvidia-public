import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from profile_catalog import get_profile
from tensorfold_runtime import command,require_admission
from inference_swap_guard import WorkerWatch
class TensorFoldTests(unittest.TestCase):
 def test_launch_is_pinned_to_qualified_capacity_and_device(self):
  p=get_profile('qwen27b-tensorfold');a=command(p)
  self.assertEqual(a[a.index('--context')+1],'12288');self.assertEqual(a[a.index('--device')+1],'0')
  self.assertEqual(a[a.index('--drafter-bits')+1],'4');self.assertNotIn('--reserve-gib',a)
  with self.assertRaises(ValueError):command(dict(p,allocated_context=16384))
 def test_actual_admission_evidence_required(self):
  proof='CUDA sm_86 device 0 (NVIDIA GeForce RTX 3080 Ti) 1 stream at once 12288-token window 1.0 GiB reserve drafts: DFlash2 + copies; context: 12288;'
  require_admission(proof)
  for piece in ('device 0','1.0 GiB reserve','+ copies'):
   with self.assertRaises(ValueError):require_admission(proof.replace(piece,''))
 def test_native_busy_gauge_and_missing_telemetry(self):
  w=WorkerWatch('/unused','qwen27b-tensorfold','test',latch=False)
  for n,phase in [(0,'idle'),(1,'inference')]:
   with patch.object(w,'get',return_value='tensorfold:num_requests_running '+str(n)):
    self.assertEqual(w.phase(),phase)
  with patch.object(w,'get',return_value='vllm:num_requests_running 0'):
   with self.assertRaises(Exception):w.phase()
  self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.window_s,w.guard.pressure_limit,w.guard.bad_samples),(1,8,30,10,3))
if __name__=='__main__':unittest.main()
