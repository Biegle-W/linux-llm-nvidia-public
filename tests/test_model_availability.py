import sys,unittest,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'network'),str(ROOT/'dsh')]
from profile_catalog import profile_enabled,require_enabled,get_profile
import worker_manager
import configure
class Availability(unittest.TestCase):
 def test_existing_profiles_default_to_available(self):self.assertTrue(profile_enabled({}))
 def test_disabled_launch_rejected_with_reason(self):
  p={'id':'ram-model','availability':{'enabled':False,'reason':'awaiting RAM upgrade'}}
  with self.assertRaisesRegex(ValueError,'awaiting RAM upgrade'):require_enabled(p)
 def test_invalid_policy_rejected(self):
  for value in [None,{}, {'enabled':1},{'enabled':'false'}]:
   with self.assertRaises(ValueError):profile_enabled({'availability':value})
 def test_router_excludes_disabled_before_selection(self):
  ps=[{'id':'on','availability':{'enabled':True}},{'id':'off','availability':{'enabled':False}}]
  with patch.object(worker_manager,'load_catalog',return_value={'profiles':ps}):self.assertEqual(list(worker_manager.profiles()),['on'])
 def test_dsh_removes_saved_disabled_model_but_keeps_definition(self):
  enabled=copy.deepcopy(get_profile('qwen27b-hyperqwen'));disabled=copy.deepcopy(get_profile('glm-maya'))
  enabled['availability']={'enabled':True};disabled['availability']={'enabled':False}
  old={configure.ROUTER_ID:{'baseURL':configure.ROUTER_URL,'models':[{'id':enabled['id']},{'id':disabled['id']}]}}
  result=configure.router_providers(old,[enabled,disabled])
  self.assertEqual([m['id'] for m in result[configure.ROUTER_ID]['models']],[enabled['id']])
  self.assertEqual(disabled['id'],'glm-maya')
if __name__=='__main__':unittest.main()
