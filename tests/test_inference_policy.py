"""Shared lifecycle policy covers every maintained engine/profile."""
import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from inference_policy import load_policy,apply_native_idle,NATIVE_SOURCES

class SharedPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'config').mkdir();self.policy={'schema':1,'idle_timeout_s':600,'lifecycle_telemetry':True,'visible_terminals_required':True}
        self.save()
        for rel in NATIVE_SOURCES.values():
            p=self.root/rel;p.parent.mkdir(parents=True);p.write_text('# Managed NVIDIA idle reservation\nidle_activity_path=None\nidle_lock_path=None\n')
    def save(self):(self.root/'config/inference-policy.json').write_text(json.dumps(self.policy))
    def test_all_six_profiles_receive_the_same_timeout(self):
        profiles=json.loads((ROOT/'config/maintained-profiles.json').read_text())['profiles'];self.assertEqual(len(profiles),6)
        for p in profiles:
            with self.subTest(profile=p['id']):
                if p['engine'] in NATIVE_SOURCES:
                    result=apply_native_idle({'args':['preserved']},p,self.root);self.assertEqual(result['idle_unload_s'],600);self.assertIn(p['id'],result['idle_activity_path']);self.assertEqual(result['args'],['preserved'])
                else:self.assertEqual(load_policy(self.root)['idle_timeout_s'],600)
    def test_zero_or_invalid_timeout_cannot_disable_idle_policy(self):
        for value in [0,-1,True,'600']:
            self.policy['idle_timeout_s']=value;self.save()
            with self.assertRaises(ValueError):load_policy(self.root)
    def test_native_adapter_missing_refuses_policy_claim(self):
        (self.root/NATIVE_SOURCES['Maya']).write_text('unpatched')
        with self.assertRaises(RuntimeError):apply_native_idle({}, {'id':'glm-maya','engine':'Maya'}, self.root)
    def test_native_policy_overrides_stale_disabled_config(self):
        result=apply_native_idle({'idle_unload_s':0},{'id':'deepseek-strata','engine':'Strata'},self.root)
        self.assertEqual(result['idle_unload_s'],600)

    def test_worker_manager_defaults_to_shared_policy_and_cannot_disable_it(self):
        sys.path.insert(0,str(ROOT/'network'))
        from worker_manager import Workers
        with patch.object(Workers,'detect',return_value=None):
            self.assertEqual(Workers('fixture').idle_timeout,600)
            with self.assertRaises(ValueError):Workers('fixture',idle_timeout=0)

if __name__=='__main__':unittest.main()
