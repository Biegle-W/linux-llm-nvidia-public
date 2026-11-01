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
   custom={'displayName':'My models','baseURL':registration.ROUTER_URL,'apiKeyEnv':'CUSTOM_KEY_ENV','models':[{'id':'bolt-vllm','contextWindow':8192},alias]}
   selected={'provider':'existing','model':'custom-search'}
   path=self.fixture(folder,[{'id':'bolt-vllm','engine':'vLLM-offload','model':'Nemotron Bolt','allocated_context':65536},{'id':'super-vllm','engine':'vLLM-offload','model':'Nemotron Super','allocated_context':65536}],[{'id':'llm-pi-ai','config':{'providers':{'existing':custom}}},{'id':'agent-default-model','config':selected}])
   registration.configure('web');entries=yaml.safe_load(path.read_text());providers=entries[0]['config']['providers'];self.assertEqual(providers['existing']['models'],[alias]);self.assertEqual(providers['existing']['apiKeyEnv'],'CUSTOM_KEY_ENV');self.assertEqual(entries[1]['config'],selected)
   router=providers['nvidia-strata'];self.assertEqual(router['displayName'],'NVIDIA Server Router');self.assertEqual(router['api'],'openai-completions');self.assertEqual([x['id'] for x in router['models']],['bolt-vllm','super-vllm']);self.assertTrue(all(m['maxTokens']==4096 and m['reasoningEfforts'] is False for m in router['models']))
   registration.configure('web');self.assertEqual(yaml.safe_load(path.read_text()),entries);self.assertEqual(path.stat().st_mode&0o777,0o600)
 def test_one_provider_search_alias_and_old_selection_migration(self):
  with tempfile.TemporaryDirectory() as folder:
   profiles=[{'id':'qwen27b-hyperqwen','engine':'HyperQwen-vLLM','model':'Qwen3.8-27B','allocated_context':56320},{'id':'bolt-vllm','engine':'vLLM-offload','model':'Bolt','allocated_context':65536}]
   providers={'nvidia-hyperqwen':{'baseURL':registration.ROUTER_URL,'models':[{'id':'qwen27b-hyperqwen'},{'id':'qwen27b-hyperqwen-search','customField':'keep'}]},'nvidia-vllm-offload':{'baseURL':registration.ROUTER_URL,'models':[{'id':'bolt-vllm'}]},'external':{'baseURL':'https://example.invalid/v1','models':[{'id':'remote'}]}}
   path=self.fixture(folder,profiles,[{'id':'llm-pi-ai','config':{'providers':providers}},{'id':'agent-default-model','config':{'provider':'nvidia-hyperqwen','model':'qwen27b-hyperqwen'}}]);registration.configure('web');entries=yaml.safe_load(path.read_text());actual=entries[0]['config']['providers'];self.assertEqual(set(actual),{'external','nvidia-strata'});self.assertEqual(actual['external'],providers['external']);models=actual['nvidia-strata']['models'];self.assertEqual([m['id'] for m in models],['qwen27b-hyperqwen-search','bolt-vllm']);self.assertEqual(models[0]['customField'],'keep');self.assertEqual(entries[1]['config'],{'provider':'nvidia-strata','model':'qwen27b-hyperqwen-search'})
   registration.configure('web');self.assertEqual(yaml.safe_load(path.read_text()),entries)
if __name__=='__main__':unittest.main()
