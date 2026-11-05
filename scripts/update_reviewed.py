"""Explicit human acceptance of an already tested, rolled-back Strata release."""
import copy
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

from update_policy import compare_short
from update_short_qualification import fingerprint
from update_transaction import Transaction, sha, write_json, validate_target_layout


def reviewed_gate(baseline, candidate):
    """Only a one-token DeepSeek difference is reviewable; recheck speed too."""
    strict = compare_short(baseline, candidate)
    if strict['passed']:
        return strict
    if (baseline.get('profile') != 'deepseek-unsloth-strata'
            or strict['reasons'] != ['Unmatched output_tokens']
            or type(baseline.get('output_tokens')) is not int
            or type(candidate.get('output_tokens')) is not int
            or abs(baseline['output_tokens'] - candidate['output_tokens']) != 1):
        raise RuntimeError('Only one DeepSeek output token may be explicitly accepted')
    normalized = copy.deepcopy(candidate)
    normalized['output_tokens'] = baseline['output_tokens']
    result = compare_short(baseline, normalized)
    if not result['passed']:
        raise RuntimeError('Other promotion gates failed: ' + str(result['reasons']))
    result.update(acceptance='Explicit manual acceptance of one output token only',
                  observed_output_tokens=[baseline['output_tokens'], candidate['output_tokens']],
                  scope='Reviewed short DSH calls with different output lengths; no sustained/full-context claim')
    return result


def verify_preserved_strata(stage, directories, manifest):
    """Recheck signed packages, control bytes and every recorded source/engine hash."""
    from native_idle_policy import transform
    terminal = next(p for target, p in directories.items() if target.name == 'terminal')
    source = next(p for target, p in directories.items() if target.name == 'source')
    engine = next(p for target, p in directories.items() if target.name == 'engine')
    version = manifest['engine_version']
    code = '''import os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1]);from strata_control import signing,engine_component as ec
os.environ.pop('STRATA_UPDATE_TRUSTED_KEYS',None)
s=Path(sys.argv[2]);keys=signing.load_trusted_keys()
signing.verify_bytes(keys,(s/'strata-feed.json').read_bytes(),json.loads((s/'strata-feed.json.sig').read_text()))
signing.install_component_verifier(keys);feed=json.loads((s/'strata-feed.json').read_text())
for section,pattern in [('control','strata-control-*.tar.gz'),('engine','strata-engine-*.tar.gz'),('dsv41','strata-dsv41-*.tar.gz')]:
 paths=list(s.glob(pattern))
 if len(paths)!=1:raise RuntimeError('Ambiguous preserved archive')
 p=paths[0];entries=[e for e in feed[section]['packages']if Path(e['url']).name==p.name]
 if len(entries)!=1 or entries[0]['sha256']!=hashlib.file_digest(p.open('rb'),'sha256').hexdigest():raise RuntimeError('Signed archive changed')
for folder in [s/'packages/qwen',Path(sys.argv[3])]:
 m=ec.read_manifest(folder);ec.verify_signature(m,{**os.environ,ec.ENV_REQUIRE_SIGNED:'1'});ec.verify(m,full=True)
'''
    subprocess.run([sys.executable, '-c', code, str(source), str(stage), str(engine)], check=True, timeout=300)
    control = terminal/version
    if not (terminal/'current').is_symlink() or os.readlink(terminal/'current') != version:
        raise RuntimeError('Preserved control selector changed')
    bytecode=[]
    with tarfile.open(stage/('strata-control-'+version+'-linux-x86_64.tar.gz')) as archive:
        archived=set(archive.getnames())
        for member in archive:
            path = control/member.name
            if member.issym():
                if not path.is_symlink() or os.readlink(path) != member.linkname:
                    raise RuntimeError('Preserved control link changed')
            elif member.isfile():
                if '/__pycache__/' in member.name and member.name.endswith('.pyc'):
                    source_name=importlib.util.source_from_cache(member.name)
                    if source_name not in archived:
                        raise RuntimeError('Compiled control file has no verified source')
                    bytecode.append(path)
                    continue
                data = archive.extractfile(member).read()
                if member.name == 'serve/server.py':
                    data = transform(data.decode(), 'strata').encode()
                if not path.is_file() or hashlib.sha256(data).hexdigest() != sha(path):
                    raise RuntimeError('Preserved control file changed: '+member.name)
    for name, expected in manifest['sha256'].items():
        path = Path(name)
        for target, saved in directories.items():
            absolute = stage.parents[3]/path
            if absolute.is_relative_to(target):
                path = saved/absolute.relative_to(target)
                break
        else:
            path = stage.parents[3]/path
        if sha(path) != expected:
            raise RuntimeError('Preserved source/runtime hash changed: '+name)
    # Python can regenerate packaged bytecode while serving. Remove those derived
    # caches under the reservation so activation recompiles verified source bytes.
    for path in control.rglob('*.pyc'):
        if path not in bytecode:
            source_name=Path(importlib.util.source_from_cache(str(path))).relative_to(control).as_posix()
            if source_name not in archived:
                raise RuntimeError('Unexpected control bytecode without verified source')
            bytecode.append(path)
    return bytecode


def accept_tested_output_variance(updater, run):
    updater.recover()
    root = updater.root
    old = (updater.base/run).resolve()
    if old.parent != updater.base.resolve() or time.time()-old.stat().st_mtime > 86400:
        raise RuntimeError('Choose one completed local run from the last 24 hours')
    report = json.loads((old/'report.json').read_text())
    rows = [r for r in report['results'] if r['component']=='strata']
    if len(rows)!=1 or rows[0]['status']!='rejected-production-preserved':
        raise RuntimeError('Run is not a completed rejected Strata qualification')
    revision = rows[0]['revision']
    component = next(c for c in updater.policy['components'] if c['id']=='strata')
    journals = list((old/'strata').glob('activation-*/transaction.json'))
    if len(journals)!=1:
        raise RuntimeError('Ambiguous original transaction')
    journal = json.loads(journals[0].read_text())
    if journal['phase']!='rolled-back' or journal['revision']!=revision:
        raise RuntimeError('Original rollback is incomplete')
    from profile_catalog import load_catalog
    profiles = {p['id']:p for p in load_catalog()['profiles']}
    hardware = subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True)
    hardware += next(x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemTotal:'))
    candidate, gates = {}, {}
    for name in component['profiles']:
        baseline = json.loads((old/'strata/production'/name/'qualification.json').read_text())
        candidate[name] = json.loads((old/'strata/candidate'/name/'qualification.json').read_text())
        restored = json.loads((old/'strata/rollback-smoke'/name/'qualification.json').read_text())
        if not compare_short(restored, restored)['passed'] or not restored.get('recovery_verification'):
            raise RuntimeError('Restored production verification incomplete')
        settings = {k:v for k,v in profiles[name].items() if k in ('id','allocated_context','cli_args','selected_settings','worker_memory_gib','guardrails','kv_cache')}
        if candidate[name]['settings_sha256']!=fingerprint(settings) or candidate[name]['hardware_sha256']!=fingerprint(hardware):
            raise RuntimeError('Hardware or operational settings changed since test')
        gates[name] = reviewed_gate(baseline, candidate[name])
    if not any('acceptance' in g for g in gates.values()):
        raise RuntimeError('No reviewable one-token exception')
    stage = root/'runtimes/daily-update'/old.name/'strata'
    receipt = json.loads((stage/'build-receipt.json').read_text())
    if receipt['revision']!=revision:
        raise RuntimeError('Receipt revision mismatch')
    directories = {}
    for action in journal['actions']:
        target = Path(action['target'])
        if action['kind']=='file':
            if sha(target)!=action['old_sha']:
                raise RuntimeError('Production changed after rollback')
            item = next(i for i in receipt['files'] if i['target']==str(target))
            if sha(item['candidate'])!=action['new_sha'] or action['new_sha']!=item['sha256']:
                raise RuntimeError('Tested candidate file changed')
        else:
            directories[target] = target.with_name(target.name+'.rejected-'+journals[0].parent.name)
    manifest = json.loads((stage/'deepseek-unsloth-runtime.json').read_text())
    production_manifest=json.loads((root/'config/deepseek-unsloth-runtime.json').read_text())
    for name,expected in production_manifest['sha256'].items():
        if sha(root/name)!=expected:
            raise RuntimeError('Production runtime changed since recorded rollback: '+name)
    bytecode=verify_preserved_strata(stage, directories, manifest)
    validate_target_layout([i['target'] for i in receipt['files']]+[root/'config/daily-update-versions.json', root/'config/maintained-profiles.json'], directories)
    updater.run_dir = updater.base/('reviewed-'+str(time.time_ns()))
    updater.run_dir.mkdir(mode=0o700)
    write_json(updater.run_dir/'acceptance.json', {'original_run':old.name,'revision':revision,'gates':gates})
    # No new GPU workload: require already unloaded/idle and reserve atomically.
    if not updater.idle_reserve(manual=True,current_only=True):
        raise RuntimeError('Reviewed activation requires idle, unloaded serving')
    transaction = Transaction(updater.run_dir/'strata/activation-reviewed/transaction.json')
    try:
        for path in bytecode:
            path.unlink(missing_ok=True)
        transaction.begin('strata',revision,updater.owner)
        updater.state['pending']={'journal':str(transaction.path),'owner':updater.owner}
        write_json(updater.state_path,updater.state)
        for item in receipt['files']:
            transaction.file(item['target'],item['candidate'])
        for target, saved in directories.items():
            transaction.directory(target,saved)
        versions = json.loads((root/'config/daily-update-versions.json').read_text())
        versions['strata']={'source_commit':revision,'qualified_on':datetime.now().isoformat(timespec='seconds'),'acceptance':'Explicit one-token DeepSeek output variance; STRATA-0211-QUALIFICATION-20261105.md'}
        temp = updater.run_dir/'versions.json';write_json(temp,versions)
        transaction.file(root/'config/daily-update-versions.json',temp)
        catalog = json.loads((root/'config/maintained-profiles.json').read_text())
        for profile in catalog['profiles']:
            name=profile['id']
            if name not in candidate:continue
            if profile.get('current_configuration_benchmark'):
                profile.setdefault('short_tool_benchmark_history',[]).append(profile['current_configuration_benchmark'])
            row=candidate[name]
            profile['current_configuration_benchmark']={k:row[k] for k in ('prefill_tps','decode_tps','ttft_s','prompt_tokens','output_tokens','cached_tokens')}
            profile['current_configuration_benchmark'].update(date=datetime.now().date().isoformat(),context=row['context'],source='docs/STRATA-0211-QUALIFICATION-20261105.md',scope=gates[name]['scope'])
            profile['engine_refresh_qualification']={'source_commit':revision,'status':'passed short DSH; explicit manual acceptance of DeepSeek one-token variance','evidence':'docs/STRATA-0211-QUALIFICATION-20261105.md'}
            if 'qualified_engine_runtime' in profile:
                profile['qualified_engine_runtime'].pop('release',None)
                profile['qualified_engine_runtime'].update(source_commit=revision,evidence='docs/STRATA-0211-QUALIFICATION-20261105.md')
        temp=updater.run_dir/'catalog.json';write_json(temp,catalog)
        transaction.file(root/'config/maintained-profiles.json',temp)
        transaction.commit()
        updater.state.pop('pending',None)
        if updater.state.get('rejected',{}).get('strata')==revision:
            updater.state['rejected'].pop('strata')
        write_json(updater.state_path,updater.state)
    except BaseException:
        transaction.rollback()
        updater.state.pop('pending',None)
        write_json(updater.state_path,updater.state)
        raise
    finally:
        if not updater.state.get('pending'):
            from daily_engine_update import release_owner
            release_owner(updater.reservation,updater.owner)
            updater.state.pop('reservation_owner',None)
            write_json(updater.state_path,updater.state)
            updater.reconcile_router()
    updater.publish([{'component':'strata','revision':revision,'status':'promoted','gates':gates,
                      'candidate_metrics':{name:{k:row[k] for k in ('context','prefill_tps','decode_tps','ttft_s')} for name,row in candidate.items()}}])
    print(json.dumps({'strata':'promoted with explicit reviewed output variance','gates':gates}))
