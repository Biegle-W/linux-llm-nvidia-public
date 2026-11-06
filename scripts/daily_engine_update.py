#!/usr/bin/env python3
"""Daily NVIDIA engine updates: paired short DSH qualification and durable recovery."""
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
from update_transaction import Transaction, sha, write_json, validate_target_layout
from update_policy import compare_short
from update_builders import build, upstream, kernel_tests, latest_release
from update_short_qualification import ShortQualification, stop_owned_with_retry


class Interrupted(RuntimeError): pass
class BaselineFailed(RuntimeError): pass


from daily_update_owner import owner_valid


def start_ticks(pid):
    return (Path('/proc') / str(pid) / 'stat').read_text().split(') ',1)[1].split()[19]


def release_owner(path, owner):
    if path.exists() and json.loads(path.read_text()) == owner:
        path.unlink()


def validate_update_coverage(catalog, policy):
    profiles = {p['id']: p for p in catalog['profiles']}
    listed = [p for c in policy['components'] for p in c['profiles']]
    pinned = policy.get('pinned_profiles', [])
    if not isinstance(pinned, list):
        raise RuntimeError('Pinned updater profiles must be a list')
    for entry in pinned:
        if not isinstance(entry, dict) or set(entry) != {'profile', 'reason'}:
            raise RuntimeError('Pinned updater profile needs an explicit reason')
        name = entry['profile']
        if (not isinstance(name, str) or name not in profiles
                or not ((name == 'deepseek-unsloth-strata'
                            and profiles[name]['engine'] == 'Strata'
                            and profiles[name].get('runtime_manifest') == 'config/deepseek-unsloth-runtime.json')
                        or (name == 'qwen27b-tensorfold'
                            and profiles[name]['engine'] == 'TensorFold'
                            and profiles[name].get('runtime_manifest') == 'config/tensorfold-runtime.json')
                        or (name == 'bolt-vllm'
                            and profiles[name]['engine'] == 'llama.cpp'
                            and profiles[name].get('runtime_manifest') == 'config/bolt-iq2-runtime.json')
                        or (name == 'flash-next-iq1s-llamacpp'
                            and profiles[name]['engine'] == 'llama.cpp'
                            and profiles[name].get('runtime_manifest') == 'config/flash-iq1s-runtime.json'))
                or not profiles[name].get('runtime_manifest')
                or not isinstance(entry['reason'], str) or not entry['reason'].strip()):
            raise RuntimeError('Only explicitly pinned custom runtimes may skip automatic updates')
        listed.append(name)
    if set(profiles) != set(listed) or len(profiles) != len(listed):
        raise RuntimeError('Updater catalog coverage differs from maintained profiles')


def select_components(policy,names=None):
    components=policy['components']
    if names is None:return components
    available={component['id']for component in components}
    if not names or len(set(names))!=len(names) or not set(names)<=available:
        raise RuntimeError('Choose unique maintained updater component IDs')
    return [component for component in components if component['id']in names]


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
        stop_owned_with_retry(self.manager,owner)

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
                smoke = ShortQualification(self.root,get_profile(name),output,self.manager,self.owner,recovery=True)
                smoke.run()
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

    def idle_reserve(self, manual=False, current_only=False):
        idle_since = None
        while manual or datetime.now().hour * 60 + datetime.now().minute < 390:
            h = self.health()
            quiet = (not self.reservation.exists() and not any(h.get(k) for k in ('busy','queued','loading_model','idle_unloading_model','admission_active'))
                     and ((h.get('active_model') is None) if current_only else h.get('idle_for_s',0) >= self.policy['idle_seconds']) and self.native_idle(h.get('active_model')))
            # Also observe the native frontend's direct requests, which bypass router
            # admission but update the existing per-profile activity files.
            now = time.time()
            for p in (self.root / 'data/router/activity').glob('*.txt'):
                try:
                    if not current_only and now - float(p.read_text()) < self.policy['idle_seconds']: quiet = False
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
            rows[name] = ShortQualification(self.root,catalog[name],self.run_dir/component['id']/label/name,self.manager,self.owner).run()
            self.stop_worker(self.owner)
        return rows

    def process(self, component, revision, receipt):
        validate_target_layout(
            [item['target'] for item in receipt['files']]+[
                self.root/'config/daily-update-versions.json',self.root/'config/maintained-profiles.json'],
            [item['target'] for item in receipt['directories']])
        cdir = self.run_dir / component['id']; started = time.time()
        print(json.dumps({'component':component['id'],'stage':'production-baseline'}),flush=True)
        journal = cdir / ('activation-'+str(time.time_ns())) / 'transaction.json'; transaction = Transaction(journal)
        try:
            baseline = self.qualify(component,'production')
        except Interrupted:
            self.stop_worker(self.owner)
            raise
        except Exception as error:
            self.stop_worker(self.owner)
            raise BaselineFailed('Production baseline did not qualify; no candidate installed') from error
        # Source/kernel tests run only while this job owns idle GPUs.
        kernel_tests(receipt,cdir)
        transaction.begin(component['id'],revision,self.owner)
        self.state['pending'] = {'journal':str(journal),'owner':self.owner}
        write_json(self.state_path,self.state)
        try:
            for protected in receipt.get('protected_files',[]):
                if sha(protected['path'])!=protected['sha256']:raise RuntimeError('External private configuration edit preserved')
            for artifact in receipt.get('artifacts',[]):
                if sha(artifact['path']) != artifact['sha256']: raise RuntimeError('Candidate native artifact changed')
            for item in receipt['files']:
                if 'expected_old_sha256' in item and sha(item['target']) != item['expected_old_sha256']:
                    raise RuntimeError('External production edit preserved; candidate aborted')
            for item in receipt['files']:
                if sha(item['candidate']) != item['sha256']: raise RuntimeError('Candidate artifact changed since build')
                transaction.file(item['target'],item['candidate'])
            for item in receipt['directories']: transaction.directory(item['target'],item['candidate'])
            print(json.dumps({'component':component['id'],'stage':'provisional-candidate'}),flush=True)
            candidate = self.qualify(component,'candidate')
            gates = {name:compare_short(baseline[name],candidate[name]) for name in component['profiles']}
            write_json(cdir/'comparison.json',gates)
            if not all(g['passed'] for g in gates.values()): raise RuntimeError('Candidate failed paired promotion gates')
            versions_path = self.root/'config/daily-update-versions.json'
            versions = json.loads(versions_path.read_text()); versions[component['id']] = {'source_commit':revision,'qualified_on':datetime.now().isoformat(timespec='seconds')}
            version_candidate = cdir/'versions-candidate.json'; write_json(version_candidate,versions)
            transaction.file(versions_path,version_candidate)
            catalog_path=self.root/'config/maintained-profiles.json'
            if catalog_path.exists():
                catalog=json.loads(catalog_path.read_text())
                for profile in catalog['profiles']:
                    if profile['id'] not in candidate:continue
                    row=candidate[profile['id']]
                    previous=profile.get('current_configuration_benchmark')
                    if previous:profile.setdefault('short_tool_benchmark_history',[]).append(previous)
                    metrics={key:row[key]for key in ('prefill_tps','decode_tps','ttft_s','prompt_tokens','output_tokens','cached_tokens')}
                    profile['current_configuration_benchmark']=dict(metrics,date=datetime.now().date().isoformat(),context=row['context'],source='docs/DAILY-ENGINE-UPDATES.md',scope='Single paired short DSH qualification; no full-context or sustained claim')
                    profile['engine_refresh_qualification']={'source_commit':revision,'status':'passed paired short DSH qualification','evidence':'docs/DAILY-ENGINE-UPDATES.md'}
                    if 'qualified_engine_runtime'in profile:
                        profile['qualified_engine_runtime'].pop('release',None)
                        profile['qualified_engine_runtime'].update(source_commit=revision,evidence='docs/DAILY-ENGINE-UPDATES.md')
                catalog['updated']=datetime.now().date().isoformat()
                candidate_catalog=cdir/'catalog-candidate.json';write_json(candidate_catalog,catalog)
                transaction.file(catalog_path,candidate_catalog)
            transaction.commit()
            self.state.pop('pending',None); write_json(self.state_path,self.state)
            return {'component':component['id'],'revision':revision,'status':'promoted','gates':gates,
                    'candidate_metrics':{name:{k:row[k] for k in ('context','prefill_tps','decode_tps','ttft_s')} for name,row in candidate.items()}}
        except BaseException:
            self.stop_worker(self.owner)
            transaction.rollback()
            self.clear_own_latch(component['profiles'],started)
            # Verify a distinct normal restored worker answers before any lock release.
            for name in component['profiles']:
                from profile_catalog import get_profile
                smoke = ShortQualification(self.root,get_profile(name),cdir/'rollback-smoke'/name,self.manager,self.owner,recovery=True)
                smoke.run()
                self.stop_worker(self.owner)
            self.state.pop('pending',None); write_json(self.state_path,self.state)
            raise

    def smoke_current(self,name):
        """One current-engine end-to-end qualification; no build or promotion."""
        self.recover()
        from profile_catalog import get_profile
        if name not in [p for component in self.policy['components']for p in component['profiles']]:raise RuntimeError('Profile is not automatically maintained')
        self.run_dir=self.base/('current-smoke-'+str(time.time_ns()));self.run_dir.mkdir(mode=0o700)
        if not self.idle_reserve(manual=True,current_only=True):raise RuntimeError('Current-engine diagnostic requires idle and unloaded serving; no work interrupted')
        try:
            result=ShortQualification(self.root,get_profile(name),self.run_dir/'current'/'short'/name,self.manager,self.owner).run()
            write_json(self.run_dir/'result.json',result)
            print(json.dumps({'profile':name,'short_DSH':'pass','prefill_tps':result['prefill_tps'],'ttft_s':result['ttft_s'],'decode_tps':result['decode_tps']}))
        finally:
            self.stop_worker(self.owner);release_owner(self.reservation,self.owner)
            self.state.pop('reservation_owner',None);write_json(self.state_path,self.state);self.reconcile_router()

    def publish(self, results):
        if getattr(self, 'local_only', False):
            write_json(self.run_dir/'report.json', {'date':datetime.now().isoformat(), 'results':results,
                'publication':'local-only; no remote publication performed'})
            print('Results saved locally: '+str(self.run_dir), flush=True)
            return
        ledger = self.root/'docs/DAILY-ENGINE-UPDATES.md'
        entry = '\n## ' + datetime.now().isoformat(timespec='seconds') + '\n\n'
        for row in results:
            entry += '- ' + row['component'] + ': **' + row['status'] + '**; upstream `' + row['revision'][:12] + '`.\n'
            for name,metrics in row.get('candidate_metrics',{}).items():
                entry += '  - `' + name + '`: ' + str(metrics['context']) + ' context, ' + format(metrics['prefill_tps'],'.2f') + ' prefill tok/s, ' + format(metrics['decode_tps'],'.2f') + ' decode tok/s, ' + format(metrics['ttft_s'],'.3f') + ' s TTFT.\n'
        if any(row.get('candidate_metrics')for row in results):
            # The updater preserves these reviewed per-profile guards; include the
            # companion table beside every nightly performance result list.
            guard_doc=self.root/'docs/ALL-ENTRY-BENCHMARKS-20261105.md'
            guards=guard_doc.read_text();start=guards.index('| Profile | Worker RAM')
            table=guards[start:].split('\n\n',1)[0]
            entry+='\nEffective guards (configured, not peak usage):2GiB host available;100C;3 bad2-second samples; unlimited swap occupancy; swap rates averaged over30s. Selected native reserves and active/loading PSI exceptions remain unchanged.\n\n'+table+'\n\n'
        text = ledger.read_text(); head, _, tail = text.partition('\n'); ledger.write_text(head+'\n'+entry+tail)
        report = {'date':datetime.now().isoformat(),'results':results}
        write_json(self.run_dir/'report.json',report)
        # Reports/pins are the only nightly tracked writes. No raw logs, installed
        # paths, credentials, session data or reservation payloads are exported.
        from update_publish import publish
        owned=['docs/DAILY-ENGINE-UPDATES.md','config/daily-update-versions.json']
        if any(row['status']=='promoted'for row in results) and (self.root/'config/maintained-profiles.json').exists():owned.append('config/maintained-profiles.json')
        for row in results:
            if row['status']=='promoted' and row['component']=='sglang': owned.append('config/sglang-runtime.json')
            if row['status']=='promoted':
                owned.extend(self.policy.get('publication_files',{}).get(row['component'],[]))
        owned=list(dict.fromkeys(self.state.get('publication_owned',[])+owned))
        self.state['publication_owned']=owned
        self.state['publication_hashes']={name:sha(self.root/name)for name in owned if (self.root/name).is_file()}
        write_json(self.state_path,self.state)
        publish(self.root,owned)
        self.state.pop('publication_owned',None);self.state.pop('publication_hashes',None);write_json(self.state_path,self.state)

    def run(self, manual=False, check_only=False, components=None):
        if getattr(self, 'local_only', False) and self.state.get('publication_owned'):
            raise RuntimeError('Local-only run cannot resume pending remote publication')
        if check_only and (self.state.get('pending') or self.state.get('reservation_owner')):
            raise RuntimeError('Recovery required before read-only discovery')
        if not check_only: self.recover()
        if not check_only:
            from update_publish import publish,git
            if self.state.get('publication_owned'):
                for name,expected in self.state.get('publication_hashes',{}).items():
                    if sha(self.root/name)!=expected:raise RuntimeError('External publication edit preserved; review required')
                publish(self.root,self.state['publication_owned'])
                self.state.pop('publication_owned',None);self.state.pop('publication_hashes',None);write_json(self.state_path,self.state)
            if git(self.root,'status','--porcelain','--untracked-files=no') or git(self.root.parent/'linux-llm-nvidia-public','status','--porcelain'):
                raise RuntimeError('Repository edits preserved; automatic engine work deferred until reviewed')
        from profile_catalog import load_catalog
        validate_update_coverage(load_catalog(), self.policy)
        selected=select_components(self.policy,components)
        versions = json.loads((self.root/'config/daily-update-versions.json').read_text())
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns())
        self.run_dir = self.base/stamp; self.run_dir.mkdir(mode=0o700)
        candidates = []; results = []
        for component in selected:
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
        for component in self.policy.get('monitored_engines',[]):
            row={'component':component['id'],'revision':'unknown','automatic_replacement':False}
            try:
                if component.get('channel')=='stable':
                    revision=latest_release(component)['tag_name'];current=component['installed_release']
                else:
                    revision=upstream(component);current=component['installed_commit']
                row.update(revision=revision,status='pinned-current' if revision==current else 'review-required-update-available')
            except Exception as error:
                row.update(status='monitor-discovery-blocked',error=type(error).__name__)
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


def validate_qualification_policy(args,policy):
    if getattr(args,'allow_full_context_tests',False):
        raise RuntimeError('The scheduled updater uses short DSH qualification only; long suites must be run separately on explicit request.')
    if policy.get('validation',{}).get('default') != 'short-actual-harness-tool-call-then-unload':
        raise RuntimeError('Updater requires the selected short actual DSH validation policy')


def install_interrupt_handlers():
    def interrupted(*_):raise Interrupted('Updater interrupted; preserve or restore production')
    previous={sig:signal.getsignal(sig)for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    for sig in previous:signal.signal(sig,interrupted)
    return previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recover-only',action='store_true')
    parser.add_argument('--accept-tested-maya-slowdown',metavar='RUN',help='Accept only the explicitly reviewed Maya 1.1.56 performance regression')
    parser.add_argument('--accept-tested-output-variance',metavar='RUN',help='Manually accept a completed Strata run whose only failed gate is one DeepSeek output token; no inference is repeated')
    parser.add_argument('--check-only',action='store_true',help='Read upstream revisions; no build, GPU use, publication or promotion')
    parser.add_argument('--smoke-current',metavar='PROFILE',help='Verify one current engine through the owned short DSH path; no update/publication')
    parser.add_argument('--components',nargs='+',metavar='ID',help='Qualify only these maintained components; full catalog coverage remains validated')
    parser.add_argument('--local-only',action='store_true',help='Save results locally without commits, exports or pushes; all qualification and ownership gates remain')
    parser.add_argument('--manual',action='store_true',help='Permit admission outside the nightly window; still requires idle and ownership checks')
    parser.add_argument('--allow-full-context-tests',action='store_true',help='Retired flag; long suites must be requested and run separately')
    args = parser.parse_args()
    from inference_policy import load_policy
    validate_qualification_policy(args,load_policy())
    os.umask(0o077); os.environ['GIT_TERMINAL_PROMPT']='0'
    # The coordinator owns the visible terminal; worker units remain API-only.
    os.environ['NVIDIA_API_ONLY']='1'
    if sum(bool(x)for x in [args.recover_only,args.check_only,args.smoke_current,args.accept_tested_output_variance,args.accept_tested_maya_slowdown])>1:parser.error('Choose only one operation')
    if (args.accept_tested_output_variance or args.accept_tested_maya_slowdown) and (not args.manual or args.components):parser.error('Reviewed acceptance requires --manual and no component selector')
    settings=json.loads((ROOT/'config/daily-update.json').read_text())
    if not (args.recover_only or args.check_only or sys.stdout.isatty() or settings.get('scheduled_visibility')=='guarded-headless'):
        raise RuntimeError('GPU qualification requires a visible terminal or the explicit scheduled-headless policy')
    if args.local_only and (not args.manual or args.accept_tested_output_variance or args.accept_tested_maya_slowdown):parser.error('--local-only requires --manual and cannot be combined with reviewed acceptance')
    updater = Updater()
    updater.local_only = args.local_only
    install_interrupt_handlers()
    if args.accept_tested_maya_slowdown:
        from update_reviewed import accept_tested_output_variance
        accept_tested_output_variance(updater,args.accept_tested_maya_slowdown,maya=True)
    elif args.accept_tested_output_variance:
        from update_reviewed import accept_tested_output_variance
        accept_tested_output_variance(updater,args.accept_tested_output_variance)
    elif args.recover_only: updater.recover()
    elif args.smoke_current:updater.smoke_current(args.smoke_current)
    else: updater.run(args.manual,args.check_only,args.components)


if __name__ == '__main__': main()
