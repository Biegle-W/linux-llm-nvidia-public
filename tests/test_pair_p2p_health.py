import json,unittest,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pair_p2p_health import require_verified_pair
class PairHealth(unittest.TestCase):
 def check(self,**changes):
  row={'passed':True,'boot_id':'boot','nvidia_srcversion':'module'};row.update(changes)
  report=Mock();report.stat.return_value=SimpleNamespace(st_uid=0,st_mode=0o100644);report.read_text.return_value=json.dumps(row)
  boot=Mock();boot.read_text.return_value='boot';module=Mock();module.read_text.return_value='module'
  return report,boot,module
 def test_current_boot_proof(self):self.assertTrue(require_verified_pair(*self.check())['passed'])
 def test_rejects_stale_boot_module_or_failure(self):
  for changes in [{'boot_id':'old'},{'nvidia_srcversion':'other'},{'passed':False}]:
   with self.assertRaises(RuntimeError):require_verified_pair(*self.check(**changes))
 def test_rejects_user_writable_or_owned_proof(self):
  for uid,mode in [(1000,0o100644),(0,0o100666)]:
   report,boot,module=self.check();report.stat.return_value=SimpleNamespace(st_uid=uid,st_mode=mode)
   with self.assertRaises(RuntimeError):require_verified_pair(report,boot,module)
