import importlib.util,tempfile,unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dsh_registration',ROOT/'dsh/configure.py');registration=importlib.util.module_from_spec(spec);spec.loader.exec_module(registration)
class Registration(unittest.TestCase):
 def fixture(self,folder,profiles,entries):
  oldroot,oldcatalog=registration.ROOT,registration.load_catalog
  self.addCleanup(setattr,registration,'ROOT',oldroot);self.addCleanup(setattr,registration,'load_catalog',oldcatalog)
  registration.ROOT=Path(folder);registration.load_catalog=lambda:{'profiles':profiles}
  path=Path(folder)/'data/dsh/profiles/web/cordis.patch.yml';path.parent.mkdir(parents=True);path.write_text(yaml.safe_dump(entries));return path
 def test_preserves_custom_routes_aliases_and_selection(self):
  with tempfile.TemporaryDirectory() as folder:
   alias={'id':'custom-search','contextWindow':56320,'customField':'preserve'}
   custom={'displayName':'My models','baseURL':registration.ROUTER_URL,'apiKeyEnv':'CUSTOM_KEY_ENV','models':[{'id':'bolt-llamacpp','contextWindow':8192},alias]}
   selected={'provider':'existing','model':'custom-search'}
   path=self.fixture(folder,[{'id':'bolt-llamacpp','engine':'vLLM-offload','model':'Nemotron Bolt','allocated_context':65536},{'id':'flash-next-strata','engine':'vLLM-offload','model':'Flash Next','allocated_context':65536}],[{'id':'llm-pi-ai','config':{'providers':{'existing':custom}}},{'id':'agent-default-model','config':selected}])
   registration.configure('web');entries=yaml.safe_load(path.read_text());providers=entries[0]['config']['providers'];self.assertEqual(providers['existing']['models'],[alias]);self.assertEqual(providers['existing']['apiKeyEnv'],'CUSTOM_KEY_ENV');self.assertEqual(entries[1]['config'],selected)
   self.assertTrue(next(x for x in entries if x['id']=='session-title-llm')['disabled']);router=providers['nvidia-strata'];self.assertEqual(router['displayName'],'NVIDIA server');self.assertEqual(router['api'],'openai-completions');self.assertEqual([x['id'] for x in router['models']],['bolt-llamacpp','flash-next-strata']);self.assertTrue(all(m['maxTokens']==4096 and m['reasoningEfforts'] is False for m in router['models']))
   registration.configure('web');self.assertEqual(yaml.safe_load(path.read_text()),entries);self.assertEqual(path.stat().st_mode&0o777,0o600)
 def test_one_provider_search_alias_and_old_selection_migration(self):
  with tempfile.TemporaryDirectory() as folder:
   profiles=[{'id':'qwen27b-hyperqwen','engine':'HyperQwen-vLLM','model':'Qwen3.8-27B','allocated_context':56320},{'id':'bolt-llamacpp','engine':'vLLM-offload','model':'Bolt','allocated_context':65536}]
   providers={'nvidia-hyperqwen':{'baseURL':registration.ROUTER_URL,'models':[{'id':'qwen27b-hyperqwen'},{'id':'qwen27b-hyperqwen-search','customField':'keep'}]},'nvidia-vllm-offload':{'baseURL':registration.ROUTER_URL,'models':[{'id':'bolt-llamacpp'}]},'external':{'baseURL':'https://example.invalid/v1','models':[{'id':'remote'}]}}
   path=self.fixture(folder,profiles,[{'id':'llm-pi-ai','config':{'providers':providers}},{'id':'agent-default-model','config':{'provider':'nvidia-hyperqwen','model':'qwen27b-hyperqwen-search'}}]);registration.configure('web');entries=yaml.safe_load(path.read_text());actual=entries[0]['config']['providers'];self.assertEqual(set(actual),{'external','nvidia-strata'});self.assertEqual(actual['external'],providers['external']);models=actual['nvidia-strata']['models'];self.assertEqual([m['id'] for m in models],['qwen27b-hyperqwen','bolt-llamacpp']);self.assertEqual(models[0]['customField'],'keep');self.assertEqual(entries[1]['config'],{'provider':'nvidia-strata','model':'qwen27b-hyperqwen'})
   registration.configure('web');self.assertEqual(yaml.safe_load(path.read_text()),entries)
 def test_external_search_named_model_and_nested_provider_are_preserved(self):
  value={'provider':'external','model':registration.SEARCH,'nested':{'provider':{'id':'remote'},'model':registration.SEARCH}}
  self.assertEqual(registration.migrate_selection(value,routes={}),value)
 def test_saved_router_search_selection_migrates_to_plain(self):
  self.assertEqual(registration.migrate_selection({'provider':registration.ROUTER_ID,'model':registration.SEARCH},routes={}),{'provider':registration.ROUTER_ID,'model':registration.PLAIN})
 def test_retired_super_is_removed_and_saved_selection_migrates(self):
  profiles=[{'id':registration.PLAIN,'engine':'HyperQwen-vLLM','model':'Qwen','allocated_context':40960}]
  original={registration.ROUTER_ID:{'baseURL':registration.ROUTER_URL,'models':[{'id':'super-vllm'},{'id':'super-strata-trial'},{'id':'custom-local','customField':'keep'}]},'external':{'baseURL':'https://example.invalid/v1','models':[{'id':'super-vllm'}]}}
  actual=registration.router_providers(original,profiles)
  self.assertEqual([m['id'] for m in actual[registration.ROUTER_ID]['models']],['custom-local',registration.PLAIN])
  self.assertEqual(actual['external'],original['external'])
  self.assertEqual(registration.migrate_selection({'provider':registration.ROUTER_ID,'model':'super-vllm'},routes={}),{'provider':registration.ROUTER_ID,'model':registration.PLAIN})
  self.assertEqual(registration.migrate_selection({'provider':'external','model':'super-vllm'},routes={}),{'provider':'external','model':'super-vllm'})
if __name__=='__main__':unittest.main()
