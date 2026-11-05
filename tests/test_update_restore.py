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
    def test_manual_review_accepts_only_one_deepseek_token_without_mutating_evidence(self):
        from update_reviewed import reviewed_gate
        baseline=good();baseline['profile']='deepseek-unsloth-strata'
        candidate=dict(baseline,output_tokens=39)
        self.assertFalse(compare_short(baseline,candidate)['passed'])
        self.assertTrue(reviewed_gate(baseline,candidate)['passed'])
        self.assertEqual(candidate['output_tokens'],39)
        self.assertEqual(reviewed_gate(baseline,candidate)['observed_output_tokens'],[40,39])

    def test_manual_review_keeps_profile_identity_resource_and_speed_gates(self):
        from update_reviewed import reviewed_gate
        baseline=good();baseline['profile']='deepseek-unsloth-strata'
        for field,value in [('profile','flash-next-strata'),('output_tokens',38),('output_tokens',39.0),('prompt_tokens',5999),('fixture_sha256','other'),('cached_tokens',1),('resources_passed',False),('prefill_tps',94.9),('decode_tps',47.4),('ttft_s',2.51)]:
            candidate=dict(baseline,output_tokens=39);candidate[field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError):reviewed_gate(baseline,candidate)

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


class RecoveryVisibility(unittest.TestCase):
    def qualification(self,root,recovery):
        from update_short_qualification import ShortQualification
        q=ShortQualification.__new__(ShortQualification);q.root=root;q.out=root;q.p={'id':'test'};q.recovery=recovery
        (root/'config').mkdir();(root/'config/daily-update.json').write_text(json.dumps({'scheduled_visibility':'require-graphical-terminal'}))
        return q
    def test_restored_production_verification_ignores_closed_or_absent_terminal(self):
        for tty in (False,True):
            with self.subTest(tty=tty),tempfile.TemporaryDirectory()as tmp:
                q=self.qualification(Path(tmp),True)
                with patch('update_short_qualification.sys.stdout',Mock(isatty=Mock(return_value=tty))),patch('update_short_qualification.subprocess.run')as run:
                    q.run_tool(['python','short-dsh'])
                self.assertEqual(run.call_args.args[0],['python','short-dsh'])
                self.assertIn('stdout',run.call_args.kwargs)
                self.assertTrue((Path(tmp)/'coordinator.log').is_file())
    def test_candidate_has_no_recovery_visibility_exemption(self):
        with tempfile.TemporaryDirectory()as tmp:
            q=self.qualification(Path(tmp),False)
            with patch('update_short_qualification.sys.stdout',Mock(isatty=Mock(return_value=False))),patch('update_short_qualification.subprocess.run')as run:
                with self.assertRaisesRegex(RuntimeError,'not authorized'):q.run_tool(['python','candidate'])
            run.assert_not_called()


class OwnedCleanupRetry(unittest.TestCase):
    def test_short_qualification_cleanup_retries_transient_states(self):
        import daily_engine_update  # Resolve the same guarded worker interface.
        from worker_manager import RouterError
        from update_short_qualification import ShortQualification
        with tempfile.TemporaryDirectory()as tmp:
            q=ShortQualification.__new__(ShortQualification);q.root=q.out=Path(tmp);q.p={'id':'qwen27b-sglang'};q.owner={'owner':'fixture'};q.manager=Mock()
            q.manager.start.side_effect=RuntimeError('fixture startup failure')
            q.manager.stop_owned.side_effect=[RouterError('busy',code)for code in ('backend_busy','resources_busy','backend_state_unknown')]+[None]
            with patch('daily_update_owner.allowed_reservation',return_value=True),patch('update_short_qualification.time.monotonic',return_value=0),patch('update_short_qualification.time.sleep')as sleep:
                with self.assertRaisesRegex(RuntimeError,'fixture startup failure'):q.run()
            self.assertEqual(q.manager.stop_owned.call_count,4)
            self.assertTrue(all(c.kwargs=={'allowed_lock':q.owner}for c in q.manager.stop_owned.call_args_list))
            self.assertEqual([c.args for c in sleep.call_args_list],[(2,)]*3)
    def test_cleanup_deadline_propagates_busy_without_unbounded_retry(self):
        import daily_engine_update
        from worker_manager import RouterError
        from update_short_qualification import stop_owned_with_retry
        manager=Mock();manager.stop_owned.side_effect=RouterError('busy','backend_busy')
        with patch('update_short_qualification.time.monotonic',side_effect=[0,120]),patch('update_short_qualification.time.sleep')as sleep:
            with self.assertRaises(RouterError):stop_owned_with_retry(manager,{'owner':'fixture'})
        self.assertEqual(manager.stop_owned.call_count,1);sleep.assert_not_called()
    def test_ownership_conflict_is_not_retried_or_bypassed(self):
        import daily_engine_update
        from worker_manager import RouterError
        from update_short_qualification import stop_owned_with_retry
        manager=Mock();manager.stop_owned.side_effect=RouterError('foreign owner','ownership_conflict')
        with patch('update_short_qualification.time.sleep')as sleep:
            with self.assertRaises(RouterError):stop_owned_with_retry(manager,{'owner':'fixture'})
        self.assertEqual(manager.stop_owned.call_count,1);sleep.assert_not_called()


class TargetLayout(unittest.TestCase):
    def test_path_aliases_are_rejected_but_similar_sibling_names_are_safe(self):
        from update_transaction import validate_target_layout
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);bundle=root/'bundle';bundle.mkdir();alias=root/'alias';alias.symlink_to(bundle,target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,'overlaps'):validate_target_layout([alias/'engine'],[bundle])
            with self.assertRaisesRegex(RuntimeError,'overlaps'):validate_target_layout([bundle],[bundle])
            validate_target_layout([root/'bundle-other/engine'],[bundle])
    def test_transaction_rejects_nested_targets_in_both_orders_and_can_roll_back(self):
        from update_transaction import Transaction
        for file_first in (True,False):
            with self.subTest(file_first=file_first),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp);bundle=root/'bundle';bundle.mkdir();(bundle/'engine').write_bytes(b'original')
                directory=root/'candidate-directory';directory.mkdir();(directory/'engine').write_bytes(b'directory-version')
                file=root/'candidate-file';file.write_bytes(b'file-version')
                tx=Transaction(root/'job/transaction.json');tx.begin('fixture','revision',{})
                if file_first:
                    tx.file(bundle/'engine',file)
                    with self.assertRaisesRegex(RuntimeError,'overlaps'):tx.directory(bundle,directory)
                    self.assertTrue(directory.exists())
                else:
                    tx.directory(bundle,directory)
                    with self.assertRaisesRegex(RuntimeError,'overlaps'):tx.file(bundle/'engine',file)
                    self.assertEqual((bundle/'engine').read_bytes(),b'directory-version')
                tx.rollback();self.assertEqual((bundle/'engine').read_bytes(),b'original')


class CUDAHostHeaders(unittest.TestCase):
    def test_missing_sdk_profiler_header_fails_before_compile(self):
        from update_native_builders import verify_cuda_host_headers
        with tempfile.TemporaryDirectory()as tmp,patch('update_builders.run')as run:
            root=Path(tmp)
            with self.assertRaisesRegex(RuntimeError,'cuda_profiler_api.h'):verify_cuda_host_headers(root,root,root/'log')
            run.assert_not_called()
    def test_host_probe_includes_profiler_before_runtime(self):
        from update_native_builders import verify_cuda_host_headers
        with tempfile.TemporaryDirectory()as tmp,patch('update_builders.run')as run:
            root=Path(tmp);include=root/'runtimes/engine-tools/lib/python3.12/site-packages/nvidia/cu13/include';include.mkdir(parents=True);(include/'cuda_profiler_api.h').write_text('fixture')
            verify_cuda_host_headers(root,root,root/'log')
            text=(root/'cuda-host-headers.cpp').read_text();self.assertLess(text.index('cuda_profiler_api.h'),text.index('cuda_runtime.h'))
            self.assertIn('-fsyntax-only',run.call_args.args[0]);self.assertIn(include,run.call_args.args[0])


class ComponentSelection(unittest.TestCase):
    def test_requested_component_excludes_unrelated_updates(self):
        from daily_engine_update import select_components
        policy={'components':[{'id':'maya'},{'id':'strata'},{'id':'llamacpp'}]}
        self.assertEqual(select_components(policy,['strata']),[{'id':'strata'}])
        self.assertEqual(select_components(policy),policy['components'])
    def test_empty_duplicate_or_unknown_selection_is_rejected(self):
        from daily_engine_update import select_components
        policy={'components':[{'id':'strata'}]}
        for names in [[],['strata','strata'],['unknown']]:
            with self.subTest(names=names),self.assertRaises(RuntimeError):select_components(policy,names)
