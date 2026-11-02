import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inference_swap_guard import dense_gpu_free_mib
class Floor(unittest.TestCase):
 def test_allowance_is_scoped_to_maintained_sglang(self):
  self.assertEqual(dense_gpu_free_mib('qwen27b-sglang'),448)
  for profile in ['qwen27b-hyperqwen','unknown','qwen27b-sglang-trial']:
   self.assertEqual(dense_gpu_free_mib(profile),512)
if __name__=='__main__':unittest.main()
