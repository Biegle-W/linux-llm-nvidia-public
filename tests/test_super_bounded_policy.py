import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inference_swap_guard import WorkerWatch,PAGE_BYTES,MIB
class SuperPolicy(unittest.TestCase):
 def guard(self):return WorkerWatch('/unused','super-vllm','fixture').guard
 def rates(self,g,read,write):
  g.sample(0,'inference',0,0,0)
  return g.sample(30,'inference',int(read*30*MIB/PAGE_BYTES),int(write*30*MIB/PAGE_BYTES),0)
 def test_recorded_window_allowed(self):self.assertIsNone(self.rates(self.guard(),51.46,56.12))
 def test_write_and_combined_remain_bounded(self):
  self.assertIsNotNone(self.rates(self.guard(),0,81))
  self.assertIsNotNone(self.rates(self.guard(),74,56))
 def test_pressure_remains_independent(self):
  g=self.guard();g.sample(0,'inference',0,0,0)
  for t in [30,31]:self.assertIsNone(g.sample(t,'inference',0,0,11))
  self.assertIsNotNone(g.sample(32,'inference',0,0,11))
 def test_dense_policy_not_relaxed(self):
  g=WorkerWatch('/unused','qwen27b-hyperqwen','fixture').guard
  self.assertEqual((g.write_limit,g.combined_limit),(1,8))
if __name__=='__main__':unittest.main()
