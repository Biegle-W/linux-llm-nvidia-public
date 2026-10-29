"""Keep MoE RAM limits and guarded ownership while allowing uncapped dense host RAM."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
import os
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from profile_catalog import get_profile, worker_budget


class WorkerBudget(unittest.TestCase):
    def test_infinity_swap_is_scoped_to_the_guarded_dense_launcher(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp/'scripts').mkdir()
            script=temp/'scripts/run_bounded_test.sh'
            script.write_text((root/'scripts/run_bounded_test.sh').read_text())
            # The launcher requires a visible-console handshake before systemd.
            # Stub that UI boundary in this isolated argument-construction test.
            (temp/'scripts/visible_terminal.py').write_text(
                'import sys\nassert sys.argv[1] == "open"\n'
                'assert "--unit" in sys.argv\nprint("fixture-console-opened")\n')
            fake=temp/'systemd-run'
            fake.write_text('#!/usr/bin/python3\nimport sys\nprint("\\n".join(sys.argv[1:]))\n')
            fake.chmod(0o755)
            env=dict(os.environ,PATH=str(temp)+':'+os.environ['PATH'])
            guarded=str(temp/'scripts/supervise_dense.py')
            cases=[('qwen27b',guarded,'hyperqwen','infinity'),
                   ('qwen27b',guarded,'sglang','infinity'),
                   ('other',guarded,'hyperqwen','1G'),
                   ('qwen27b','/unrecognized.py','hyperqwen','1G')]
            for name,command,engine,limit in cases:
                result=subprocess.check_output(['bash',str(script),name,'/usr/bin/python3',command,engine],text=True,env=env)
                self.assertIn('fixture-console-opened',result)
                self.assertIn('--property=MemorySwapMax='+limit,result)
                self.assertIn('--property=MemoryHigh='+('infinity' if limit=='infinity' else '30G'),result)
                self.assertIn('--property=MemoryMax='+('infinity' if limit=='infinity' else '36G'),result)
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

    def test_dense_models_have_no_per_worker_ram_caps(self):
        for name in ['qwen27b-hyperqwen', 'qwen27b-sglang']:
            self.assertEqual(worker_budget(get_profile(name)), {'high': None, 'max': None, 'swap': None})

    def test_dense_cannot_take_the_larger_moe_budget(self):
        p = deepcopy(get_profile('qwen27b-hyperqwen'))
        p['worker_memory_gib'] = {'high': 44, 'max': 48, 'swap': None}
        with self.assertRaises(ValueError):
            worker_budget(p)

    def test_moe_accepts_the_bounded_larger_cache_budget(self):
        p = deepcopy(get_profile('deepseek-strata'))
        p['worker_memory_gib'] = {'high': 44, 'max': 48, 'swap': None}
        self.assertEqual(worker_budget(p)['max'], 48)

    def test_fixed_swap_caps_or_unbounded_moe_ram_are_refused(self):
        for b in [{'high': 44, 'max': 48, 'swap': 1}, {'high': 44, 'max': 48, 'swap': 2}, {'high': 48, 'max': 56, 'swap': None}, {'high': 48, 'max': 48, 'swap': None}]:
            p = deepcopy(get_profile('deepseek-maya'))
            p['worker_memory_gib'] = b
            with self.assertRaises(ValueError):
                worker_budget(p)


class DenseNativeGuard(unittest.TestCase):
    def test_uncapped_dense_preflight_still_requires_exact_owned_cgroup(self):
        from unittest.mock import patch,Mock
        import serve_qwen27b_engines as engine
        p=get_profile('qwen27b-hyperqwen')
        for unit,high,hard,accepted in [
                ('llm-test-qwen27b.service','max','max',True),
                ('foreign.service','max','max',False),
                ('llm-test-qwen27b.service',str(30*1024**3),'max',False),
                ('llm-test-qwen27b.service','max',str(36*1024**3),False)]:
            with self.subTest(unit=unit,high=high,hard=hard),tempfile.TemporaryDirectory() as d:
                root=Path(d);group=root/'managed'/unit;group.mkdir(parents=True)
                (group/'memory.high').write_text(high);(group/'memory.max').write_text(hard)
                proc=Mock();proc.read_text.return_value='0::/managed/'+unit+'\n'
                def paths(v):
                    if v=='/proc/self/cgroup':return proc
                    if v=='/sys/fs/cgroup':return root
                    return Path(v)
                with patch.object(engine,'Path',side_effect=paths),patch.dict(os.environ,{'LOCAL_LLM_GUARDED_WORKER':'1'}),patch.object(engine,'verify_storage',side_effect=RuntimeError('storage-boundary')) as verify:
                    with self.assertRaises(RuntimeError if accepted else SystemExit):engine.preflight(p)
                    self.assertEqual(verify.call_count,1 if accepted else 0)
    def test_unbounded_or_half_unbounded_moe_budgets_are_rejected(self):
        for b in [{'high':None,'max':None,'swap':None},{'high':30,'max':None,'swap':None},{'high':None,'max':36,'swap':None}]:
            for name in ['glm-maya','deepseek-strata','deepseek-maya','flash-next-strata']:
                p=deepcopy(get_profile(name));p['worker_memory_gib']=b
                with self.subTest(profile=name,budget=b),self.assertRaises(ValueError):worker_budget(p)

if __name__ == '__main__':
    unittest.main()
