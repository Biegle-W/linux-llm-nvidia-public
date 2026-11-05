"""Keep the new native preset separate and fail closed on drift."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from flash_iq1m_strata_runtime import prepare_config
from inference_swap_guard import WorkerWatch


class IQ1M(unittest.TestCase):
    def fixture(self,root):
        directory=root/'models/iq1m';directory.mkdir(parents=True)
        files=[]
        for i in range(1,4):
            name=f'Qwen3.8-Flash-Next-UD-IQ1_M-0000{i}-of-00003.gguf'
            (directory/name).write_bytes(b'x')
            files.append(dict(file=name,bytes=1,publisher_sha256_matched=True))
        binary=root/'engine/strata';binary.parent.mkdir();binary.write_bytes(b'native')
        pins=dict(binary='engine/strata',pack_directory='pack',files=files,runtime_files_sha256={'engine/strata':hashlib.sha256(b'native').hexdigest()})
        config=dict(exe=str(binary),tokenizer=str(root/'pack/tokenizer'),gpu=[0,1],layer_split='auto',args=['--pack',str(root/'pack'),'--native',str(directory/files[0]['file']),'--ple-gguf',str(directory/files[-1]['file']),'--max-context','131072','--vram-reserve-mib','1024','--mmap-experts','--resident-experts'])
        pins['args_sha256']=hashlib.sha256(json.dumps(config['args'],separators=(',',':')).encode()).hexdigest()
        manifest=root/'config/flash-iq1m-strata-runtime.json';manifest.parent.mkdir();manifest.write_text(json.dumps(pins))
        preset=root/'home/.local/state/strata/launch/qwen-flash-next-iq1m.json';preset.parent.mkdir(parents=True);preset.write_text(json.dumps(config))
        profile=dict(id='flash-next-iq1m-strata',allocated_context=131072,runtime_manifest='config/flash-iq1m-strata-runtime.json',storage=dict(checkpoint_directory='models/iq1m'))
        return profile,preset,config

    def test_native_preset_is_separate_and_hash_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);profile,preset,config=self.fixture(root)
            self.assertEqual(prepare_config(profile,root,root/'home'),preset)
            (root/'engine/strata').write_bytes(b'changed')
            with self.assertRaises(ValueError):prepare_config(profile,root,root/'home')

    def test_wrong_devices_context_and_arguments_are_rejected(self):
        for field,value in [('gpu',[0]),('layer_split','off'),('args',[]),('tokenizer','wrong-pack')]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as d:
                root=Path(d);profile,preset,config=self.fixture(root);config[field]=value;preset.write_text(json.dumps(config))
                with self.assertRaises(ValueError):prepare_config(profile,root,root/'home')

    def test_native_status_and_bounded_swap_policy(self):
        from unittest.mock import patch
        watch=WorkerWatch('/unused','flash-next-iq1m-strata','fixture',latch=False)
        self.assertEqual((watch.guard.write_limit,watch.guard.combined_limit,watch.guard.pressure_limit),(128,160,15))
        with patch.object(watch,'get',return_value=json.dumps({'busy':True,'loading':False,'queued':0})):
            self.assertEqual(watch.phase(),'inference')

    def test_future_signed_update_refreshes_both_presets_and_iq1m_hashes(self):
        from unittest.mock import patch
        from update_native_builders import strata_qwen_actions
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);stage=root/'stage';qwen=stage/'packages/qwen';qwen.mkdir(parents=True)
            (qwen/'strata').write_bytes(b'new-engine')
            pin=root/'config/flash-iq1m-strata-runtime.json';pin.parent.mkdir()
            pin.write_text(json.dumps(dict(binary='old/strata',runtime_files_sha256={'old/strata':'old-hash','pack/dense.bin':'retained-pack-hash'},args_sha256='retained-arguments')))
            presets={name:root/(name+'.json') for name in ['flash-next-strata','flash-next-iq1m-strata']}
            for path in presets.values():path.write_text(json.dumps(dict(exe='old',args=['--max-context','131072'])))
            receipt={'files':[]}
            with patch('update_builders.canonical',side_effect=lambda r,name:presets[name]):
                strata_qwen_actions(root,{'profiles':list(presets)},stage,root/'terminal','0.1.58',qwen,{'tag_name':'v-next'},receipt)
            self.assertEqual(len(receipt['files']),3)
            new=json.loads((stage/pin.name).read_text())
            self.assertEqual(new['binary'],'stage/packages/qwen/strata')
            self.assertNotIn('old/strata',new['runtime_files_sha256'])
            self.assertEqual(new['runtime_files_sha256']['stage/packages/qwen/strata'],hashlib.sha256(b'new-engine').hexdigest())
            self.assertEqual(new['runtime_files_sha256']['pack/dense.bin'],'retained-pack-hash')
            self.assertEqual(new['args_sha256'],'retained-arguments')
            self.assertEqual(json.loads(pin.read_text())['binary'],'old/strata')

    def test_dsh_replaces_only_the_local_retired_iq1s_selection(self):
        import importlib.util
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('iq1m_dsh_registration',root/'dsh/configure.py')
        registration=importlib.util.module_from_spec(spec);spec.loader.exec_module(registration)
        old='flash-next-iq1s-llamacpp';new='flash-next-iq1m-strata'
        self.assertEqual(registration.migrate_selection({'provider':registration.ROUTER_ID,'model':old}),{'provider':registration.ROUTER_ID,'model':new})
        self.assertEqual(registration.migrate_selection({'provider':'external','model':old}),{'provider':'external','model':old})
        profiles=[dict(id=new,model='Flash',engine='Strata',allocated_context=131072)]
        result=registration.router_providers({registration.ROUTER_ID:{'models':[{'id':old,'name':'old'}]}},profiles)
        self.assertEqual([m['id'] for m in result[registration.ROUTER_ID]['models']],[new])
