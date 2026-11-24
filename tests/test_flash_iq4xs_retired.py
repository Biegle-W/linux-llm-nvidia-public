import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'network'), str(ROOT / 'scripts')]
import router
from dsh import configure
from profile_catalog import load_catalog


class FlashIQ4XSRetired(unittest.TestCase):
    retired = ('flash-next-iq4xs-strata',)

    def test_catalog_and_router_reject_retired_id(self):
        ids = {p['id'] for p in load_catalog()['profiles']}
        worker = SimpleNamespace(active=None)
        handler = SimpleNamespace(server=SimpleNamespace(workers=worker))
        listed = router.Handler.catalog(handler)
        for model in self.retired:
            with self.subTest(model=model):
                self.assertNotIn(model, ids)
                self.assertNotIn(model, listed)
                with self.assertRaises(router.RouterError) as caught:
                    router.request_model({'model': model}, '/router/select')
                self.assertEqual(caught.exception.code, 'model_not_found')

    def test_saved_local_selections_move_to_strata(self):
        profiles = load_catalog()['profiles']
        for provider in (configure.ROUTER_ID, 'nvidia-vllm-offload', 'custom-local'):
            stored = {provider: {'baseURL': configure.ROUTER_URL,
                                 'models': [{'id': model} for model in self.retired]}}
            routes = configure.selection_routes(stored, profiles)
            updated = configure.router_providers(stored, profiles)
            for model in self.retired:
                with self.subTest(provider=provider, model=model):
                    selected = {'provider': provider, 'model': model}
                    self.assertEqual(configure.migrate_selection(selected, routes=routes),
                                     {'provider': configure.ROUTER_ID, 'model': 'flash-next-strata'})
                    external = {'provider': 'external', 'model': model}
                    self.assertEqual(configure.migrate_selection(external, routes=routes), external)
                    for entry in updated.values():
                        self.assertNotIn(model, [m['id'] for m in entry['models']])

    def test_launcher_rejects_retired_id(self):
        result = subprocess.run(['bash', ROOT / 'scripts/start_model.sh', 'qwen-iq4xs'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Usage:', result.stderr)
