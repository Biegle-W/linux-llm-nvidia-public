"""Reject changed runtime bytes and unqualified Unsloth launch settings."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import strata_unsloth_runtime as rt
from inference_swap_guard import WorkerWatch
from storage_policy import verify_storage
from unittest.mock import patch

class Runtime(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.profile={'id':rt.PROFILE,'engine':'Strata','allocated_context':8192,'selected_settings':{'gpu':[0,1],'experts':6,'cpu_store_decimal_gb':36}}
        names=['engine/strata-dsv41','source/serve/server.py','pack/ds4.txt','pack/tensors.txt','pack/engram.bin','pack/tokenizer/vocab.json','profile-2.00.bin']
        self.hashes={}
        for n in names:
            rel=rt.RUNTIME+'/'+n;p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'pinned fixture');self.hashes[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.manifest={'schema':1,'profile':rt.PROFILE,'runtime_directory':rt.RUNTIME,'engine_version':'0.1.55','signature_verified':True,'sha256':self.hashes}
        (self.root/'config').mkdir();self.save()
    def save(self):(self.root/'config/deepseek-unsloth-runtime.json').write_text(json.dumps(self.manifest))
    def test_pinned_fixture(self):self.assertEqual(rt.verify(self.profile,self.root),self.root/rt.RUNTIME)
    def test_changed_runtime_refused(self):
        (self.root/rt.RUNTIME/'engine/strata-dsv41').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'file/hash'):rt.verify(self.profile,self.root)
    def test_incomplete_manifest_refused(self):
        self.hashes.pop(rt.RUNTIME+'/pack/ds4.txt');self.save()
        with self.assertRaisesRegex(ValueError,'incomplete'):rt.verify(self.profile,self.root)
    def test_missing_trust_evidence_refused(self):
        self.manifest['signature_verified']=False;self.save()
        with self.assertRaisesRegex(ValueError,'identity'):rt.verify(self.profile,self.root)
    def test_symlink_escape_refused(self):
        p=self.root/rt.RUNTIME/'engine/strata-dsv41';p.unlink();outside=self.root/'outside';outside.write_bytes(b'pinned fixture');p.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'file/hash'):rt.verify(self.profile,self.root)
    def test_config_preserves_context_without_credentials(self):
        c=rt.build_config(self.profile,self.root/rt.RUNTIME);self.assertEqual(c['args'][c['args'].index('--max-context')+1],'8192');self.assertNotIn('api_key',c);self.assertEqual(c['env']['STRATA_DS4_SLOT_DIR'],str(self.root/'data/strata-unsloth/ds4-slots'))
    def test_3060_main_placement_refused(self):
        self.profile['selected_settings']['gpu']=[0,1,2]
        with self.assertRaises(ValueError):rt.build_config(self.profile,self.root/rt.RUNTIME)
    def test_wrong_engine_refused(self):
        self.profile['engine']='Maya'
        with self.assertRaisesRegex(ValueError,'identity'):rt.verify(self.profile,self.root)
    def test_changed_gpu_order_refused_before_config_write(self):
        inventory='0, NVIDIA GeForce RTX 3060\n1, NVIDIA GeForce RTX 3080\n2, NVIDIA GeForce RTX 3080 Ti\n'
        with patch('strata_unsloth_runtime.subprocess.check_output',return_value=inventory):
            with self.assertRaisesRegex(ValueError,'GPU identities/order'):rt.prepare_config(self.profile,self.root)
        self.assertFalse((self.root/'data/router/unsloth-source.json').exists())
    def test_main_pair_with_optional_auxiliary(self):
        pair='0, NVIDIA GeForce RTX 3080 Ti\n1, NVIDIA GeForce RTX 3080\n'
        for inventory in [pair,pair+'2, NVIDIA GeForce RTX 3060\n']:
            with self.subTest(inventory=inventory), patch('strata_unsloth_runtime.subprocess.check_output',return_value=inventory):
                target=rt.prepare_config(self.profile,self.root)
                self.assertEqual(json.loads(target.read_text())['gpu'],[0,1])
    def test_missing_or_reindexed_main_pair_refused(self):
        for inventory in ['0, NVIDIA GeForce RTX 3080 Ti\n','1, NVIDIA GeForce RTX 3080 Ti\n0, NVIDIA GeForce RTX 3080\n']:
            with patch('strata_unsloth_runtime.subprocess.check_output',return_value=inventory):
                with self.assertRaisesRegex(ValueError,'GPU identities/order'):rt.prepare_config(self.profile,self.root)
    def test_guard_policy_bounded(self):
        g=WorkerWatch('/unused',rt.PROFILE,'fixture').guard
        self.assertEqual((g.write_limit,g.combined_limit,g.pressure_limit),(128,160,15))

class MixedStorage(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'weights').mkdir()
        for n in ['core.gguf','engram.gguf']:(self.root/'weights'/n).write_bytes(b'fixture')
        self.p={'id':rt.PROFILE,'storage':{'checkpoint_directory':'weights','required_transport':'nvme','file_transports':{'core.gguf':'nvme','engram.gguf':'sata'}}}
    def replies(self,last='sata'):return ['/dev/core\n','part\ndisk nvme\n','/dev/engram\n','part\ndisk '+last+'\n']
    def test_declared_split_passes(self):
        with patch('storage_policy.subprocess.check_output',side_effect=self.replies()):self.assertEqual(verify_storage(self.p,self.root)['weight_files'],2)
    def test_wrong_engram_transport_refused(self):
        with patch('storage_policy.subprocess.check_output',side_effect=self.replies('nvme')),self.assertRaisesRegex(RuntimeError,'requires sata'):verify_storage(self.p,self.root)
    def test_missing_shard_policy_refused(self):
        self.p['storage']['file_transports'].pop('core.gguf')
        with self.assertRaisesRegex(RuntimeError,'explicit per-file'):verify_storage(self.p,self.root)

if __name__=='__main__':unittest.main()
