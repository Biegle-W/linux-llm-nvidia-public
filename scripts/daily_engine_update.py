#!/usr/bin/env python3
"""Nightly NVIDIA engine updates: stage, paired qualification, promote or recover."""
import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'network'))
from update_transaction import Transaction, sha, write_json
from update_policy import compare
from update_builders import build, upstream, kernel_tests
from update_qualification import Qualification


class Interrupted(RuntimeError): pass
class BaselineFailed(RuntimeError): pass


from daily_update_owner import owner_valid


def start_ticks(pid):
    return (Path('/proc') / str(pid) / 'stat').read_text().split(') ',1)[1].split()[19]


def release_owner(path, owner):
    if path.exists() and json.loads(path.read_text()) == owner:
        path.unlink()


class Updater:
    def __init__(self, root=ROOT):
        self.root = Path(root); self.base = self.root / 'data/daily-update'
        self.base.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock_file = (self.base / 'coordinator.lock').open('a')
        fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.policy = json.loads((self.root / 'config/daily-update.json').read_text())
        self.state_path = self.base / 'state.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {'rejected':{}}
        self.key = (self.root / 'data/local-api-key').read_text().strip()
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.owner = {'owner':'nvidia-daily-update','pid':os.getpid(),'start_ticks':start_ticks(os.getpid()),'nonce':secrets.token_hex(24)}
        self.reservation = self.root / 'data/GPU-LOCK'; self.manager = None

    def health(self):
        req = urllib.request.Request('http://127.0.0.1:10100/health', headers={'Authorization':'Bearer '+self.key})
        with self.op.open(req, timeout=5) as f: return json.load(f)

    def native_idle(self, active):
        if active is None: return True
        from inference_swap_guard import WorkerWatch
        from worker_manager import unit_property, DENSE_UNIT, MOE_UNIT
        unit = DENSE_UNIT if active.startswith('qwen27b-') else MOE_UNIT
        if unit_property(unit, 'ActiveState') not in ('active','activating'): return True
        group = unit_property(unit, 'ControlGroup')
        watch = WorkerWatch(Path('/sys/fs/cgroup')/group.lstrip('/'),active,self.key,latch=False)
        return watch.phase() == 'idle'

    def stop_worker(self,owner):
        from worker_manager import RouterError
        deadline=time.monotonic()+120
        while True:
            try:
                self.manager.stop_owned(allowed_lock=owner); return
            except RouterError as error:
                if error.code not in ('backend_busy','backend_state_unknown','resources_busy') or time.monotonic()>=deadline:
                    raise
                time.sleep(2)

    def recover(self):
        pending = self.state.get('pending')
        owner = pending['owner'] if pending else self.state.get('reservation_owner')
        if not owner: return
        if owner_valid(owner, self.root) and owner['pid'] != os.getpid():
            raise RuntimeError('An existing updater owns recovery; preserve its jobs')
        if self.reservation.exists() and json.loads(self.reservation.read_text()) != owner:
            raise RuntimeError('Another reservation blocks safe recovery')
        # Stale reservation remains until exact-owned workers are stopped and every
        # preimage is restored. Never clear a foreign/live owner to start a schedule.
        if self.manager is None:
            from worker_manager import Workers
            self.manager = Workers(self.key, timeout=1800)
        self.stop_worker(owner)
        if pending:
            transaction = Transaction(pending['journal']); transaction.rollback()
            # Transfer only this stale reservation to this recovery process. Keep
            # it held until restored production answers through normal guards.
            if self.reservation.exists(): write_json(self.reservation,self.owner)
            else:
                with self.reservation.open('x') as f:
                    os.fchmod(f.fileno(),0o600); json.dump(self.owner,f)
            pending['owner'] = self.owner
            self.state['reservation_owner'] = self.owner; write_json(self.state_path,self.state)
            from profile_catalog import get_profile
            component = next(x for x in self.policy['components'] if x['id']==transaction.data['component'])
            for name in component['profiles']:
                self.clear_recovery_latch(name,transaction.data['started_unix'])
                output = self.base/('recovery-'+str(time.time_ns()))/name
                smoke = Qualification(self.root,get_profile(name),output,self.manager,self.owner)
                self.manager.start(name,allowed_lock=self.owner)
                smoke.exact_json('json','Return only JSON with key sum=17+25.',{'sum':42})
                self.stop_worker(self.owner)
            owner = self.owner
        self.state.pop('pending',None); self.state.pop('reservation_owner',None)
        write_json(self.state_path,self.state)
        release_owner(self.reservation,owner)

    def clear_recovery_latch(self,name,since):
        latch=self.root/'data/router/guard-stops'/(name+'.json')
        if latch.exists():
            data=json.loads(latch.read_text())
            if data.get('time',0)>=since:
                write_json(self.base/('recovered-guard-'+str(time.time_ns())+'.json'),data)
                latch.unlink()

    def idle_reserve(self, manual=False):
        idle_since = None
        while manual or datetime.now().hour * 60 + datetime.now().minute < 390:
            h = self.health()
            quiet = (not self.reservation.exists() and not any(h.get(k) for k in ('busy','queued','loading_model','idle_unloading_model','admission_active'))
                     and h.get('idle_for_s',0) >= self.policy['idle_seconds'] and self.native_idle(h.get('active_model')))
            # Also observe the native frontend's direct requests, which bypass router
            # admission but update the existing per-profile activity files.
            now = time.time()
            for p in (self.root / 'data/router/activity').glob('*.txt'):
                try:
                    if now - float(p.read_text()) < self.policy['idle_seconds']: quiet = False
                except (OSError,ValueError): quiet = False
            if quiet:
                idle_since = idle_since or time.monotonic()
                # Server-side idle age plus a fresh atomic reservation and recheck;
                # no active request is stopped to reclaim the GPUs.
                self.state['reservation_owner'] = self.owner; write_json(self.state_path,self.state)
                try:
                    with self.reservation.open('x') as f:
                        os.fchmod(f.fileno(),0o600); json.dump(self.owner,f); f.flush(); os.fsync(f.fileno())
                except FileExistsError:
                    quiet = False
                    self.state.pop('reservation_owner',None); write_json(self.state_path,self.state)
                else:
                    h = self.health()
                    if not any(h.get(k) for k in ('busy','queued','loading_model','admission_active')) and self.native_idle(h.get('active_model')):
                        from worker_manager import Workers
                        self.manager = Workers(self.key, timeout=1800)
                        self.stop_worker(self.owner)
                        return True
                    release_owner(self.reservation,self.owner)
                    self.state.pop('reservation_owner',None); write_json(self.state_path,self.state)
            if manual: return False
            time.sleep(30)
        return False

    def reconcile_router(self):
        # Only reset a stale unloaded selection. If another client has already
        # started after release, preserve it and let normal admission handle it.
        h = self.health()
        if h.get('active_model') and not any(h.get(k) for k in ('busy','queued','loading_model','admission_active')):
            from worker_manager import unit_property, DENSE_UNIT, MOE_UNIT
            if all(unit_property(u,'ActiveState') not in ('active','activating') for u in (DENSE_UNIT,MOE_UNIT)):
                req = urllib.request.Request('http://127.0.0.1:10100/router/unload',headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},data=b'{}')
                try:
                    with self.op.open(req,timeout=10) as f: f.read()
                except OSError: pass

    def clear_own_latch(self, profiles, since):
        for name in profiles:
            latch = self.root / 'data/router/guard-stops' / (name + '.json')
            if latch.exists():
                data = json.loads(latch.read_text())
                if data.get('time',0) >= since:
                    # Caller only invokes this after rollback, to smoke-test restored
                    # production. Old/unrelated guard stops remain blocking evidence.
                    saved = self.run_dir / (name + '-candidate-guard-stop.json')
                    write_json(saved,data); latch.unlink()

    def qualify(self, component, label):
        from profile_catalog import load_catalog
        catalog = {p['id']:p for p in load_catalog()['profiles']}
        rows = {}
        for name in component['profiles']:
            rows[name] = Qualification(self.root,catalog[name],self.run_dir/component['id']/label/name,self.manager,self.owner).run()
            self.stop_worker(self.owner)
        return rows

    def process(self, component, revision, receipt):
        cdir = self.run_dir / component['id']; started = time.time()
        print(json.dumps({'component':component['id'],'stage':'production-baseline'}),flush=True)
        journal = cdir / 'transaction.json'; transaction = Transaction(journal)
        try:
            baseline = self.qualify(component,'production')
        except Exception as error:
            self.stop_worker(self.owner)
            raise BaselineFailed('Production baseline did not qualify; no candidate installed') from error
        # Source/kernel tests run only while this job owns idle GPUs.
        kernel_tests(receipt,cdir)
        transaction.begin(component['id'],revision,self.owner)
        self.state['pending'] = {'journal':str(journal),'owner':self.owner}
        write_json(self.state_path,self.state)
        try:
            for artifact in receipt.get('artifacts',[]):
                if sha(artifact['path']) != artifact['sha256']: raise RuntimeError('Candidate native artifact changed')
            for item in receipt['files']:
                if 'expected_old_sha256' in item and sha(item['target']) != item['expected_old_sha256']:
                    raise RuntimeError('External production edit preserved; candidate aborted')
            for item in receipt['directories']: transaction.directory(item['target'],item['candidate'])
            for item in receipt['files']:
                if sha(item['candidate']) != item['sha256']: raise RuntimeError('Candidate artifact changed since build')
                transaction.file(item['target'],item['candidate'])
            print(json.dumps({'component':component['id'],'stage':'provisional-candidate'}),flush=True)
            candidate = self.qualify(component,'candidate')
            gates = {name:compare(baseline[name],candidate[name]) for name in component['profiles']}
            write_json(cdir/'comparison.json',gates)
            if not all(g['passed'] for g in gates.values()): raise RuntimeError('Candidate failed paired promotion gates')
            versions_path = self.root/'config/daily-update-versions.json'
            versions = json.loads(versions_path.read_text()); versions[component['id']] = {'source_commit':revision,'qualified_on':datetime.now().isoformat(timespec='seconds')}
            version_candidate = cdir/'versions-candidate.json'; write_json(version_candidate,versions)
            transaction.file(versions_path,version_candidate)
            transaction.commit()
            self.state.pop('pending',None); write_json(self.state_path,self.state)
            return {'component':component['id'],'revision':revision,'status':'promoted','gates':gates,
                    'candidate_metrics':{name:{k:row[k] for k in ('context','prefill_tps','decode_tps','ttft_s','retrieval_input_tokens','sustained_generation_s')} for name,row in candidate.items()}}
        except BaseException:
            self.stop_worker(self.owner)
            transaction.rollback()
            self.clear_own_latch(component['profiles'],started)
            # Verify a distinct normal restored worker answers before any lock release.
            for name in component['profiles']:
                from profile_catalog import get_profile
                smoke = Qualification(self.root,get_profile(name),cdir/'rollback-smoke'/name,self.manager,self.owner)
                self.manager.start(name,allowed_lock=self.owner)
                smoke.exact_json('json','Return only JSON with key sum=17+25.',{'sum':42})
                self.stop_worker(self.owner)
            self.state.pop('pending',None); write_json(self.state_path,self.state)
            raise

    def publish(self, results):
        ledger = self.root/'docs/DAILY-ENGINE-UPDATES.md'
        entry = '\n## ' + datetime.now().isoformat(timespec='seconds') + '\n\n'
        for row in results:
            entry += '- ' + row['component'] + ': **' + row['status'] + '**; upstream `' + row['revision'][:12] + '`.\n'
            for name,metrics in row.get('candidate_metrics',{}).items():
                entry += '  - `' + name + '`: ' + str(metrics['context']) + ' context, ' + format(metrics['prefill_tps'],'.2f') + ' prefill tok/s, ' + format(metrics['decode_tps'],'.2f') + ' decode tok/s, ' + format(metrics['ttft_s'],'.3f') + ' s TTFT.\n'
        text = ledger.read_text(); head, _, tail = text.partition('\n'); ledger.write_text(head+'\n'+entry+tail)
        report = {'date':datetime.now().isoformat(),'results':results}
        write_json(self.run_dir/'report.json',report)
        # Reports/pins are the only nightly tracked writes. No raw logs, installed
        # paths, credentials, session data or reservation payloads are exported.
        from update_publish import publish
        owned=['docs/DAILY-ENGINE-UPDATES.md','config/daily-update-versions.json']
        for row in results:
            if row['status']=='promoted' and row['component']=='sglang': owned.append('config/sglang-runtime.json')
            if row['status']=='promoted' and row['component']=='maya-deepseek': owned.append('config/maya-cachebound-runtime.json')
        publish(self.root,owned)

    def run(self, manual=False, check_only=False):
        if check_only and (self.state.get('pending') or self.state.get('reservation_owner')):
            raise RuntimeError('Recovery required before read-only discovery')
        if not check_only: self.recover()
        from profile_catalog import load_catalog
        ids = {p['id'] for p in load_catalog()['profiles']}
        listed = [p for c in self.policy['components'] for p in c['profiles']]
        if ids != set(listed) or len(ids) != len(listed): raise RuntimeError('Updater catalog coverage differs from maintained profiles')
        versions = json.loads((self.root/'config/daily-update-versions.json').read_text())
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.run_dir = self.base/stamp; self.run_dir.mkdir(mode=0o700)
        if not check_only:
            from visible_terminal import open_monitor
            try: open_monitor('NVIDIA daily engine update','nvidia-daily-engine-update.service')
            except Exception: write_json(self.run_dir/'console-warning.json',{'warning':'Minimized console unavailable; systemd journal retained'})
        candidates = []; results = []
        for component in self.policy['components']:
            row = {'component':component['id'],'revision':'unknown'}
            try:
                revision = upstream(component); row['revision'] = revision
                if revision == versions[component['id']]['source_commit']: row['status'] = 'unchanged'
                elif self.state['rejected'].get(component['id']) == revision: row['status'] = 'rejected-revision-not-retried'
                elif check_only: row['status'] = 'update-available'
                else:
                    candidates.append((component,revision,None)); continue
            except Exception as error:
                row.update(status='build-or-discovery-blocked',error=type(error).__name__)
                if row['revision'] != 'unknown' and not check_only: self.state['rejected'][component['id']] = row['revision']
                write_json(self.run_dir/(component['id']+'-failure.json'),{'error':str(error).replace(self.key,'[redacted]')})
            results.append(row)
        write_json(self.state_path,self.state)
        if candidates:
            if not self.idle_reserve(manual):
                results.extend({'component':c['id'],'revision':rev,'status':'deferred-machine-not-idle'} for c,rev,_ in candidates)
            else:
                # Persist reservation ownership even before a candidate is installed.
                self.state['reservation_owner'] = self.owner; write_json(self.state_path,self.state)
                try:
                    for component,revision,receipt in candidates:
                        if not manual and datetime.now().hour * 60 + datetime.now().minute >= 390:
                            results.append({'component':component['id'],'revision':revision,'status':'deferred-after-0630'}); continue
                        try:
                            if __import__('shutil').disk_usage(self.root).free < 40 * 1024**3:
                                raise RuntimeError('Insufficient isolated-build disk headroom')
                            receipt = build(self.root,component,revision,self.root/'runtimes/daily-update'/stamp/component['id'])
                            results.append(self.process(component,revision,receipt))
                        except Interrupted: raise
                        except BaselineFailed as error:
                            write_json(self.run_dir/(component['id']+'-production-failure.json'),{'error':str(error)})
                            results.append({'component':component['id'],'revision':revision,'status':'production-failed-skipped'})
                        except Exception as error:
                            if self.state.get('pending'): raise  # failed rollback retains lock
                            self.state['rejected'][component['id']] = revision
                            write_json(self.state_path,self.state)
                            write_json(self.run_dir/(component['id']+'-qualification-failure.json'),{'error':str(error).replace(self.key,'[redacted]')})
                            results.append({'component':component['id'],'revision':revision,'status':'rejected-production-preserved'})
                finally:
                    if not self.state.get('pending'):
                        self.stop_worker(self.owner)
                        release_owner(self.reservation,self.owner)
                        self.state.pop('reservation_owner',None); write_json(self.state_path,self.state)
                        self.reconcile_router()
        if check_only: write_json(self.run_dir/'discovery.json',results)
        else: self.publish(results)
        print(json.dumps({'results':results,'gpu_work_performed':bool(candidates and self.manager)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recover-only',action='store_true')
    parser.add_argument('--check-only',action='store_true',help='Read upstream revisions; no build, GPU use, publication or promotion')
    parser.add_argument('--manual',action='store_true',help='Permit admission outside the nightly window; still requires idle and ownership checks')
    args = parser.parse_args(); os.umask(0o077); os.environ['GIT_TERMINAL_PROMPT']='0'
    updater = Updater()
    def interrupted(*_): raise Interrupted('Updater interrupted; preserve or restore production')
    signal.signal(signal.SIGTERM,interrupted); signal.signal(signal.SIGINT,interrupted)
    if args.recover_only: updater.recover()
    else: updater.run(args.manual,args.check_only)


if __name__ == '__main__': main()
