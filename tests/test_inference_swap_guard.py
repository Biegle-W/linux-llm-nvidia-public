"""Phase, ownership-counter and sustained-churn checks without GPU work."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from inference_swap_guard import SwapGuard, WorkerWatch, read_cgroup, PAGE_BYTES, MIB


def pages(mib):
    return int(mib * MIB / PAGE_BYTES)


class SwapPolicyTest(unittest.TestCase):
    def test_ssd_relaxation_is_scoped_and_still_bounded(self):
        for profile in ('flash-next-strata', 'glm-maya', 'deepseek-strata', 'deepseek-maya'):
            with self.subTest(profile=profile):
                q = WorkerWatch('/unused', profile, 'test').guard
                self.assertEqual((q.window_s, q.write_limit, q.combined_limit,
                                  q.pressure_limit, q.bad_samples),
                                 (30, 128, 160, 15 if profile in ('flash-next-strata', 'deepseek-maya') else 10, 3))
                q.sample(0, 'inference', 0, 0, 0)
                self.assertIsNone(q.sample(30, 'inference', pages(0.22 * 30), pages(12.95 * 30), 0))
                self.assertIsNotNone(q.sample(60, 'inference', pages(0.22 * 30), pages((12.95 + 129) * 30), 0))
                read = WorkerWatch('/unused', profile, 'test').guard
                read.sample(0, 'inference', 0, 0, 0)
                self.assertIsNotNone(read.sample(30, 'inference', pages(161 * 30), 0, 0))
                pressure = WorkerWatch('/unused', profile, 'test').guard
                for t in [0, 30, 32]:
                    self.assertIsNone(pressure.sample(t, 'inference', 0, 0, pressure.pressure_limit + 1))
                self.assertIsNotNone(pressure.sample(34, 'inference', 0, 0, pressure.pressure_limit + 1))
                missing = WorkerWatch('/unused', profile, 'test').guard
                self.assertIsNone(missing.unavailable('missing'))
                self.assertIsNone(missing.unavailable('missing'))
                self.assertIsNotNone(missing.unavailable('missing'))
                reset = WorkerWatch('/unused', profile, 'test').guard
                reset.sample(1, 'inference', 10, 10, 0)
                self.assertIsNotNone(reset.sample(2, 'inference', 9, 10, 0))
        for profile in ('qwen27b-hyperqwen', 'qwen27b-sglang', 'unknown', 'deepseek-new'):
            with self.subTest(profile=profile):
                guard = WorkerWatch('/unused', profile, 'test').guard
                self.assertEqual((guard.write_limit, guard.combined_limit), (1, 8))

    def test_pressure_allowance_is_two_profile_only_and_still_latches(self):
        for profile in ('flash-next-strata', 'deepseek-maya'):
            with self.subTest(profile=profile):
                g = WorkerWatch('/unused', profile, 'test').guard
                for t in (0, 30, 32, 34):
                    self.assertIsNone(g.sample(t, 'inference', 0, 0, 15))
                self.assertIsNone(g.sample(36, 'inference', 0, 0, 16))
                self.assertIsNone(g.sample(38, 'inference', 0, 0, 14))
                self.assertEqual(g.pressure_bad, 0)
                self.assertIsNone(g.sample(40, 'inference', 0, 0, 16))
                self.assertIsNone(g.sample(42, 'inference', 0, 0, 16))
                self.assertIsNotNone(g.sample(44, 'inference', 0, 0, 16))
                self.assertIsNotNone(g.sample(46, 'idle', 0, 0, 0))
        for profile in ('glm-maya', 'deepseek-strata', 'qwen27b-hyperqwen',
                        'qwen27b-sglang', 'unknown', 'deepseek-new'):
            with self.subTest(profile=profile):
                g = WorkerWatch('/unused', profile, 'test').guard
                self.assertEqual((g.pressure_limit, g.window_s, g.bad_samples), (10, 30, 3))
                for t in (0, 30, 32):
                    self.assertIsNone(g.sample(t, 'inference', 0, 0, 11))
                self.assertIsNotNone(g.sample(34, 'inference', 0, 0, 11))

    def test_loading_and_parked_swap_are_allowed(self):
        g = SwapGuard()
        self.assertIsNone(g.sample(0, 'loading', 0, 0, 90))
        self.assertIsNone(g.sample(60, 'loading', 0, pages(10000), 90))
        self.assertIsNone(g.sample(61, 'inference', 0, pages(10000), 0))
        self.assertIsNone(g.sample(92, 'inference', 0, pages(10000), 0))
        self.assertEqual(g.last_rates['write_mib_s'], 0)

    def test_sustained_swap_writes_stop_and_latch(self):
        g = SwapGuard()
        self.assertIsNone(g.sample(0, 'inference', 0, 0, 0))
        self.assertIsNotNone(g.sample(30, 'inference', 0, pages(60), 0))
        self.assertIsNotNone(g.sample(31, 'idle', 0, pages(60), 0))

    def test_combined_reads_also_detect_thrashing(self):
        g = SwapGuard()
        g.sample(0, 'inference', 0, 0, 0)
        self.assertIsNotNone(g.sample(30, 'inference', pages(270), 0, 0))

    def test_small_io_is_not_a_zero_swap_rule(self):
        g = SwapGuard()
        g.sample(0, 'inference', 0, 0, 0)
        self.assertIsNone(g.sample(30, 'inference', pages(30), pages(15), 0))

    def test_brief_burst_has_no_sustained_window_claim(self):
        g = SwapGuard()
        g.sample(0, 'inference', 0, 0, 0)
        self.assertIsNone(g.sample(5, 'inference', 0, pages(20), 0))
        self.assertIsNone(g.last_rates)

    def test_phase_change_excludes_loading_and_idle_io(self):
        g = SwapGuard()
        g.sample(0, 'inference', 0, 0, 0)
        g.sample(10, 'idle', 0, pages(100), 0)
        g.sample(20, 'inference', 0, pages(100), 0)
        self.assertIsNone(g.sample(50, 'inference', 0, pages(100), 0))

    def test_pressure_waits_for_active_window_and_three_samples(self):
        g = SwapGuard()
        for t in [0, 10, 20, 30, 32]:
            self.assertIsNone(g.sample(t, 'inference', 0, 0, 20))
        self.assertIsNotNone(g.sample(34, 'inference', 0, 0, 20))

    def test_rolling_window_does_not_average_away_new_churn(self):
        g = SwapGuard()
        for t in range(0, 62, 2):
            g.sample(t, 'inference', 0, 0, 0)
        result = None
        for t in range(62, 92, 2):
            result = g.sample(t, 'inference', 0, pages((t - 60) * 2), 0)
            if result:
                break
        self.assertIsNotNone(result)

    def test_counter_reset_and_missing_data_fail_closed(self):
        g = SwapGuard()
        g.sample(1, 'inference', 10, 10, 0)
        self.assertIsNotNone(g.sample(2, 'inference', 9, 10, 0))
        h = SwapGuard()
        self.assertIsNone(h.unavailable('missing'))
        self.assertIsNone(h.unavailable('missing'))
        self.assertIsNotNone(h.unavailable('missing'))

    def test_reads_owned_cgroup_counters_and_parked_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / 'memory.stat').write_text('anon 100\npswpin 7\npswpout 11\n')
            (p / 'memory.pressure').write_text('some avg10=3 avg60=0 avg300=0 total=4\nfull avg10=2 avg60=0 avg300=0 total=3\n')
            (p / 'memory.swap.current').write_text('1048576\n')
            value = read_cgroup(p)
            self.assertEqual(value['swap_out_pages'], 11)
            self.assertEqual(value['pressure_pct'], 2)
            self.assertEqual(value['swap_current_bytes'], 1048576)

    def test_native_busy_and_dense_gauges_cover_direct_requests(self):
        w = WorkerWatch('/unused', 'glm-maya', 'not-a-real-key')
        w.get = lambda _path: json.dumps({'busy': True, 'phase': 'reading the prompt'})
        self.assertEqual(w.phase(), 'inference')
        w.get = lambda _path: json.dumps({'busy': False})
        self.assertEqual(w.phase(), 'idle')
        w.get = lambda _path: json.dumps({'busy': False, 'loaded': False})
        self.assertEqual(w.phase(), 'unloaded')
        w.get = lambda _path: json.dumps({'busy': False, 'loaded': False, 'loading': True})
        self.assertEqual(w.phase(), 'loading')
        w.get = lambda _path: json.dumps({'busy': False, 'compute_active': True, 'loading': False})
        self.assertEqual(w.phase(), 'inference')
        s = WorkerWatch('/unused', 'qwen27b-sglang', 'not-a-real-key')
        s.get = lambda _path: 'sglang:num_running_reqs{pp_rank="0"} 0\nsglang:num_running_reqs{pp_rank="1"} 1\n'
        self.assertEqual(s.phase(), 'inference')


if __name__ == '__main__':
    unittest.main()
