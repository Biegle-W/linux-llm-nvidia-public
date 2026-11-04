from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from profile_catalog import require_host_capacity,load_catalog,worker_budget
class RAM96(unittest.TestCase):
 def test_upgraded_profiles_require_measured_capacity_not_free_ram(self):
  for profile in load_catalog()['profiles']:
   self.assertEqual(profile['minimum_usable_ram_gib'],90)
   require_host_capacity(profile,'MemTotal: 96227652 kB\nMemAvailable: 2097152 kB\n')
   for capacity in [32051232,64279104]:
    with self.subTest(profile=profile['id'],capacity=capacity),self.assertRaises(RuntimeError):require_host_capacity(profile,f'MemTotal: {capacity} kB\nMemAvailable: 99999999 kB\n')
 def test_bounded_budgets_leave_host_reserve(self):
  for profile in load_catalog()['profiles']:
   expected={'high':32,'max':36,'swap':None} if profile['id'].startswith('qwen27b-') else {'high':87.76984786987305,'max':89.76984786987305,'swap':None}
   self.assertEqual(worker_budget(profile),expected)
   self.assertGreaterEqual(98537123840/2**30-expected['max'],2)
 def test_byte_exact_only_two_GiB_remain_outside_heavy_worker(self):
  from profile_catalog import budget_limit_string,budget_systemd_size
  for p in load_catalog()['profiles']:
   if p['id'].startswith('qwen27b-'):continue
   b=worker_budget(p);self.assertEqual(98537123840-int(budget_limit_string(b['max'])),2*2**30)
   self.assertEqual(budget_systemd_size(b['max']),budget_limit_string(b['max']))
 def test_invalid_minimum_and_legacy_fixture(self):
  for value in [-1,90.5,True,1025]:
   with self.assertRaises(ValueError):require_host_capacity({'minimum_usable_ram_gib':value},'MemTotal: 96227652 kB')
  require_host_capacity({'id':'fixture'})
if __name__=='__main__':unittest.main()
