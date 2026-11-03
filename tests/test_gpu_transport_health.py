import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gpu_transport_health import check_identity, trusted_json
from unittest.mock import Mock
from types import SimpleNamespace

class Transport(unittest.TestCase):
 def row(self):return dict(mode='host-staged',passed=True,boot_id='boot',nvidia_srcversion='stock',peer_access=[0,0])
 def test_current_boot_disabled_peers(self):self.assertTrue(check_identity(self.row(),'boot','stock')['passed'])
 def test_stale_failed_or_peer_enabled_refused(self):
  for delta in [dict(mode='p2p'),dict(passed=False),dict(boot_id='old'),dict(nvidia_srcversion='old'),dict(peer_access=[1,0]),dict(peer_access=[0,1])]:
   with self.subTest(delta=delta),self.assertRaises(ValueError):check_identity(self.row()|delta,'boot','stock')
 def test_untrusted_ownership_and_write_permissions(self):
  for uid,mode in [(1000,0o644),(0,0o664),(0,0o666)]:
   p=Mock();p.stat.return_value=SimpleNamespace(st_uid=uid,st_mode=mode)
   with self.assertRaises(ValueError):trusted_json(p)

if __name__=='__main__':unittest.main()
