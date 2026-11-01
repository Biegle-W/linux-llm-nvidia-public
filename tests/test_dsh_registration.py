import importlib.util,tempfile,unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dsh_registration',ROOT/'dsh/configure.py');registration=importlib.util.module_from_spec(spec);spec.loader.exec_module(registration)
class Registration(unittest.TestCase):
 def test_preserves_custom_routes_aliases_and_selection(self):
  with tempfile.TemporaryDirectory() as folder:
   oldroot,oldcatalog=registration.ROOT,registration.load_catalog
   self.addCleanup(setattr,registration,'ROOT',oldroot);self.addCleanup(setattr,registration,'load_catalog',oldcatalog)
   registration.ROOT=Path(folder);registration.load_catalog=lambda:{'profiles':[{'id':'bolt-vllm','engine':'vLLM-offload','model':'Nemotron Bolt','allocated_context':32768},{'id':'super-vllm','engine':'vLLM-offload','model':'Nemotron Super','allocated_context':32768}]}
   path=Path(folder)/'data/dsh/profiles/web/cordis.patch.yml';path.parent.mkdir(parents=True)
   alias={'id':'custom-search','contextWindow':56320,'customField':'preserve'}
   custom={'displayName':'My models','baseURL':'http://127.0.0.1:10100/v1','apiKeyEnv':'CUSTOM_KEY_ENV','models':[{'id':'bolt-vllm','contextWindow':8192},alias]}
   selected={'provider':'existing','model':'custom-search'}
   path.write_text(yaml.safe_dump([{'id':'llm-pi-ai','config':{'providers':{'existing':custom}}},{'id':'agent-default-model','config':selected}]))
   registration.configure('web');entries=yaml.safe_load(path.read_text());providers=next(x['config']['providers'] for x in entries if x['id']=='llm-pi-ai')
   self.assertEqual(providers['existing']['models'][1],alias);self.assertEqual(providers['existing']['displayName'],'My models');self.assertEqual(providers['existing']['apiKeyEnv'],'CUSTOM_KEY_ENV');self.assertEqual(next(x['config'] for x in entries if x['id']=='agent-default-model'),selected)
   bolt=providers['existing']['models'][0];self.assertEqual((bolt['contextWindow'],bolt['maxTokens']),(32768,4096));self.assertEqual([x['id'] for x in providers['nvidia-vllm-offload']['models']],['super-vllm'])
   registration.configure('web');again=yaml.safe_load(path.read_text());self.assertEqual(entries,again);self.assertEqual(path.stat().st_mode&0o777,0o600)
 def test_hyperqwen_search_only_migrates_selection_and_stays_idempotent(self):
  with tempfile.TemporaryDirectory() as folder:
   oldroot,oldcatalog=registration.ROOT,registration.load_catalog
   self.addCleanup(setattr,registration,'ROOT',oldroot);self.addCleanup(setattr,registration,'load_catalog',oldcatalog)
   registration.ROOT=Path(folder);registration.load_catalog=lambda:{'profiles':[{'id':'qwen27b-hyperqwen','engine':'HyperQwen-vLLM','model':'Qwen3.8-27B','allocated_context':56320}]}
   path=Path(folder)/'data/dsh/profiles/web/cordis.patch.yml';path.parent.mkdir(parents=True)
   provider={'apiKeyEnv':'PRESERVE','models':[{'id':'qwen27b-hyperqwen'},{'id':'qwen27b-hyperqwen-search','customField':'keep'},{'id':'other-model'}]}
   path.write_text(yaml.safe_dump([{'id':'llm-pi-ai','config':{'providers':{'existing':provider,'dynamic':{'baseURL':'preserve'}}}},{'id':'agent-default-model','config':{'provider':'existing','model':'qwen27b-hyperqwen'}}]))
   registration.configure('web');entries=yaml.safe_load(path.read_text());providers=entries[0]['config']['providers'];models=providers['existing']['models']
   self.assertEqual([m['id'] for m in models],['qwen27b-hyperqwen-search','other-model']);self.assertEqual(models[0]['customField'],'keep');self.assertEqual(models[0]['contextWindow'],56320);self.assertEqual(providers['existing']['apiKeyEnv'],'PRESERVE');self.assertEqual(providers['dynamic'],{'baseURL':'preserve'})
   self.assertEqual(entries[1]['config'],{'provider':'existing','model':'qwen27b-hyperqwen-search'})
   registration.configure('web');self.assertEqual(yaml.safe_load(path.read_text()),entries)
if __name__=='__main__':unittest.main()
