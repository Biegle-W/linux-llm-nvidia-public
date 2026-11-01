import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from serve_qwen27b_engines import wait_for_gpu_memory
class Settle(unittest.TestCase):
 def setUp(self):self.now=0;self.p={'startup_gpu_free_mib':[9728,8960]}
 def clock(self):return self.now
 def sleep(self,n):self.now+=n
 def raw(self,free):return f'NVIDIA GeForce RTX 3080 Ti, 11949\nNVIDIA GeForce RTX 3080, {free}\n'
 def test_released_memory_allows_start(self):
  with patch('serve_qwen27b_engines.subprocess.check_output',side_effect=[self.raw(8800),self.raw(9027)]):wait_for_gpu_memory(self.p,clock=self.clock,sleep=self.sleep)
  self.assertEqual(self.now,1)
 def test_persistent_shortage_reports_actual_without_relaxation(self):
  with patch('serve_qwen27b_engines.subprocess.check_output',return_value=self.raw(8800)),self.assertRaisesRegex(SystemExit,'8800 MiB free, 8960 MiB required'):wait_for_gpu_memory(self.p,timeout=2,clock=self.clock,sleep=self.sleep)
  self.assertEqual(self.now,2)
 def test_identity_mismatch_does_not_wait(self):
  with patch('serve_qwen27b_engines.subprocess.check_output',return_value=self.raw(9999).replace('RTX 3080,','RTX 3060,')),self.assertRaisesRegex(SystemExit,'identity changed'):wait_for_gpu_memory(self.p,clock=self.clock,sleep=self.sleep)
  self.assertEqual(self.now,0)
if __name__ == '__main__':
 unittest.main()
