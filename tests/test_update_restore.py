"""Short-only update gates, stable discovery, binary-safe publication and staging."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from update_policy import compare_short
from update_builders import upstream


def good():
    return dict(qualification='short-dsh-v1',profile='test',context=8192,settings_sha256='same',hardware_sha256='same',fixture_sha256='same',prompt_tokens=6000,output_tokens=40,cached_tokens=0,prefill_tps=100,decode_tps=50,ttft_s=2,checks=dict.fromkeys(['tool','tool_result','followup','unload'],True),resources_passed=True,telemetry_samples=2)


class ShortGates(unittest.TestCase):
    def test_short_tool_pair_needs_no_stress_or_retrieval(self):
        self.assertTrue(compare_short(good(),good())['passed'])
        changed=good();changed.update(prefill_tps=95,decode_tps=47.5,ttft_s=2.5)
        self.assertTrue(compare_short(good(),changed)['passed'])
    def test_mismatched_cache_fixture_tokens_and_missing_native_metrics_fail_closed(self):
        for field,value in [('qualification','legacy'),('cached_tokens',1),('fixture_sha256','other'),('prompt_tokens',5999),('output_tokens',41),('decode_tps',None),('prefill_tps',float('nan')),('resources_passed',False),('telemetry_samples',0)]:
            row=good();row[field]=value
            with self.subTest(field=field):self.assertFalse(compare_short(good(),row)['passed'])
        row=good();row['checks']['unload']=False;self.assertFalse(compare_short(good(),row)['passed'])
    def test_short_metric_regression_rejects_candidate(self):
        for field,value in [('prefill_tps',94.9),('decode_tps',47.4),('ttft_s',2.51)]:
            row=good();row[field]=value;self.assertFalse(compare_short(good(),row)['passed'])


class Discovery(unittest.TestCase):
    def test_stable_uses_peeled_tag_commit_not_newer_head(self):
        component={'upstream':'https://github.com/example/engine.git','channel':'stable'}
        with patch('update_builders.latest_release',return_value={'tag_name':'v2'}),patch('update_builders.subprocess.check_output',return_value='a'*40+'\trefs/tags/v2\n'+'b'*40+'\trefs/tags/v2^{}\n')as remote:
            self.assertEqual(upstream(component),'b'*40)
            self.assertEqual(remote.call_args.args[0][-2:],['refs/tags/v2','refs/tags/v2^{}'])
    def test_changed_default_branch_cannot_silently_select_stock_sglang(self):
        component={'upstream':'repo','default_branch':'fix/851-consolidated'}
        with patch('update_builders.subprocess.check_output',return_value='ref: refs/heads/main\tHEAD\n'+'a'*40+'\tHEAD\n'):
            with self.assertRaisesRegex(RuntimeError,'branch changed'):upstream(component)


class Publication(unittest.TestCase):
    def test_binary_samples_are_verified_without_utf8_decode(self):
        import sync_public,update_publish
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'data').mkdir();(root/'data/local-api-key').write_text('fixture-secret')
            assets=root/'assets/samples/comfy';assets.mkdir(parents=True);sample=b'\x89PNG\xffbinary';(assets/'image.png').write_bytes(sample)
            (assets/'manifest.json').write_text(json.dumps({'samples':[{'file':'image.png','bytes':len(sample),'sha256':hashlib.sha256(sample).hexdigest()}]}))
            with patch.object(sync_public,'FILES',('assets/samples/comfy/image.png',)),patch.object(sync_public,'SAMPLE_MEDIA',('assets/samples/comfy/image.png',)),patch.object(sync_public,'validate_sample_media')as verify:
                hashes=update_publish.audit_payload(root)
            verify.assert_called_once();self.assertEqual(hashes['assets/samples/comfy/image.png'],hashlib.sha256(sample).hexdigest())


class NativeSettings(unittest.TestCase):
    def test_cuda_uses_matching_sdk_libraries_and_relocatable_origin(self):
        from update_native_builders import cuda_options
        values=cuda_options(Path('/project'))
        self.assertTrue(any('libcudart.so'in x and '/cu13/'in x for x in values))
        self.assertTrue(any('libcublas.so'in x and '/cu13/'in x for x in values))
        self.assertTrue(any('$ORIGIN;'in x for x in values))
    def test_release_asset_rejects_escape_or_unbounded_download(self):
        from update_native_builders import download
        with self.assertRaisesRegex(RuntimeError,'URL/name'):download({'name':'../bad','browser_download_url':'https://evil.invalid/a'},Path('/unused'))
        with self.assertRaisesRegex(RuntimeError,'bounded size'):download({'name':'archive','browser_download_url':'https://github.com/Niko1221/Strata/releases/download/v1/archive','size':9*1024**3},Path('/unused'))


if __name__=='__main__':unittest.main()

class ScheduledConsole(unittest.TestCase):
    def test_console_carries_its_explicit_build_memory_budget(self):
        import visible_terminal
        command=['xterm','-e','updater']
        with patch('visible_terminal.desktop_env',return_value={}),patch('visible_terminal.subprocess.Popen')as launch:
            unit=visible_terminal.launch_terminal(command,unit_properties=('MemoryHigh=6G','MemoryMax=8G'))
        args=launch.call_args.args[0]
        self.assertIn('--property=MemoryHigh=6G',args);self.assertIn('--property=MemoryMax=8G',args)
        self.assertIn('--unit='+unit,args);self.assertTrue(unit.startswith('llm-terminal-'))

class VisibilityPolicy(unittest.TestCase):
    def dispatch(self,mode):
        import daily_update_terminal as terminal
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);(root/'config').mkdir();(root/'config/daily-update.json').write_text(json.dumps({'scheduled_visibility':mode}))
            with patch.object(terminal,'ROOT',root),patch.object(terminal,'desktop_env',return_value={}),patch.object(terminal.sys,'argv',['entry']),patch.object(terminal.signal,'signal'),patch.object(terminal.subprocess,'Popen',return_value=Mock(wait=Mock(return_value=0)))as run:
                self.assertEqual(terminal.main(),0)
                return run.call_args.args[0]
    def test_explicit_headless_schedule_runs_the_guarded_updater(self):
        self.assertNotIn('--check-only',self.dispatch('guarded-headless'))
    def test_absent_headless_authorization_defers_to_discovery(self):
        self.assertEqual(self.dispatch('require-graphical-terminal')[-1],'--check-only')


class FixedFixture(unittest.TestCase):
    def test_paired_fixture_is_reused_outside_repository(self):
        import shutil
        from update_short_qualification import ShortQualification
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);profile={'id':'test'}
            first=ShortQualification(root,profile,root/'run/component/production/test',None,None)
            self.addCleanup(shutil.rmtree,first.fixture,ignore_errors=True)
            second=ShortQualification(root,profile,root/'run/component/candidate/test',None,None)
            self.assertEqual(first.fixture,second.fixture)
            self.assertEqual(first.fixture.parent,Path('/tmp'))
            self.assertFalse(first.fixture.is_relative_to(root))
            self.assertEqual((first.fixture/'proof.txt').stat().st_mode & 0o777,0o600)

class InstallerIdentity(unittest.TestCase):
    def test_timer_identity_does_not_require_a_service_working_directory(self):
        from install_daily_engine_update import managed_preimage
        self.assertTrue(managed_preimage('nvidia-daily-engine-update.timer','[Timer]\nUnit=nvidia-daily-engine-update.service\n'))
        self.assertFalse(managed_preimage('nvidia-daily-engine-update.timer','[Timer]\nUnit=unrelated.service\n'))
        self.assertFalse(managed_preimage('unrelated.service','WorkingDirectory=/project\n',Path('/project')))

class PushRecovery(unittest.TestCase):
    def answers(self,root,*args):
        if args==('branch','--show-current'):return 'main'
        if args[:1]==('rev-list',)and '--reverse'in args:return 'commit'
        if args[:1]==('show',):return 'LLM Maintenance\nllm-maintenance@example.invalid\nLLM Maintenance\nllm-maintenance@example.invalid'
        if args[:1]==('rev-list',):return 'commit parent'
        if args[:1]==('diff-tree',):return 'docs/owned.md'
        raise AssertionError(args)
    def test_committed_owned_records_are_pushed_on_retry(self):
        from update_publish import push_if_ahead
        with patch('update_publish.git',side_effect=self.answers),patch('update_publish.subprocess.run')as run:
            push_if_ahead(Path('/repo'),['docs/owned.md'])
        self.assertEqual(run.call_args.args[0][-3:],['push','origin','main'])
    def test_unrelated_committed_files_are_not_pushed_with_owned_records(self):
        from update_publish import push_if_ahead
        with patch('update_publish.git',side_effect=self.answers),patch('update_publish.subprocess.run')as run:
            with self.assertRaisesRegex(RuntimeError,'Unrelated unpublished files'):push_if_ahead(Path('/repo'),['docs/other.md'])
        run.assert_not_called()


class ScheduledCancellation(unittest.TestCase):
    def test_headless_stop_forwards_only_to_its_owned_coordinator(self):
        import daily_update_terminal as terminal
        import signal
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);(root/'config').mkdir();(root/'config/daily-update.json').write_text(json.dumps({'scheduled_visibility':'guarded-headless'}))
            handlers={};child=Mock();child.poll.return_value=None
            def wait():handlers[signal.SIGTERM]();return 143
            child.wait.side_effect=wait
            with patch.object(terminal,'ROOT',root),patch.object(terminal,'desktop_env',return_value={}),patch.object(terminal.sys,'argv',['entry']),patch.object(terminal.signal,'signal',side_effect=lambda sig,handler:handlers.update({sig:handler})),patch.object(terminal.subprocess,'Popen',return_value=child):
                self.assertEqual(terminal.main(),143)
            child.terminate.assert_called_once()
