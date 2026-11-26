"""benchmarks/shared: this server matches the shared model set and benchmark definitions. No model, no GPU."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_shared', ROOT / 'benchmarks/shared/check_shared.py')
check_shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_shared)
SHARED = ROOT / 'benchmarks/shared/tooluse-short-manifest.json'


class SharedBenchmarkTests(unittest.TestCase):
    def test_nvidia_matches_shared_definitions(self):
        # The harness manifest lives outside the repo; on a machine without it, check against the shared copy.
        manifest = None if check_shared.NVIDIA_HARNESS_MANIFEST.exists() else SHARED
        errors, _ = check_shared.check('nvidia', ROOT, manifest)
        self.assertEqual(errors, [])

    def test_shared_items(self):
        ids = check_shared.tooluse_ids(SHARED)
        self.assertEqual(len(ids), 55)
        self.assertEqual(sum(core for _, core in ids), 49)


if __name__ == '__main__':
    unittest.main()
