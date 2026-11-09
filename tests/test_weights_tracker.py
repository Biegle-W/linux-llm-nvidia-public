import contextlib, importlib.util, io, json, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('weights_tracker', ROOT / 'scripts/weights_tracker.py')
wt = importlib.util.module_from_spec(spec); spec.loader.exec_module(wt)


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data) if isinstance(data, bytes) else p.write_text(data)


class WeightsTracker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); r = self.root = Path(self.tmp.name)
        sata = r / 'sata'
        write(r / 'data/storage-mount.json', json.dumps({'uuid': 'x', 'mountpoint': str(sata)}))
        write(r / 'config/maintained-profiles.json', json.dumps({'profiles': [
            {'id': 'flash', 'storage': {'checkpoint_directory': 'models/strata/IQ3'}},
            {'id': 'gone-missing', 'storage': {'checkpoint_directory': 'models/strata/absent'}}]}))
        write(r / 'config/comfy-runtime.json', json.dumps({'checkpoint_directory': 'models/comfy-images',
              'models': [{'id': 'img', 'files': [{'file': 'vae/a.safetensors'}]}]}))
        write(r / 'config/comfy-video-entries.json', json.dumps({'models': [{'id': 'vid', 'trial_id': 'vid-trial'}]}))
        write(r / 'config/comfy-video-trial.json', json.dumps({'checkpoint_directory': 'models/comfy-video',
              'models': [{'id': 'vid-trial', 'files': [{'file': 'v.gguf'}]}]}))
        write(r / 'scripts/update_native_builders.py', "table = 'IQ3/shard2.gguf'\n")
        self.cfg = {'roots': [{'repo': 'models'}, {'mount_relative': 'llm'}, {'repo': 'runtimes', 'extensions_only': True}],
                    'weight_extensions': ['.gguf', '.safetensors'], 'min_bytes': 10_000, 'min_weight_bytes': 100,
                    'extra_references': [
                        {'path': 'models/strata/mtp', 'owner': 'router:flash', 'why': 'MTP head'},
                        {'path': 'models/strata/old-pack', 'owner': 'router:retired', 'why': 'pack of a retired entry'},
                        {'path': 'models/strata/IQ3', 'owner': 'updater:scripts/update_native_builders.py#IQ3/shard2.gguf', 'why': 'PLE table'}],
                    'kept': [{'mount_relative': 'llm/backup', 'why': 'owner keeps a backup'}]}
        blob = b'w' * 300
        write(r / 'models/strata/IQ3/shard1.gguf', blob)
        write(r / 'models/strata/mtp/head.bin', b'h' * 20_000)
        write(r / 'models/strata/old-pack/pack.bin', b'p' * 20_000)
        write(r / 'models/comfy-images/vae/a.safetensors', b'a' * 200)
        write(r / 'models/comfy-video/v.gguf', b'v' * 200)
        write(r / 'models/stray.safetensors', b's' * 150)
        write(r / 'models/notes.txt', 'small text is ignored')
        write(sata / 'llm/copy/shard1.gguf', blob)
        write(sata / 'llm/backup/old.gguf', b'b' * 200)
        write(sata / 'llm/shard5.gguf', b'5' * 400)
        (r / 'models/strata/IQ3/shard5.gguf').symlink_to(sata / 'llm/shard5.gguf')
        write(r / 'runtimes/build/fixture.gguf', b'f' * 120)
        write(r / 'runtimes/build/libbig.so', b'l' * 20_000)
        self.old_root = wt.ROOT; wt.ROOT = r

    def tearDown(self):
        wt.ROOT = self.old_root; self.tmp.cleanup()

    def report(self):
        return wt.build_report(self.cfg)

    def test_classifies_used_unused_duplicate_kept(self):
        r = self.report()
        status = {Path(u['path']).name: u['status'] for u in r['unused']}
        self.assertEqual(status, {'stray.safetensors': 'unused', 'pack.bin': 'unused', 'shard1.gguf': 'duplicate', 'fixture.gguf': 'unused'})
        dup = next(u for u in r['unused'] if u['status'] == 'duplicate')
        self.assertTrue(dup['path'].endswith('sata/llm/copy/shard1.gguf'))
        self.assertTrue(dup['duplicate_of'].endswith('models/strata/IQ3/shard1.gguf'))
        used = {Path(u['path']).name: u['owners'] for u in r['used']}
        self.assertEqual(used['shard1.gguf'], ['router:flash', 'updater:scripts/update_native_builders.py#IQ3/shard2.gguf'])
        self.assertEqual(used['head.bin'], ['router:flash'])
        self.assertEqual(used['a.safetensors'], ['comfy:img'])
        self.assertEqual(used['v.gguf'], ['comfy-video:vid'])
        self.assertEqual([Path(k['path']).name for k in r['kept']], ['old.gguf'])
        self.assertNotIn('notes.txt', json.dumps(r)); self.assertNotIn('libbig.so', json.dumps(r))

    def test_symlinked_shard_on_other_drive_is_used_and_counted_there(self):
        r = self.report()
        shard5 = [u for u in r['used'] if u['path'].endswith('shard5.gguf')]
        self.assertEqual(len(shard5), 1)
        self.assertEqual((shard5[0]['drive'], shard5[0]['owners']), ('SATA', ['router:flash', 'updater:scripts/update_native_builders.py#IQ3/shard2.gguf']))

    def test_reports_missing_paths_and_retired_owners(self):
        r = self.report()
        self.assertEqual([m['owner'] for m in r['missing']], ['router:gone-missing'])
        self.assertTrue(any('retired owner router:retired' in p for p in r['problems']))

    def test_updater_reference_lapses_when_updater_stops_using_it(self):
        write(self.root / 'scripts/update_native_builders.py', 'table = None\n')
        r = self.report()
        used = {Path(u['path']).name: u['owners'] for u in r['used']}
        self.assertEqual(used['shard1.gguf'], ['router:flash'])
        self.assertTrue(any('updater no longer mentions' in p for p in r['problems']))

    def test_hardlinks_and_symlinked_roots_counted_once(self):
        (self.root / 'models/link').symlink_to(self.root / 'models/strata/IQ3')
        r = self.report()
        self.assertEqual(sum(1 for u in r['used'] if u['path'].endswith('IQ3/shard1.gguf')), 1)

    def test_main_writes_private_report_and_fails_on_unused(self):
        write(self.root / 'config/weights-inventory.json', json.dumps(self.cfg))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wt.main(['--fail-on-unused']), 1)
        out = self.root / 'data/weights-tracker'
        self.assertIn('## Unused or duplicate weights', (out / 'latest.md').read_text())
        self.assertEqual(json.loads((out / 'history.jsonl').read_text().splitlines()[0])['unused_files'], 4)

    def test_real_inventory_config_is_well_formed(self):
        cfg = json.loads((self.old_root / 'config/weights-inventory.json').read_text())
        for key in ('roots', 'weight_extensions', 'min_bytes', 'min_weight_bytes', 'extra_references', 'kept'):
            self.assertIn(key, cfg)
        for x in cfg['extra_references']:
            self.assertTrue(x['why'] and x['owner'].split(':')[0] in ('router', 'comfy', 'comfy-video', 'updater'), x)
        for k in cfg['kept']:
            self.assertTrue(k['why'], k)
        for prefix in ('home', 'run/media'):  # no machine-specific absolute paths
            self.assertNotIn(f'/{prefix}/', json.dumps(cfg))


if __name__ == '__main__':
    unittest.main()
