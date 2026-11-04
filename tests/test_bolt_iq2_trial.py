import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import bolt_iq2_worker as worker
from inference_swap_guard import TelemetryError
class NativeBoltGuards(unittest.TestCase):
 def test_native_request_queue_blocks_idle(self):
  w=worker.BoltWatch('/unused','bolt-vllm','fake',latch=False)
  for running,queued,phase in [(0,0,'idle'),(1,0,'inference'),(0,1,'inference')]:
   with patch.object(w,'get',return_value=f'llamacpp:requests_processing {running}\nllamacpp:requests_deferred {queued}\n'):self.assertEqual(w.phase(),phase)
  with patch.object(w,'get',side_effect=OSError):
   with self.assertRaises(TelemetryError):w.phase()
 def test_invalid_telemetry_fails_closed(self):
  w=worker.BoltWatch('/unused','bolt-vllm','fake',latch=False)
  for text in ['', 'llamacpp:requests_processing NaN\nllamacpp:requests_deferred 0\n','llamacpp:requests_processing 0\nllamacpp:requests_deferred -1\n']:
   with patch.object(w,'get',return_value=text),self.assertRaises(TelemetryError):w.phase()
 def test_awq_swap_pressure_policy_retained(self):
  w=worker.BoltWatch('/unused','bolt-vllm','fake',latch=False)
  self.assertEqual((w.guard.write_limit,w.guard.combined_limit,w.guard.window_s,w.guard.pressure_limit,w.guard.bad_samples),(1,8,30,10,3))
 def test_fit_can_offload_without_lowering_context(self):
  p={'binary':'runtime/llama-server','checkpoint_directory':'models/bolt','first_shard':'bolt.gguf','planned_context':163840,'fit_target_MiB':[512,512]};cmd=worker.build_command(p)
  for flag in ['--ctx-size','--fit-ctx']:self.assertEqual(cmd[cmd.index(flag)+1],'163840')
  self.assertEqual(cmd[cmd.index('--fit-target')+1],'512,512')
  for flag in ['--cpu-moe','--n-cpu-moe','--gpu-layers','-ngl','--mmproj']:self.assertNotIn(flag,cmd)
  p['fit_target_MiB']=[256,256];self.assertEqual(worker.build_command(p)[worker.build_command(p).index('--fit-target')+1],'256,256')
  p['fit_target_MiB']=[384,384];self.assertEqual(worker.build_command(p)[worker.build_command(p).index('--fit-target')+1],'384,384')
  p['fit_target_MiB']=[128,128]
  with self.assertRaises(ValueError):worker.build_command(p)
  p['fit_target_MiB']=[512,512]
  p['planned_context']=4096
  with self.assertRaises(ValueError):worker.build_command(p)

 def test_non_utf8_model_log_keeps_strict_placement_checks(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'engine.log';p.write_bytes(b'token: \xc4\xff\nCUDA0 model buffer size = 10000 MiB\nCUDA1 model buffer size = 8000 MiB\nn_ctx = 163840\n')
   self.assertTrue(worker.native_placement_proof(p,163840))
   self.assertFalse(worker.native_placement_proof(p,4096))
   p.write_bytes(b'CUDA0 model buffer size = 10000 MiB\nn_ctx = 163840\n')
   self.assertFalse(worker.native_placement_proof(p,163840))
