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
   expected={'high':32,'max':36,'swap':None} if profile['id'].startswith('qwen27b-') else {'high':84,'max':86,'swap':None}
   self.assertEqual(worker_budget(profile),expected)
   self.assertGreater(96227652/1024**2-expected['max'],2)
 def test_invalid_minimum_and_legacy_fixture(self):
  for value in [-1,90.5,True,1025]:
   with self.assertRaises(ValueError):require_host_capacity({'minimum_usable_ram_gib':value},'MemTotal: 96227652 kB')
  require_host_capacity({'id':'fixture'})
if __name__=='__main__':unittest.main()
