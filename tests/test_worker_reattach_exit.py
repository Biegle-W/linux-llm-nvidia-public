import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch,Mock
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'network'),str(Path(__file__).resolve().parents[1]/'scripts')]
import worker_manager as m
class Reattach(unittest.TestCase):
 def test_stopped_worker_with_cleared_invocation_is_launch_failure(self):
  w=m.Workers.__new__(m.Workers);w.timeout=2;w.loading=None;ids=iter(['owned',''])
  with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.object(m,'unit_property',side_effect=lambda unit,key:next(ids) if key=='InvocationID' else 'inactive'),patch.object(m.subprocess,'run') as command:
   with self.assertRaises(m.RouterError) as result:w.wait_existing_start('qwen27b-hyperqwen',lambda:None)
   self.assertEqual(result.exception.code,'launch_failed');command.assert_not_called();self.assertIsNone(w.loading)
 def test_live_replacement_is_preserved(self):
  w=m.Workers.__new__(m.Workers);w.timeout=2;w.loading=None;ids=iter(['owned','replacement'])
  with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.object(m,'unit_property',side_effect=lambda unit,key:next(ids) if key=='InvocationID' else 'active'),patch.object(m.subprocess,'run') as command:
   with self.assertRaises(m.RouterError) as result:w.wait_existing_start('qwen27b-hyperqwen',lambda:None)
   self.assertEqual(result.exception.code,'ownership_conflict');command.assert_not_called();self.assertIsNone(w.loading)
if __name__=='__main__':unittest.main()
