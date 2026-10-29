"""The approved Qwen floor must not lower other profiles or bypass thermal/swap stops."""
import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from profile_catalog import host_ram_reserve_gib,load_catalog
import serve_router_moe as supervisor

class HostRamReserve(unittest.TestCase):
    def test_other_profiles_keep_eight(self):
        for p in load_catalog()['profiles']:
            if p['id']!='flash-next-strata':self.assertEqual(host_ram_reserve_gib(p),8)
    def test_only_qwen_accepts_two(self):
        self.assertEqual(host_ram_reserve_gib({'id':'flash-next-strata','host_ram_reserve_gib':2}),2)
        for value in [0,1,3,-2,2.0,True,'2']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                host_ram_reserve_gib({'id':'flash-next-strata','host_ram_reserve_gib':value})
        with self.assertRaises(ValueError):host_ram_reserve_gib({'id':'glm-maya','host_ram_reserve_gib':2})
    def run_guard(self,available_gib,reserve=2,temp=40,swap_reason=None):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);group=root/'cgroups/managed/llm-router-worker.service';group.mkdir(parents=True)
            for n,v in [('memory.max',48*1024**3),('memory.high',44*1024**3),('memory.swap.max','max')]:
                (group/n).write_text(str(v))
            (root/'data').mkdir();(root/'data/local-api-key').write_text('test-only-key');(root/'data/local-api-key').chmod(0o600)
            source=root/'.local/state/strata/launch/qwen-flash-next.json';source.parent.mkdir(parents=True);source.write_text(json.dumps({'args':['--max-context','32768']}))
            profile={'id':'flash-next-strata','engine':'Strata','allocated_context':32768,'host_ram_reserve_gib':reserve}
            cgroup=Mock();cgroup.read_text.return_value='0::/managed/llm-router-worker.service\n'
            mem=Mock();mem.read_text.return_value=f'MemAvailable: {int(available_gib*1024**2)} kB\n'
            def paths(value):
                if value=='/proc/self/cgroup':return cgroup
                if value=='/proc/meminfo':return mem
                if value=='/sys/fs/cgroup':return root/'cgroups'
                return Path(value)
            child=Mock(returncode=0,pid=999999);states=iter([None]*4+[0]);child.poll.side_effect=lambda:next(states,0)
            watch=Mock();watch.step.return_value=swap_reason;watch.last_phase='inference'
            with patch.object(supervisor,'ROOT',root),patch.object(supervisor,'Path',side_effect=paths) as path_mock, \
                 patch.object(supervisor,'get_profile',return_value=profile),patch.object(supervisor,'verify_storage'), \
                 patch.object(supervisor,'telemetry_enabled',return_value=False), \
                 patch.object(supervisor.subprocess,'Popen',return_value=child), \
                 patch.object(supervisor.subprocess,'check_output',return_value=str(temp)+'\n'), \
                 patch.object(supervisor,'WorkerWatch',return_value=watch), \
                 patch.object(supervisor.os,'killpg') as kill,patch.object(supervisor.signal,'signal'), \
                 patch.object(supervisor.time,'sleep'),patch.object(sys,'argv',['supervisor','flash-next-strata']):
                path_mock.home.return_value=root
                with self.assertRaises(SystemExit) as result:supervisor.main()
                return result.exception.code,kill.call_count
    def test_qwen_survives_between_two_and_eight(self):
        code,kills=self.run_guard(3);self.assertEqual((code,kills),(0,0))
    def test_exactly_two_is_not_below_floor(self):
        self.assertEqual(self.run_guard(2),(0,0))
    def test_below_two_stops_after_hysteresis(self):
        code,kills=self.run_guard(1);self.assertEqual(code,1);self.assertGreater(kills,0)
    def test_eight_gib_setting_still_stops_at_three(self):
        self.assertEqual(self.run_guard(3,reserve=8)[0],1)
    def test_temperature_guard_is_unchanged(self):
        self.assertEqual(self.run_guard(3,temp=82)[0],1)
    def test_swap_stop_still_wins_above_floor(self):
        self.assertEqual(self.run_guard(16,swap_reason='swap guard test')[0],1)

if __name__=='__main__':unittest.main()
