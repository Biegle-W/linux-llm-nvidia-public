"""All maintained profiles share the approved floor without bypassing thermal/swap stops."""
import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from profile_catalog import host_ram_reserve_gib,load_catalog
import serve_router_moe as supervisor
import supervise_dense as dense_supervisor

class HostRamReserve(unittest.TestCase):
    def test_all_six_select_two(self):
        profiles=load_catalog()['profiles'];self.assertEqual(len(profiles),6)
        for p in profiles:
            self.assertEqual(p['host_ram_reserve_gib'],2)
            self.assertEqual(host_ram_reserve_gib(p),2)
    def test_all_profiles_accept_two_and_invalid_values_fail(self):
        self.assertEqual(host_ram_reserve_gib({'id':'flash-next-strata','host_ram_reserve_gib':2}),2)
        for value in [0,1,3,-2,2.0,True,'2']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                host_ram_reserve_gib({'id':'flash-next-strata','host_ram_reserve_gib':value})
        for p in load_catalog()['profiles']:
            self.assertEqual(host_ram_reserve_gib({'id':p['id'],'host_ram_reserve_gib':2}),2)
            self.assertEqual(host_ram_reserve_gib({'id':p['id']}),2)
    def run_guard(self,available_gib,reserve=2,temp=40,swap_reason=None,dense_engine=None,gpu_free=2048):
        module=dense_supervisor if dense_engine else supervisor
        identifier='qwen27b-'+dense_engine if dense_engine else 'flash-next-strata'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);unit='llm-test-qwen27b.service' if dense_engine else 'llm-router-worker.service';group=root/'cgroups/managed'/unit;group.mkdir(parents=True)
            for n,v in [('memory.max',('max' if dense_engine else 48*1024**3)),('memory.high',('max' if dense_engine else 44*1024**3)),('memory.swap.max','max')]:
                (group/n).write_text(str(v))
            (root/'data').mkdir();(root/'data/local-api-key').write_text('test-only-key');(root/'data/local-api-key').chmod(0o600)
            source=root/'.local/state/strata/launch/qwen-flash-next.json';source.parent.mkdir(parents=True);source.write_text(json.dumps({'args':['--max-context','32768']}))
            profile={'id':identifier,'engine':'Strata','allocated_context':32768,'host_ram_reserve_gib':reserve}
            cgroup=Mock();cgroup.read_text.return_value='0::/managed/'+unit+'\n'
            mem=Mock();mem.read_text.return_value=f'MemAvailable: {int(available_gib*1024**2)} kB\n'
            def paths(value):
                if value=='/proc/self/cgroup':return cgroup
                if value=='/proc/meminfo':return mem
                if value=='/sys/fs/cgroup':return root/'cgroups'
                return Path(value)
            child=Mock(returncode=0,pid=999999);states=iter([None]*4+[0]);child.poll.side_effect=lambda:next(states,0)
            watch=Mock();watch.step.return_value=swap_reason;watch.last_phase='inference';watch.ready=True
            with patch.object(module,'ROOT',root),patch.object(module,'Path',side_effect=paths) as path_mock, \
                 patch.object(module,'get_profile',return_value=profile),patch.object(module,'verify_storage',create=True), \
                 patch.object(module,'telemetry_enabled',return_value=False), \
                 patch.object(module.subprocess,'Popen',return_value=child), \
                 patch.object(module.subprocess,'check_output',return_value=(f'{temp}, {gpu_free}\n' if dense_engine else str(temp)+'\n')), \
                 patch.object(module,'WorkerWatch',return_value=watch), \
                 patch.object(module.os,'killpg') as kill,patch.object(module.signal,'signal'), \
                 patch.object(module.time,'sleep'),patch.object(sys,'argv',['supervisor',dense_engine or 'flash-next-strata']):
                path_mock.home.return_value=root
                with self.assertRaises(SystemExit) as result:module.main()
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

    def test_dense_engines_accept_two_and_three(self):
        for engine in ['hyperqwen','sglang']:
            for available in [2,3]:
                with self.subTest(engine=engine,available=available):
                    self.assertEqual(self.run_guard(available,dense_engine=engine),(0,0))
    def test_dense_engines_stop_below_two(self):
        for engine in ['hyperqwen','sglang']:
            with self.subTest(engine=engine):self.assertEqual(self.run_guard(1,dense_engine=engine)[0],1)
    def test_dense_512mib_gpu_floor_unchanged(self):
        for engine in ['hyperqwen','sglang']:
            with self.subTest(engine=engine):
                self.assertEqual(self.run_guard(3,dense_engine=engine,gpu_free=512),(0,0))
                self.assertEqual(self.run_guard(3,dense_engine=engine,gpu_free=511)[0],1)
    def test_dense_thermal_and_swap_guards_unchanged(self):
        for engine in ['hyperqwen','sglang']:
            with self.subTest(engine=engine):
                self.assertEqual(self.run_guard(3,dense_engine=engine,temp=82)[0],1)
                self.assertEqual(self.run_guard(16,dense_engine=engine,swap_reason='swap guard test')[0],1)

if __name__=='__main__':unittest.main()
