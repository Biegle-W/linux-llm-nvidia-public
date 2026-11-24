import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from profile_catalog import load_catalog, profile_enabled
import gbench_template_check as check


class GbenchTemplateCheck(unittest.TestCase):
    cfg = json.loads((ROOT / 'config/gbench-template-check.json').read_text())

    def test_every_enabled_profile_has_a_pinned_tokenizer(self):
        for p in load_catalog()['profiles']:
            if profile_enabled(p):
                with self.subTest(profile=p['id']):
                    spec = self.cfg['tokenizers'][p['model']]
                    self.assertEqual(len(spec['revision']), 40)

    def test_six_template_and_tool_cases(self):
        self.assertEqual(sorted(self.cfg['tasks']), sorted([
            'template_tool_response', 'template_tool_response_twin', 'template_multi_turn',
            'template_multi_turn_twin', 'function_call_single', 'tool_call_minimal']))

    def test_time_limits_stay_short(self):
        limits = self.cfg['time_limits_s']
        self.assertLessEqual(limits['gbench_run'], 120)
        self.assertEqual(limits['per_request_fixed_by_gbench'], 30)

    def test_results_and_tools_stay_out_of_git(self):
        ignored = (ROOT / '.gitignore').read_text().splitlines()
        for top in ('data/', 'models/', 'runtimes/'):
            self.assertIn(top, ignored)
        self.assertTrue(self.cfg['venv'].startswith('runtimes/'))
        self.assertTrue(self.cfg['tokenizer_root'].startswith('models/'))
        self.assertIn("'data/gbench-template'", (ROOT / 'scripts/gbench_template_check.py').read_text())

    def test_tokenizer_dir_is_pinned_by_revision(self):
        d = check.tokenizer_dir(self.cfg, 'Qwen3.8-Flash-Next')
        self.assertEqual(d.relative_to(ROOT).as_posix(), 'models/tokenizers/Qwen__Qwen3.8-Flash-Next/812d96e10a0d')

    def summary(self, ids, status='passed'):
        return {'status': 'passed', 'error_cases': 0, 'task_results': [{'task_id': i, 'status': status} for i in ids]}

    def test_verdict_needs_exit_zero_time_and_each_case_once(self):
        ids = self.cfg['tasks']
        self.assertEqual(check.verdict(self.cfg, self.summary(ids), 0, 9.0), 'PASS')
        self.assertEqual(check.verdict(self.cfg, self.summary(ids), 1, 9.0), 'FAIL')
        self.assertEqual(check.verdict(self.cfg, self.summary(ids), 'timeout', 9.0), 'FAIL')
        self.assertEqual(check.verdict(self.cfg, self.summary(ids), 0, 120.01), 'FAIL')
        self.assertEqual(check.verdict(self.cfg, self.summary(ids[:-1] + ids[:1]), 0, 9.0), 'FAIL')
        self.assertEqual(check.verdict(self.cfg, self.summary(ids, 'failed'), 0, 9.0), 'FAIL')


if __name__ == '__main__':
    unittest.main()
