"""No-GPU promotion, durable rollback and reservation regressions."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from update_policy import compare
from update_transaction import Transaction, write_json
from daily_update_owner import allowed_reservation, owner_valid


def good():
    return {'profile':'test','context':32768,'fixture_sha256':'fixed','settings_sha256':'settings',
            'hardware_sha256':'hardware','prompt_tokens':[2200]*3,'output_tokens':[128]*3,
            'repetitions':3,'prefill_tps':100,'decode_tps':50,'ttft_s':2,
            'checks':dict.fromkeys(['json','arithmetic','retrieval','sustained','reload'],True),
            'resources_passed':True,'telemetry_samples':50,'retrieval_input_tokens':29450,
            'sustained_generation_s':120}


class PromotionTests(unittest.TestCase):
    def test_matched_passing_candidate_and_inclusive_speed_boundaries(self):
        baseline=good(); candidate=good();candidate.update(prefill_tps=95,decode_tps=47.5,ttft_s=2.5)
        self.assertTrue(compare(baseline,candidate)['passed'])
        candidate['decode_tps']=47.49;self.assertFalse(compare(baseline,candidate)['passed'])

    def test_quality_resource_and_measurement_fail_closed(self):
        for field,value in [('resources_passed',False),('telemetry_samples',0),('sustained_generation_s',89),
                            ('retrieval_input_tokens',10000),('repetitions',2),('output_tokens',[127]*3),
                            ('decode_tps',float('nan')),('prefill_tps',0),('fixture_sha256','changed'),
                            ('settings_sha256','changed'),('hardware_sha256','changed'),('context',16384)]:
            with self.subTest(field=field):
                candidate=good();candidate[field]=value;self.assertFalse(compare(good(),candidate)['passed'])
        candidate=good();candidate['checks']['reload']=False;self.assertFalse(compare(good(),candidate)['passed'])
        candidate=good();candidate['vision']=True;self.assertFalse(compare(good(),candidate)['passed'])
        candidate=good();candidate['tools']=True;self.assertFalse(compare(good(),candidate)['passed'])

    def test_bad_production_cannot_be_used_to_promote(self):
        baseline=good();baseline['checks']['json']=False
        self.assertFalse(compare(baseline,good())['passed'])


class TransactionTests(unittest.TestCase):
    def test_process_restart_rolls_back_provisional_files_and_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'runtime';target.write_bytes(b'old');target.chmod(0o755)
            candidate=root/'candidate';candidate.write_bytes(b'new');journal=root/'transaction.json'
            t=Transaction(journal);t.begin('test','rev',{});t.file(target,candidate)
            self.assertEqual(target.read_bytes(),b'new')
            Transaction(journal).rollback();self.assertEqual(target.read_bytes(),b'old')
            self.assertEqual(target.stat().st_mode & 0o777,0o755)

    def test_committed_candidate_is_not_rolled_back_on_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'runtime';target.write_bytes(b'old');candidate=root/'candidate';candidate.write_bytes(b'new')
            t=Transaction(root/'wal.json');t.begin('test','rev',{});t.file(target,candidate);t.commit()
            Transaction(root/'wal.json').rollback();self.assertEqual(target.read_bytes(),b'new')

    def test_directory_swap_restores_original_and_retains_rejected_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'production';target.mkdir();(target/'version').write_text('old')
            candidate=root/'candidate';candidate.mkdir();(candidate/'version').write_text('new')
            t=Transaction(root/'job'/'wal.json');t.begin('test','rev',{});t.directory(target,candidate)
            Transaction(root/'job'/'wal.json').rollback();self.assertEqual((target/'version').read_text(),'old')
            self.assertEqual((root/'production.rejected-job'/'version').read_text(),'new')

    def test_recovery_after_first_directory_rename(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'production';target.mkdir();(target/'version').write_text('old')
            backup=root/'backup';os.rename(target,backup)
            journal=root/'wal.json';write_json(journal,{'phase':'prepared','actions':[{'kind':'directory','target':str(target),'backup':str(backup),'candidate':str(root/'candidate')}]})
            Transaction(journal).rollback();self.assertEqual((target/'version').read_text(),'old')

    def test_external_runtime_edits_and_bad_preimages_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'runtime';target.write_bytes(b'old');candidate=root/'candidate';candidate.write_bytes(b'new')
            t=Transaction(root/'wal.json');t.begin('test','rev',{});t.file(target,candidate);target.write_bytes(b'external')
            with self.assertRaisesRegex(RuntimeError,'External'): t.rollback()
            self.assertEqual(target.read_bytes(),b'external')


class ReservationTests(unittest.TestCase):
    def test_foreign_or_changed_reservation_is_never_authorized(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'GPU-LOCK';owner={'owner':'nvidia-daily-update','nonce':'a'*48,'pid':123,'start_ticks':'1'}
            p.write_text(json.dumps({'owner':'other'}))
            with patch('daily_update_owner.owner_valid',return_value=True):
                self.assertFalse(allowed_reservation(p,owner));p.write_text(json.dumps(owner));self.assertTrue(allowed_reservation(p,owner))
                self.assertFalse(allowed_reservation(p,dict(owner,nonce='b'*48)))
            self.assertFalse(owner_valid(owner));self.assertFalse(owner_valid({'owner':'other'}))

    def test_actual_python_test_process_is_not_a_daily_updater(self):
        ticks=(Path('/proc')/str(os.getpid())/'stat').read_text().split(') ',1)[1].split()[19]
        self.assertFalse(owner_valid({'owner':'nvidia-daily-update','nonce':'a'*48,'pid':os.getpid(),'start_ticks':ticks}))



class UpdaterIntegrationTests(unittest.TestCase):
    def prepare(self,root):
        from daily_engine_update import Updater
        from unittest.mock import Mock
        u=Updater.__new__(Updater);u.root=root;u.run_dir=root/'run';u.run_dir.mkdir();u.state_path=root/'state.json';u.state={'rejected':{}};u.owner={'owner':'test'}
        u.manager=Mock();u.clear_own_latch=Mock();u.policy={'components':[]}
        (root/'config').mkdir();write_json(root/'config/daily-update-versions.json',{'test':{'source_commit':'old'}})
        target=root/'production';target.write_bytes(b'old');candidate=root/'candidate';candidate.write_bytes(b'new')
        from update_transaction import sha
        receipt={'files':[{'target':str(target),'candidate':str(candidate),'sha256':sha(candidate)}],'directories':[]}
        component={'id':'test','profiles':['test']}
        return u,target,receipt,component

    def test_success_commits_only_after_all_gates_and_updates_version(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);u,target,receipt,component=self.prepare(root)
            u.qualify=Mock(side_effect=[{'test':good()},{'test':good()}])
            with patch('daily_engine_update.kernel_tests'):
                result=u.process(component,'new-revision',receipt)
            self.assertEqual(result['status'],'promoted');self.assertEqual(target.read_bytes(),b'new')
            self.assertNotIn('pending',u.state)
            self.assertEqual(json.loads((root/'config/daily-update-versions.json').read_text())['test']['source_commit'],'new-revision')
            self.assertEqual(json.loads((root/'run/test/transaction.json').read_text())['phase'],'committed')

    def test_failed_candidate_is_restored_and_smoked_before_pending_clears(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);u,target,receipt,component=self.prepare(root);bad=good();bad['checks']['retrieval']=False
            u.qualify=Mock(side_effect=[{'test':good()},{'test':bad}])
            with patch('daily_engine_update.kernel_tests'),patch('profile_catalog.get_profile',return_value={'id':'test'}),patch('daily_engine_update.Qualification') as q:
                with self.assertRaisesRegex(RuntimeError,'paired'):u.process(component,'bad-revision',receipt)
                q.return_value.exact_json.assert_called_once()
            self.assertEqual(target.read_bytes(),b'old');self.assertNotIn('pending',u.state)
            self.assertEqual(json.loads((root/'config/daily-update-versions.json').read_text())['test']['source_commit'],'old')

    def test_failed_production_does_not_install_or_blacklist_upstream(self):
        from unittest.mock import Mock
        from daily_engine_update import BaselineFailed
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);u,target,receipt,component=self.prepare(root);u.qualify=Mock(side_effect=RuntimeError('baseline failed'))
            with self.assertRaises(BaselineFailed):u.process(component,'new-revision',receipt)
            self.assertEqual(target.read_bytes(),b'old');self.assertNotIn('pending',u.state);self.assertEqual(u.state['rejected'],{})

    def test_interrupt_rolls_back_provisional_runtime(self):
        from unittest.mock import Mock
        from daily_engine_update import Interrupted
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);u,target,receipt,component=self.prepare(root);u.qualify=Mock(side_effect=[{'test':good()},Interrupted('stop')])
            with patch('daily_engine_update.kernel_tests'),patch('profile_catalog.get_profile',return_value={'id':'test'}),patch('daily_engine_update.Qualification'):
                with self.assertRaises(Interrupted):u.process(component,'new-revision',receipt)
            self.assertEqual(target.read_bytes(),b'old');self.assertNotIn('pending',u.state)

    def test_publication_includes_only_the_promoted_runtime_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);u,_,_,_=self.prepare(root);(root/'docs').mkdir()
            (root/'docs/DAILY-ENGINE-UPDATES.md').write_text('# Updates\n')
            rows=[{'component':'sglang','status':'promoted','revision':'a'*40},
                  {'component':'maya-deepseek','status':'rejected-production-preserved','revision':'b'*40}]
            with patch('update_publish.publish') as publish:
                u.publish(rows)
                self.assertEqual(publish.call_args.args[1],['docs/DAILY-ENGINE-UPDATES.md','config/daily-update-versions.json','config/sglang-runtime.json'])

    def test_normal_router_cannot_bypass_an_updater_reservation(self):
        from unittest.mock import Mock
        import worker_manager
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir();lock=root/'data/GPU-LOCK';owner={'owner':'nvidia-daily-update','nonce':'a'*48,'pid':1,'start_ticks':'1'};lock.write_text(json.dumps(owner))
            w=worker_manager.Workers.__new__(worker_manager.Workers);w.wait_native_idle=Mock();w.active='test';w.backend_models=Mock(return_value=[{'id':'test'}])
            with patch.object(worker_manager,'ROOT',root),patch('daily_update_owner.owner_valid',return_value=True):
                with self.assertRaises(worker_manager.RouterError):w.start('test')
                w.start('test',allowed_lock=owner)
                with self.assertRaises(worker_manager.RouterError):w.start('test',allowed_lock=dict(owner,nonce='b'*48))


class RecoveryIntegrationTests(unittest.TestCase):
    prepare=UpdaterIntegrationTests.prepare
    def pending(self,root):
        u,target,receipt,component=self.prepare(root)
        u.base=root/'private';u.base.mkdir();u.reservation=root/'GPU-LOCK'
        old={'owner':'nvidia-daily-update','pid':999999,'start_ticks':'1','nonce':'b'*48}
        u.reservation.write_text(json.dumps(old));u.policy={'components':[component]}
        t=Transaction(root/'provisional'/'transaction.json');t.begin('test','new',old);t.file(target,receipt['files'][0]['candidate'])
        u.state['pending']={'journal':str(t.path),'owner':old};write_json(u.state_path,u.state)
        return u,target,old

    def test_stale_provisional_worker_is_restored_and_smoked_before_release(self):
        with tempfile.TemporaryDirectory() as temp:
            u,target,old=self.pending(Path(temp))
            with patch('daily_engine_update.owner_valid',return_value=False),patch('profile_catalog.get_profile',return_value={'id':'test'}),patch('daily_engine_update.Qualification') as q:
                u.recover();q.return_value.exact_json.assert_called_once()
            self.assertEqual(target.read_bytes(),b'old');self.assertFalse(u.reservation.exists());self.assertNotIn('pending',u.state)

    def test_live_updater_and_foreign_reservation_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            u,target,old=self.pending(Path(temp))
            with patch('daily_engine_update.owner_valid',return_value=True):
                with self.assertRaisesRegex(RuntimeError,'existing updater'):u.recover()
            self.assertEqual(target.read_bytes(),b'new')
            u.reservation.write_text(json.dumps({'owner':'other-task'}))
            with patch('daily_engine_update.owner_valid',return_value=False):
                with self.assertRaisesRegex(RuntimeError,'Another reservation'):u.recover()
            self.assertEqual(json.loads(u.reservation.read_text()),{'owner':'other-task'})

    def test_failed_recovery_smoke_keeps_the_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            u,target,old=self.pending(Path(temp))
            with patch('daily_engine_update.owner_valid',return_value=False),patch('profile_catalog.get_profile',return_value={'id':'test'}),patch('daily_engine_update.Qualification') as q:
                q.return_value.exact_json.side_effect=RuntimeError('smoke failed')
                with self.assertRaisesRegex(RuntimeError,'smoke failed'):u.recover()
            self.assertEqual(target.read_bytes(),b'old');self.assertTrue(u.reservation.exists());self.assertIn('pending',u.state)


class NativeCoverageTests(unittest.TestCase):
    def test_native_tests_cover_both_cards_and_reject_skips(self):
        from update_builders import kernel_tests
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def completed(command,log,**kwargs):Path(log).write_text('100% tests passed')
            with patch('update_builders.subprocess.check_output',return_value='Test #1: kernel_parity\nTotal Tests: 1'),patch('update_builders.run',side_effect=completed) as run:
                kernel_tests({'ctest':str(root)},root)
                self.assertEqual([c.kwargs['env']['CUDA_VISIBLE_DEVICES'] for c in run.call_args_list],['0','1'])
            def skipped(command,log,**kwargs):Path(log).write_text('***Skipped')
            with patch('update_builders.subprocess.check_output',return_value='Test #1: kernel_parity\nTotal Tests: 1'),patch('update_builders.run',side_effect=skipped):
                with self.assertRaisesRegex(RuntimeError,'skipped'):kernel_tests({'ctest':str(root)},root)

class CommitIdentityTests(unittest.TestCase):
    def test_nightly_commit_overrides_personal_environment_identity(self):
        from update_publish import commit
        with patch.dict(os.environ,{'GIT_AUTHOR_NAME':'personal','GIT_AUTHOR_EMAIL':'personal@example.invalid'}),patch('update_publish.subprocess.run') as run:
            commit(Path('/repository'),'Update',['config/pin.json'])
            env=run.call_args.kwargs['env']
            self.assertEqual(env['GIT_AUTHOR_NAME'],'LLM Maintenance')
            self.assertEqual(env['GIT_COMMITTER_NAME'],'LLM Maintenance')
            self.assertEqual(env['GIT_AUTHOR_EMAIL'],'llm-maintenance@example.invalid')
            self.assertEqual(env['GIT_COMMITTER_EMAIL'],'llm-maintenance@example.invalid')


class MemoryEventTests(unittest.TestCase):
    def test_soft_throttle_does_not_hide_hard_failure_or_missing_counters(self):
        from update_qualification import check_memory_events
        self.assertEqual(check_memory_events('high 530\nmax 0\noom 0\noom_kill 0\n')['high'],530)
        for name in ('max','oom','oom_kill'):
            values={'high':530,'max':0,'oom':0,'oom_kill':0};values[name]=1
            with self.assertRaises(RuntimeError):check_memory_events('\n'.join(k+' '+str(v) for k,v in values.items()))
        with self.assertRaises(RuntimeError):check_memory_events('high 0\n')
        with self.assertRaises(ValueError):check_memory_events('high unknown\nmax 0\noom 0\noom_kill 0\n')


if __name__=='__main__':unittest.main()


class RetrievalCountingTests(unittest.TestCase):
    def qualification(self, root, engine, actual=29450):
        from update_qualification import Qualification
        from unittest.mock import Mock
        profile = 'flash-next-strata' if engine == 'Strata' else 'glm-maya'
        cfg = root / 'data/router' / (profile + '-runtime.json')
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps({'tokenizer': str(root / 'pinned-tokenizer')}))
        (root / 'pinned-tokenizer').mkdir(exist_ok=True)
        (root / 'pinned-tokenizer/tokenizer.json').write_text(json.dumps({'model': {'type':'BPE'}}))
        q = object.__new__(Qualification)
        q.root, q.p = root, {'id': profile, 'engine': engine, 'allocated_context': 32768}
        q.request = Mock(return_value={'answer': json.dumps({'start':'COPPER-8271-ORBIT',
            'middle':'VELVET-4936-HARBOR','end':'QUARTZ-6182-RIVER'}),
            'usage': {'prompt_tokens': actual, 'prompt_tokens_details': {'cached_tokens':0}}})
        return q

    def test_strata_uses_pinned_tokenizer_without_unsupported_endpoint(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); q=self.qualification(root, 'Strata')
            q.http=Mock(side_effect=AssertionError('Strata has no token-count endpoint'))
            with patch('update_qualification.subprocess.check_output', return_value='29491') as count:
                self.assertEqual(q.retrieval(),29450)
            q.http.assert_not_called()
            payload=json.loads(count.call_args.kwargs['input'])
            self.assertEqual(payload['path'],str(root/'pinned-tokenizer/tokenizer.json'))
            q.request.assert_called_once()

    def test_maya_keeps_native_token_counter(self):
        import io
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            q=self.qualification(Path(temp), 'Maya')
            q.http=Mock(return_value=io.BytesIO(b'{"tokens":29491}'))
            with patch('update_qualification.subprocess.check_output') as count:
                self.assertEqual(q.retrieval(),29450)
            count.assert_not_called();self.assertEqual(q.http.call_args.args[0],'/api/tokens')

    def test_estimate_does_not_replace_actual_usage_coverage_gate(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            q=self.qualification(Path(temp), 'Strata',actual=10000);q.http=Mock()
            with patch('update_qualification.subprocess.check_output', return_value='29491'):
                with self.assertRaisesRegex(RuntimeError,'Retrieval below allocated context'):
                    q.retrieval()


class NativeCheckpointCountingTests(unittest.TestCase):
    def test_native_format_uses_resolved_terminal_bundle(self):
        from update_qualification import checkpoint_token_count
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); directory=root/'pack-tokenizer';directory.mkdir()
            (directory/'tokenizer.json').write_text('{"model":"gpt2","pre":"qwen35"}')
            bundle=root/'pinned-terminal';(bundle/'bin').mkdir(parents=True)
            (bundle/'bin/strata').touch();(root/'runtimes/bin').mkdir(parents=True)
            (root/'runtimes/bin/strata').symlink_to(bundle/'bin/strata')
            with patch('update_qualification.subprocess.check_output',return_value='29498') as count:
                self.assertEqual(checkpoint_token_count(root,directory,'archive'),29498)
            args=count.call_args.args[0];payload=json.loads(count.call_args.kwargs['input'])
            self.assertEqual(args[0],str(bundle/'python/bin/python3'))
            self.assertEqual(payload['tools'],str(bundle/'tools'))
            self.assertEqual(payload['directory'],str(directory))
            self.assertIn('from strata_tokenizer import Tokenizer',args[2])
            self.assertEqual(count.call_args.kwargs['timeout'],120)

    def test_native_counter_failure_remains_fail_closed(self):
        import subprocess
        from update_qualification import checkpoint_token_count
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);directory=root/'tokenizer';directory.mkdir()
            (directory/'tokenizer.json').write_text('{"model":"gpt2","pre":"qwen35"}')
            with patch('update_qualification.subprocess.check_output',side_effect=subprocess.CalledProcessError(1,['counter'])):
                with self.assertRaises(subprocess.CalledProcessError):
                    checkpoint_token_count(root,directory,'archive')
