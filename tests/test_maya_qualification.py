import json
from pathlib import Path
import sys
import unittest
import tempfile
from daily_engine_update import Updater
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from update_native_builders import build_registered_test_executables

class NativeCoverageTests(unittest.TestCase):
    def test_missing_registered_tests_are_built_without_skipping_present_tests(self):
        listing={'tests':[{'name':'cpu_missing'},{'name':'gpu_present','command':['/build/gpu_present']},{'name':'cpu_missing'}]}
        with patch('update_native_builders.subprocess.check_output',return_value=json.dumps(listing)), patch('update_builders.run') as run:
            self.assertEqual(build_registered_test_executables(Path('/build'),Path('/log'),{}),['cpu_missing'])
            self.assertEqual(run.call_args.args[0],['cmake','--build',Path('/build'),'--parallel','2','--target','cpu_missing'])
    def test_no_missing_targets_does_not_rebuild(self):
        with patch('update_native_builders.subprocess.check_output',return_value=json.dumps({'tests':[{'name':'ok','command':['/build/ok']}]})),patch('update_builders.run') as run:
            self.assertEqual(build_registered_test_executables(Path('/build'),Path('/log'),{}),[])
            run.assert_not_called()
    def test_invalid_missing_target_fails_closed(self):
        with patch('update_native_builders.subprocess.check_output',return_value=json.dumps({'tests':[{'name':'--target'}]})),patch('update_builders.run') as run:
            with self.assertRaises(RuntimeError):build_registered_test_executables(Path('/build'),Path('/log'),{})
            run.assert_not_called()

class LocalResultsTests(unittest.TestCase):
    def test_local_results_never_publish_or_modify_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            u=Updater.__new__(Updater);u.local_only=True;u.run_dir=Path(d)
            with patch('update_publish.publish') as publish:
                u.publish([{'component':'maya','status':'unchanged'}])
                publish.assert_not_called()
            data=json.loads((Path(d)/'report.json').read_text())
            self.assertEqual(data['results'][0]['status'],'unchanged')
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()),['report.json'])
    def test_local_run_refuses_pending_remote_publication(self):
        u=Updater.__new__(Updater);u.local_only=True;u.state={'publication_owned':['docs/x.md']}
        with patch('update_publish.publish') as publish:
            with self.assertRaisesRegex(RuntimeError,'pending remote publication'):u.run(manual=True)
            publish.assert_not_called()

if __name__=='__main__':unittest.main()

class ReviewedMayaTests(unittest.TestCase):
    def rows(self):
        row=dict(profile='deepseek-maya',context=32768,settings_sha256='s',hardware_sha256='h',fixture_sha256='f',prompt_tokens=5701,output_tokens=60,cached_tokens=0,qualification='short-dsh-v1',checks=dict(tool=True,tool_result=True,followup=True,unload=True),resources_passed=True,telemetry_samples=4,prefill_tps=186.8,decode_tps=8.2,ttft_s=31.83)
        import copy
        candidate=copy.deepcopy(row);candidate.update(prefill_tps=171.5,decode_tps=7.7,ttft_s=34.57)
        return row,candidate
    def accept(self,a,b,revision=None,run=None):
        from update_reviewed import maya_reviewed_gate,MAYA_REVIEWED_REVISION,MAYA_REVIEWED_RUN
        return maya_reviewed_gate(a,b,revision or MAYA_REVIEWED_REVISION,run or MAYA_REVIEWED_RUN)
    def test_only_reviewed_speed_exception_is_accepted(self):
        from update_policy import compare_short
        a,b=self.rows();self.assertTrue(compare_short(a,b)['passed'])
        self.assertEqual(len(compare_short(a,b)['warnings']),2)
        gate=self.accept(a,b);self.assertTrue(gate['passed']);self.assertFalse(gate['strict_passed'])
        self.assertEqual(len(gate['accepted_reasons']),2)
    def test_other_run_or_revision_is_rejected(self):
        for kwargs in ({'run':'another-run'},{'revision':'another-revision'}):
            with self.assertRaises(RuntimeError):self.accept(*self.rows(),**kwargs)
    def test_changed_measurement_or_other_gate_is_rejected(self):
        mutations=[lambda b:b.update(prefill_tps=170),lambda b:b.update(ttft_s=100),lambda b:b.update(resources_passed=False),lambda b:b['checks'].update(tool=False)]
        for mutate in mutations:
            a,b=self.rows();mutate(b)
            with self.assertRaises(RuntimeError):self.accept(a,b)
