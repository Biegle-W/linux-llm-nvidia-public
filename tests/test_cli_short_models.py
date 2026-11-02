import sys,unittest
from pathlib import Path
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cli_short_models as runner
class ForegroundCLI(unittest.TestCase):
 def test_inaccessible_bus_fails_closed(self):
  with patch.object(runner.subprocess,'run',return_value=Mock(returncode=1,stdout='')):
   with self.assertRaisesRegex(RuntimeError,'service bus'):runner.inactive()
 def test_empty_state_is_unknown_not_idle(self):
  with patch.object(runner.subprocess,'run',return_value=Mock(returncode=0,stdout='')):
   with self.assertRaisesRegex(RuntimeError,'Unknown worker state'):runner.inactive()
 def test_live_or_stopping_worker_is_not_inactive(self):
  for state in ['active','activating','deactivating']:
   with self.subTest(state=state),patch.object(runner,'property_of',return_value=state):self.assertFalse(runner.inactive())
 def test_nonterminal_launch_does_not_reach_model_preflight(self):
  with patch.object(sys,'argv',['cli_short_models.py']),patch.object(sys.stdin,'isatty',return_value=False),patch.object(runner,'load_catalog') as catalog:
   with self.assertRaisesRegex(RuntimeError,'foreground terminal'):runner.main()
   catalog.assert_not_called()
if __name__=='__main__':unittest.main()
