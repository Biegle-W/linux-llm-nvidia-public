import sys,json,tempfile,unittest,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
from short_tool_metrics import ToolMetrics
class Metrics(unittest.TestCase):
 def test_sglang_native_intervals_and_ranked_prefill(self):
  with tempfile.TemporaryDirectory() as p:
   t=self.tap(p);t.model='qwen27b-sglang'
   counters='sglang:per_stage_req_latency_seconds_sum{stage="prefill_forward",tp_rank="0",pp_rank="0"} 2\nsglang:per_stage_req_latency_seconds_count{stage="prefill_forward",tp_rank="0",pp_rank="0"} 1\nsglang:time_to_first_token_seconds_sum 2.1\nsglang:time_to_first_token_seconds_count 1\nsglang:inter_token_latency_seconds_sum 0.5\nsglang:inter_token_latency_seconds_count 10\n'
   t.finish({}, {'prompt_tokens':100,'completion_tokens':11},{},3,3.5,4,time.perf_counter(),'',counters)
   r=json.loads((Path(p)/'tool-benchmark.json').read_text());self.assertEqual(r['prefill_tps'],50);self.assertEqual(r['ttft_s'],2.1);self.assertEqual(r['decode_tps'],20)
 def tap(self,p):
  t=ToolMetrics.__new__(ToolMetrics);t.output=Path(p);t.model='qwen27b-hyperqwen';return t
 def test_native_metrics_survive_buffered_tool_output(self):
  with tempfile.TemporaryDirectory() as p:
   t=self.tap(p);t.finish({}, {'prompt_tokens':100,'completion_tokens':20},{'prompt_per_second':50,'predicted_per_second':10},3,3,1,time.perf_counter(),'','');r=json.loads((Path(p)/'tool-benchmark.json').read_text());self.assertEqual(r['prefill_tps'],50);self.assertEqual(r['decode_tps'],10)
 def test_buffered_tool_output_does_not_invent_decode(self):
  with tempfile.TemporaryDirectory() as p:
   t=self.tap(p);t.finish({}, {'prompt_tokens':100,'completion_tokens':20},{},3,3.01,1,time.perf_counter(),'','');r=json.loads((Path(p)/'tool-benchmark.json').read_text());self.assertIsNone(r['decode_tps'])
 def test_counter_deltas_use_one_request_and_exclude_cached_tokens(self):
  with tempfile.TemporaryDirectory() as p:
   t=self.tap(p);a='vllm:request_prefill_time_seconds_sum 2\nvllm:request_prefill_time_seconds_count 1\nvllm:request_decode_time_seconds_sum 1\nvllm:request_decode_time_seconds_count 1\nvllm:time_to_first_token_seconds_sum 2.5\nvllm:time_to_first_token_seconds_count 1\n';t.finish({}, {'prompt_tokens':100,'completion_tokens':11,'prompt_tokens_details':{'cached_tokens':20}},{},4,5,1,time.perf_counter(),'',a);r=json.loads((Path(p)/'tool-benchmark.json').read_text());self.assertEqual(r['prefill_tps'],40);self.assertEqual(r['ttft_s'],2.5);self.assertEqual(r['decode_tps'],10)
 def test_tensorfold_speculative_tpot_uses_native_counter(self):
  with tempfile.TemporaryDirectory() as p:
   t=self.tap(p);t.model='qwen27b-tensorfold'
   counters='tensorfold:request_time_per_output_token_seconds_sum 0.005\ntensorfold:request_time_per_output_token_seconds_count 1\n'
   t.finish({}, {'prompt_tokens':100,'completion_tokens':39},{},10,10.2,1,time.perf_counter(),'',counters)
   r=json.loads((Path(p)/'tool-benchmark.json').read_text());self.assertEqual(r['decode_tps'],200)
   self.assertIn('short speculative tool burst',r['decode_method'])
if __name__=='__main__':unittest.main()
