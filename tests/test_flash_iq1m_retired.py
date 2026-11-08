import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class FlashIq1mRetired(unittest.TestCase):
    def test_dsh_moves_retired_flash_selections_to_iq3_xxs(self):
        spec=importlib.util.spec_from_file_location('iq1m_retired_dsh',ROOT/'dsh/configure.py')
        registration=importlib.util.module_from_spec(spec);spec.loader.exec_module(registration)
        new='flash-next-strata'
        for old in ('flash-next-iq1m-strata','flash-next-iq1s-llamacpp'):
            with self.subTest(old=old):
                self.assertEqual(registration.migrate_selection({'provider':registration.ROUTER_ID,'model':old}),{'provider':registration.ROUTER_ID,'model':new})
                self.assertEqual(registration.migrate_selection({'provider':'external','model':old}),{'provider':'external','model':old})
                profiles=[dict(id=new,model='Flash',engine='Strata',allocated_context=131072)]
                result=registration.router_providers({registration.ROUTER_ID:{'models':[{'id':old,'name':'old'}]}},profiles)
                self.assertEqual([m['id'] for m in result[registration.ROUTER_ID]['models']],[new])

    def test_iq1m_is_gone_from_registry_and_updater(self):
        profiles=json.loads((ROOT/'config/maintained-profiles.json').read_text())['profiles']
        self.assertNotIn('flash-next-iq1m-strata',[p['id'] for p in profiles])
        self.assertNotIn('flash-next-iq1m-strata',(ROOT/'config/daily-update.json').read_text())
        builders=(ROOT/'scripts/update_native_builders.py').read_text()
        self.assertNotIn('flash-next-iq1m',builders)
        self.assertIn('Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf',builders)


if __name__=='__main__':
    unittest.main()
