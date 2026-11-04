import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'dsh')]
import bolt_iq2_runtime as runtime
from bolt_iq2_worker import build_command
from profile_catalog import get_profile
import configure
class MaintainedBoltIQ2(unittest.TestCase):
 def setUp(self):
  self.profile=get_profile('bolt-vllm');self.manifest=json.loads((ROOT/'config/bolt-iq2-runtime.json').read_text())
 def test_only_qualified_minimum_setting_can_start(self):
  runtime.verify(self.profile,self.manifest)
  for fit in [[256,256],[512,512]]:
   bad=copy.deepcopy(self.manifest);bad['fit_target_MiB']=fit
   with self.assertRaises(ValueError):runtime.verify(self.profile,bad)
 def test_wrong_quant_or_context_refused(self):
  for key,value in [('weight_quant','AWQ-INT4'),('allocated_context',8192),('engine','vLLM-offload')]:
   bad=copy.deepcopy(self.profile);bad[key]=value
   with self.assertRaises(ValueError):runtime.verify(bad,self.manifest)
 def test_managed_port_and_alias_are_explicit(self):
  cmd=build_command(self.manifest,port=10000,alias='bolt')
  self.assertEqual(cmd[cmd.index('--port')+1],'10000');self.assertEqual(cmd[cmd.index('--alias')+1],'bolt')
  self.assertEqual(cmd[cmd.index('--fit-target')+1],'384,384')
 def test_dsh_saved_awq_name_is_replaced_without_losing_other_routes(self):
  providers={'nvidia-strata':{'baseURL':configure.ROUTER_URL,'models':[{'id':'bolt-vllm','name':'Bolt AWQ old name'}]},'unrelated':{'baseURL':'http://example.invalid/v1','models':[{'id':'other','name':'Keep custom name'}]}}
  result=configure.router_providers(providers,[self.profile]);model=result['nvidia-strata']['models'][0]
  self.assertIn('native IQ2',model['name']);self.assertNotIn('AWQ',model['name']);self.assertEqual(model['id'],'bolt-vllm');self.assertEqual(result['unrelated'],providers['unrelated'])
if __name__=='__main__':unittest.main()
