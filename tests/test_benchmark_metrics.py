"""Protect benchmark accounting against pipeline double-counting and stage mixing."""
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


if __name__ == '__main__':
    unittest.main()
