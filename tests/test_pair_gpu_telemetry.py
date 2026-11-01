import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from serve_router_moe import pair_gpu_free_values
class PairTelemetry(unittest.TestCase):
 def test_permanent_pair(self):self.assertEqual(pair_gpu_free_values('1024\n2048\n'),[1024,2048])
 def test_missing_extra_and_invalid_values_fail_closed(self):
  for raw in ['1024','1024\n2048\n512','nan\n2048','-1\n2048']:
   with self.assertRaises(RuntimeError):pair_gpu_free_values(raw)
