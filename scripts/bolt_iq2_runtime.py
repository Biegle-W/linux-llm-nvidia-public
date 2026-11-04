"""Run qualified native IQ2 Bolt through the existing guarded router entry."""
import json
from pathlib import Path
from profile_catalog import get_profile,require_enabled,require_host_capacity
from bolt_iq2_worker import main as serve
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'config/bolt-iq2-runtime.json'
def verify(profile,manifest):
 if (profile['id']!='bolt-vllm' or profile['engine']!='llama.cpp'
     or profile['weight_quant']!='native-IQ2' or profile['allocated_context']!=163840
     or profile['storage']['checkpoint_directory']!=manifest['checkpoint_directory']
     or manifest['planned_context']!=163840 or manifest['fit_target_MiB']!=[384,384]
     or profile.get('runtime_manifest')!='config/bolt-iq2-runtime.json'):
  raise ValueError('Maintained native Bolt profile/manifest mismatch')
 return manifest
def main():
 profile=require_enabled(get_profile('bolt-vllm'));require_host_capacity(profile)
 verify(profile,json.loads(MANIFEST.read_text()))
 return serve(work=ROOT/'data/router/bolt-iq2',unit='llm-router-worker.service',port=10000,
              alias='bolt',manifest=MANIFEST,capture_engine_log=True,profile_id='bolt-vllm',latch=True)
if __name__=='__main__':main()
