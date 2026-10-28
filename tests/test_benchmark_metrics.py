"""Protect benchmark accounting against parallel-rank duplication and stage mixing."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from benchmark_models import metric_delta


class MetricAccounting(unittest.TestCase):
    def test_pipeline_wall_time_is_not_summed_across_replicas(self):
        before = 'm{pp_rank="0",stage="prefill_forward"} 1\nm{pp_rank="1",stage="prefill_forward"} 2\n'
        after = 'm{pp_rank="0",stage="prefill_forward"} 1.6\nm{pp_rank="1",stage="prefill_forward"} 2.7\n'
        value, rows = metric_delta(before, after, 'm', 'prefill_forward')
        self.assertAlmostEqual(value, .7)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]['pp_rank'], '1')

    def test_chunk_details_do_not_double_count_whole_prefill(self):
        after = 'm{pp_rank="1",stage="prefill_forward"} 0.8\nm{pp_rank="1",stage="chunked_prefill"} 0.5\n'
        value, _ = metric_delta('', after, 'm', 'prefill_forward')
        self.assertAlmostEqual(value, .8)

    def test_counter_reveals_overlapping_requests(self):
        value, _ = metric_delta('m{pp_rank="1",stage="prefill_forward"} 1\n',
                                'm{pp_rank="1",stage="prefill_forward"} 3\n', 'm', 'prefill_forward')
        self.assertEqual(value, 2)

    def test_prior_requests_are_subtracted(self):
        value, _ = metric_delta('vllm:request_prefill_time_seconds_sum{engine="0"} 10.5\n',
                                'vllm:request_prefill_time_seconds_sum{engine="0"} 12.1\n',
                                'vllm:request_prefill_time_seconds_sum')
        self.assertAlmostEqual(value, 1.6)

    def test_tensor_rank_counters_represent_one_request(self):
        before = 'm{pp_rank="0",tp_rank="1",stage="prefill_forward"} 1\nm{pp_rank="0",tp_rank="0",stage="prefill_forward"} 1\n'
        after = 'm{pp_rank="0",tp_rank="1",stage="prefill_forward"} 2\nm{pp_rank="0",tp_rank="0",stage="prefill_forward"} 2\n'
        value, rows = metric_delta(before, after, 'm', 'prefill_forward')
        self.assertEqual(value, 1)
        self.assertEqual(rows[0][0]['tp_rank'], '0')

    def test_tensor_duration_matches_saved_parallel_wall_interval(self):
        before = 'm{pp_rank="0",tp_rank="1"} 0.21442542000022513\nm{pp_rank="0",tp_rank="0"} 0.21457340799997837\n'
        after = 'm{pp_rank="0",tp_rank="1"} 1.257920753000235\nm{pp_rank="0",tp_rank="0"} 1.2580878730000222\n'
        value, rows = metric_delta(before, after, 'm')
        self.assertAlmostEqual(value, 1.0435144650000439)
        self.assertEqual(len(rows), 1)

    def test_combined_pipeline_and_tensor_replicas(self):
        after = '\n'.join(f'm{{pp_rank="{pp}",tp_rank="{tp}"}} {value}'
                          for pp, tp, value in [(0, 0, .4), (0, 1, .5), (1, 0, .7), (1, 1, .8)])
        value, rows = metric_delta('', after, 'm')
        self.assertAlmostEqual(value, .7)
        self.assertEqual(rows[0][0], {'pp_rank': '1', 'tp_rank': '0'})


if __name__ == '__main__':
    unittest.main()
