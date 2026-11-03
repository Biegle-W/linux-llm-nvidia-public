import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inference_swap_guard import dense_gpu_free_mib
class Floor(unittest.TestCase):
 def test_headless_floor_is_shared(self):
  self.assertEqual(dense_gpu_free_mib('qwen27b-sglang'),256)
  for profile in ['qwen27b-hyperqwen','unknown','qwen27b-sglang-trial','bolt-vllm','deepseek-unsloth-strata']:
   self.assertEqual(dense_gpu_free_mib(profile),256)
if __name__=='__main__':unittest.main()
