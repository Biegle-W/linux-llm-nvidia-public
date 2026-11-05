"""One real DSH read/result/follow-up on an exclusively owned guarded worker."""
import hashlib
import json
import secrets
import tempfile
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from update_transaction import write_json
from update_qualification import check_memory_events


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class ShortQualification:
    def __init__(self,root,profile,output,manager,owner):
        self.root,self.p,self.out=Path(root),profile,Path(output)
        self.manager,self.owner=manager,owner
        self.out.mkdir(parents=True,exist_ok=False)
        record=self.out.parents[1]/'fixtures'/(profile['id']+'.json')
        if record.exists():
            self.fixture=Path(json.loads(record.read_text())['directory'])
            if not self.fixture.name.startswith('nvidia-daily-tool-') or self.fixture.parent!=Path('/tmp') or self.fixture.stat().st_uid!=os.getuid():
                raise RuntimeError('Unexpected fixed DSH fixture ownership')
        else:
            # A workspace inside the repository imports AGENTS.md into the model's
            # prompt. Keep the actual tool fixture outside the repository instead.
            self.fixture=Path(tempfile.mkdtemp(prefix='nvidia-daily-tool-',dir='/tmp'))
            proof=self.fixture/'proof.txt';proof.write_text('NVIDIA_TOOL_OK_'+secrets.token_hex(16)+'\n');proof.chmod(0o600)
            write_json(record,{'directory':str(self.fixture)})

    def run(self):
        from daily_update_owner import allowed_reservation
        from worker_manager import unit_property,DENSE_UNIT,MOE_UNIT
        from inference_swap_guard import WorkerWatch
        reservation=self.root/'data/GPU-LOCK'
        if not allowed_reservation(reservation,self.owner,self.root):raise RuntimeError('Missing exact updater reservation')
        errors=[];samples=[];stop=threading.Event();monitor=None
        unit=DENSE_UNIT if self.p['id'].startswith('qwen27b-') else MOE_UNIT
        try:
            self.manager.start(self.p['id'],allowed_lock=self.owner)
            invocation=unit_property(unit,'InvocationID');group=unit_property(unit,'ControlGroup')
            if not invocation or not group.endswith('/'+unit):raise RuntimeError('Wrong updater worker identity')
            cg=Path('/sys/fs/cgroup')/group.lstrip('/')
            key=(self.root/'data/local-api-key').read_text().strip()
            watch=WorkerWatch(cg,self.p['id'],key,latch=False)
            def sample():
                if not allowed_reservation(reservation,self.owner,self.root) or unit_property(unit,'InvocationID')!=invocation:
                    raise RuntimeError('Qualification ownership changed')
                reason=watch.step()
                if reason:raise RuntimeError('Retained worker resource guard: '+reason)
                events=check_memory_events((cg/'memory.events').read_text())
                samples.append({'time':time.time(),'memory_events':events})
            sample()
            def observe():
                while not stop.wait(2):
                    try:sample()
                    except Exception as error:errors.append(type(error).__name__+': '+str(error));return
            monitor=threading.Thread(target=observe,daemon=True);monitor.start()
            backend=self.manager.backend_models()[0]['id']
            command=[sys.executable,str(self.root/'scripts/smoke_dsh_tools.py'),
                '--model',self.p['id'],'--require-followup','--updater-owner-file',str(reservation),
                '--backend-model',backend,'--fixture',str(self.fixture),'--output',str(self.out/'dsh')]
            if sys.stdout.isatty():
                command=[sys.executable,str(self.root/'scripts/visible_terminal.py'),'foreground','--title',
                         'Daily engine short DSH check: '+self.p['id'],'--',*command]
                subprocess.run(command,check=True,timeout=900)
            else:
                settings=json.loads((self.root/'config/daily-update.json').read_text())
                if settings.get('scheduled_visibility')!='guarded-headless':raise RuntimeError('Headless scheduled qualification is not authorized')
                with (self.out/'coordinator.log').open('w')as log:
                    subprocess.run(command,check=True,timeout=900,stdout=log,stderr=subprocess.STDOUT)
            sample()
            if errors:raise RuntimeError(errors[0])
            state=json.loads((self.out/'dsh/state.json').read_text())
            if not (state.get('phase')=='pass' and state.get('strict_final_format') and state.get('followup_passed')):
                raise RuntimeError('Incomplete actual DSH tool/result/followup')
            metrics=json.loads((self.out/'dsh/tool-benchmark.json').read_text())
            hardware=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True)
            hardware+=next(x for x in Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemTotal:'))
            # Operational settings, not runtime hashes, must match across a pair.
            settings={k:v for k,v in self.p.items()if k in ('id','allocated_context','cli_args','selected_settings','worker_memory_gib','guardrails','kv_cache')}
            result={**metrics,'qualification':'short-dsh-v1','profile':self.p['id'],'context':self.p['allocated_context'],
                    'settings_sha256':fingerprint(settings),'hardware_sha256':fingerprint(hardware),'fixture_sha256':fingerprint((self.fixture/'proof.txt').read_text()),
                    'checks':{'tool':True,'tool_result':True,'followup':True},'resources_passed':True,
                    'telemetry_samples':len(samples),'full_context_stress':False}
        finally:
            stop.set()
            if monitor:monitor.join(timeout=10)
            write_json(self.out/'resource-samples.json',{'samples':samples,'errors':errors})
            # Parent owns unloading/recovery; preserve the reservation on any failure.
            self.manager.stop_owned(allowed_lock=self.owner)
        result['checks']['unload']=True
        write_json(self.out/'qualification.json',result)
        return result
