import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from context_capacity import require_sglang_context,require_p2p_transport
class ContextCapacity(unittest.TestCase):
 def test_actual_pool_backs_selected_context(self):
  self.assertEqual(require_sglang_context(40960,'KV Cache is allocated. dtype: bf16, #tokens: 48000\nmax_total_num_tokens=47000'),47000)
 def test_short_call_success_does_not_prove_full_advertised_capacity(self):
  with self.assertRaises(ValueError):require_sglang_context(49152,'max_total_num_tokens=14915, context_len=49152')
 def test_missing_native_capacity_fails_closed(self):
  with self.assertRaises(ValueError):require_sglang_context(32768,'Server ready')

class TransportEvidence(unittest.TestCase):
 def test_bidirectional_native_transport(self):
  log='NCCL INFO Channel00 :0[0] -> 1[1] via P2P/CUMEM\nNCCL INFO Channel00 :1[1] -> 0[0] via P2P/IPC'
  self.assertEqual(require_p2p_transport(log),[(0,1),(1,0)])
 def test_flags_or_shm_or_one_direction_do_not_prove_p2p(self):
  for log in ['NCCL_P2P_DISABLE=0','0[0] -> 1[1] via SHM/direct','0[0] -> 1[1] via P2P/CUMEM']:
   with self.assertRaises(ValueError):require_p2p_transport(log)

class LazyTransport(unittest.TestCase):
 def test_idle_lazy_communicator_is_not_a_fallback(self):
  from context_capacity import check_p2p_progress
  self.assertEqual(check_p2p_progress('', 'idle',100,allow_lazy=True),(False,None,None))
 def test_missing_transport_after_real_traffic_times_out(self):
  from context_capacity import check_p2p_progress
  self.assertEqual(check_p2p_progress('Prefill batch', 'idle',100,allow_lazy=True),(False,100,None))
  self.assertIsNotNone(check_p2p_progress('Prefill batch','idle',131,100,True)[2])
 def test_real_transport_finishes_the_pending_check(self):
  from context_capacity import check_p2p_progress
  log='0[0] -> 1[1] via P2P/CUMEM\n1[1] -> 0[0] via P2P/IPC'
  self.assertEqual(check_p2p_progress(log,'idle',101,100,True),(True,None,None))
 def test_nonlazy_engine_requires_evidence_at_readiness(self):
  from context_capacity import check_p2p_progress
  self.assertIsNotNone(check_p2p_progress('', 'idle',100)[2])

class HostStagedTransport(unittest.TestCase):
 def log(self):return 'NCCL_P2P_DISABLE set by environment to 1\n0[0] -> 1[1] via SHM/direct/direct\n1[1] -> 0[0] via SHM/direct/direct'
 def test_bidirectional_shm_with_p2p_disabled(self):
  from context_capacity import require_runtime_transport
  self.assertEqual(require_runtime_transport(self.log(),'host-staged'),[(0,1),(1,0)])
 def test_flags_alone_missing_direction_or_peer_channel_fail(self):
  from context_capacity import require_runtime_transport
  for log in ['NCCL_P2P_DISABLE set by environment to 1',self.log().split('1[1] ->')[0],self.log()+'\n0[0] -> 1[1] via P2P/IPC',self.log().replace('environment to 1','environment to 0')]:
   with self.assertRaises(ValueError):require_runtime_transport(log,'host-staged')
 def test_progress_uses_selected_mode(self):
  from context_capacity import check_p2p_progress
  self.assertEqual(check_p2p_progress(self.log(),'idle',100,mode='host-staged'),(True,None,None))

 def test_host_channel_logging_gets_bounded_startup_grace(self):
  from context_capacity import check_p2p_progress
  self.assertEqual(check_p2p_progress('NCCL_P2P_DISABLE set by environment to 1','idle',100,mode='host-staged'),(False,100,None))
  self.assertIsNotNone(check_p2p_progress('', 'idle',131,100,mode='host-staged')[2])
 def test_actual_peer_channel_is_never_graced(self):
  from context_capacity import check_p2p_progress
  self.assertIsNotNone(check_p2p_progress(self.log()+'\n0[0] -> 1[1] via P2P/IPC','idle',100,mode='host-staged')[2])
