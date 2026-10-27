"""Prevent dense limits or swap caps from expanding with MoE cache tuning."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from profile_catalog import get_profile, worker_budget


class WorkerBudget(unittest.TestCase):
    def test_moe_shell_commands_use_managed_router_selection(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp / 'scripts').mkdir()
            shell = temp / 'scripts/start_model.sh'
            shell.write_text((root / 'scripts/start_model.sh').read_text())
            (temp / 'scripts/router_client.py').write_text('import sys; print(" ".join(sys.argv[1:]))')
            for command, model in [('qwen', 'flash-next-strata'), ('glm', 'glm-maya'),
                                   ('strata-deepseek', 'deepseek-strata'), ('maya-deepseek', 'deepseek-maya')]:
                with self.subTest(command=command):
                    result = subprocess.check_output(['bash', str(shell), command], text=True).strip()
                    self.assertEqual(result, '--model ' + model)

    def test_dense_models_keep_their_original_budget(self):
        for name in ['qwen27b-hyperqwen', 'qwen27b-sglang']:
            self.assertEqual(worker_budget(get_profile(name)), {'high': 30, 'max': 36, 'swap': 1})

    def test_dense_cannot_take_the_larger_moe_budget(self):
        p = deepcopy(get_profile('qwen27b-hyperqwen'))
        p['worker_memory_gib'] = {'high': 44, 'max': 48, 'swap': 1}
        with self.assertRaises(ValueError):
            worker_budget(p)

    def test_moe_accepts_the_bounded_larger_cache_budget(self):
        p = deepcopy(get_profile('deepseek-strata'))
        p['worker_memory_gib'] = {'high': 44, 'max': 48, 'swap': 1}
        self.assertEqual(worker_budget(p)['max'], 48)

    def test_larger_swap_or_unbounded_moe_ram_is_refused(self):
        for b in [{'high': 44, 'max': 48, 'swap': 2}, {'high': 48, 'max': 56, 'swap': 1}, {'high': 48, 'max': 48, 'swap': 1}]:
            p = deepcopy(get_profile('deepseek-maya'))
            p['worker_memory_gib'] = b
            with self.assertRaises(ValueError):
                worker_budget(p)


if __name__ == '__main__':
    unittest.main()
