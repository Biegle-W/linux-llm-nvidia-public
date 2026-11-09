"""GPU peer access stays off: the cards run on CPU PCIe bifurcation (x8/x8) with no P2P.

ggml/llama.cpp (Bolt, Strata, Maya) turns peer access on whenever GGML_CUDA_P2P is present in
the environment, whatever its value (getenv != nullptr), so launchers must remove it rather than
set it to '0'. NCCL reads its own variable's value, so NCCL_P2P_DISABLE='1' stays.
"""
import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = ['scripts/serve_router_moe.py', 'scripts/serve_qwen27b_engines.py', 'scripts/bolt_iq2_worker.py']
ASSIGN = re.compile(r"""GGML_CUDA_P2P\s*=|['"]GGML_CUDA_P2P['"]\s*:""")


class NoGgmlPeerAccess(unittest.TestCase):
    def test_no_tracked_script_or_config_sets_ggml_cuda_p2p(self):
        files = list((ROOT / 'scripts').rglob('*.py')) + list((ROOT / 'config').rglob('*.json'))
        offenders = [str(f.relative_to(ROOT)) for f in files if ASSIGN.search(f.read_text(errors='replace'))]
        self.assertEqual(offenders, [])

    def test_registry_environments_have_no_ggml_cuda_p2p(self):
        for p in json.loads((ROOT / 'config/maintained-profiles.json').read_text())['profiles']:
            for env in (p.get('environment') or {}, (p.get('selected_settings') or {}).get('environment') or {}):
                self.assertNotIn('GGML_CUDA_P2P', env, p['id'])

    def test_launchers_remove_inherited_value_and_keep_nccl_disabled(self):
        for rel in LAUNCHERS:
            s = (ROOT / rel).read_text()
            self.assertRegex(s, r"pop\(\s*['\"]GGML_CUDA_P2P['\"]|\(\s*['\"]NCCL_P2P_LEVEL['\"]\s*,\s*['\"]GGML_CUDA_P2P['\"]\s*\)", rel)
            self.assertIn("NCCL_P2P_DISABLE='1'", s, rel)


if __name__ == '__main__':
    unittest.main()
