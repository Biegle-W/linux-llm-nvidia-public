#!/usr/bin/env python3
"""Stage a pinned source snapshot and review matched evidence; never activate it."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')
    path.chmod(0o600)


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args])


def extract_snapshot(raw, destination):
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        members = archive.getmembers()
        for member in members:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or member.isdev() or member.islnk():
                raise ValueError('Unsafe archive entry')
            if member.issym():
                resolved = (destination / name.parent / member.linkname).resolve()
                if not resolved.is_relative_to(destination.resolve()):
                    raise ValueError('Source symlink escapes the candidate')
        archive.extractall(destination, members=members, filter='data')


def stage(source, revision, profile_id, name, fixtures, root=ROOT):
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', name):
        raise ValueError('Use a short lowercase candidate name')
    catalog_path = root / 'config/maintained-profiles.json'
    catalog = json.loads(catalog_path.read_text())
    profile = next(p for p in catalog['profiles'] if p['id'] == profile_id)
    # An explicit immutable commit is required, rather than a moving branch name.
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Supply the reviewed full 40-character source commit')
    commit = git(source, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    if commit != revision:
        raise ValueError('Commit resolution mismatch')
    fixture_data = [(Path(p).name, Path(p).read_bytes()) for p in fixtures]
    if not fixture_data or len({n for n, _ in fixture_data}) != len(fixture_data):
        raise ValueError('Provide uniquely named, saved code/prose request fixtures')
    snapshot = git(source, 'archive', '--format=tar', revision)
    target = root / 'data/engine-candidates' / name
    target.mkdir(parents=True, exist_ok=False, mode=0o700)
    try:
        (target / 'source').mkdir()
        extract_snapshot(snapshot, target / 'source')
        (target / 'fixtures').mkdir()
        fixture_hashes = {}
        for filename, raw in fixture_data:
            path = target / 'fixtures' / filename
            path.write_bytes(raw)
            path.chmod(0o600)
            fixture_hashes[filename] = hashlib.sha256(raw).hexdigest()
        manifest = dict(schema=1, created_unix=time.time(), status='staged-unbuilt',
                        name=name, profile_id=profile_id, source_commit=commit,
                        source_archive_sha256=hashlib.sha256(snapshot).hexdigest(),
                        source_path=str(Path(source).resolve()),
                        catalog_sha256=digest(catalog_path), profile=profile,
                        fixtures=fixture_hashes,
                        scope='Manual isolated build and guarded evaluation; no activation')
        write_json(target / 'manifest.json', manifest)
        return target
    except Exception:
        # Retain partial evidence for review rather than silently reusing a name.
        write_json(target / 'FAILED.json', {'stage': 'source-staging', 'time': time.time()})
        raise


def evidence(path):
    data = json.loads(path.read_text())
    for key in ['profile_id', 'source_commit', 'model_quant_fingerprint', 'settings_sha256',
                'hardware_fingerprint', 'fixture_sha256', 'context', 'repetitions',
                'input_tokens', 'output_tokens', 'prefill_tps', 'ttft_s', 'decode_tps',
                'quality', 'resources', 'raw_evidence']:
        if key not in data:
            raise ValueError('Missing evidence field: ' + key)
    # Raw records must exist beside/below the evidence file and match their hashes.
    if not data['raw_evidence']:
        raise ValueError('Raw evidence is required')
    for relative, expected in data['raw_evidence'].items():
        raw = (path.parent / relative).resolve()
        if not raw.is_relative_to(path.parent.resolve()) or digest(raw) != expected:
            raise ValueError('Raw evidence missing, outside evidence folder or changed')
    return data


def evaluate(stage_path, baseline_path, candidate_path):
    manifest = json.loads((stage_path / 'manifest.json').read_text())
    baseline, candidate = evidence(baseline_path), evidence(candidate_path)
    reasons = []
    for key in ['profile_id', 'model_quant_fingerprint', 'hardware_fingerprint',
                'fixture_sha256', 'input_tokens', 'output_tokens']:
        if baseline[key] != candidate[key]:
            reasons.append('Unmatched ' + key)
    if candidate['profile_id'] != manifest['profile_id'] or candidate['source_commit'] != manifest['source_commit']:
        reasons.append('Candidate does not match staged source/profile')
    expected_fixtures = set(manifest['fixtures'].values())
    if not expected_fixtures.issubset(set(candidate['fixture_sha256'].values())):
        reasons.append('Saved staged fixtures were not all measured')
    for label, row in [('baseline', baseline), ('candidate', candidate)]:
        if row['repetitions'] < 3 or row['output_tokens'] < 128:
            reasons.append(label + ': need at least three requests and 128 output tokens')
        if not all(isinstance(row[k], (float, int)) and row[k] > 0
                   for k in ['prefill_tps', 'ttft_s', 'decode_tps']):
            reasons.append(label + ': invalid timing data')
        q, r = row['quality'], row['resources']
        if not all(q.get(k) is True for k in ['json', 'arithmetic', 'near_window_retrieval']):
            reasons.append(label + ': quality qualification incomplete')
        if row.get('vision_enabled') and q.get('image') is not True:
            reasons.append(label + ': image qualification incomplete')
        if not .85 * row['context'] <= q.get('retrieval_input_tokens', 0) < row['context'] - 128:
            reasons.append(label + ': retrieval did not qualify the allocated window')
        if not all(r.get(k) is True for k in
                   ['owned_worker', 'ram_limits', 'host_floor', 'gpu_headroom', 'thermal', 'active_swap_guard']):
            reasons.append(label + ': resource proof incomplete')
        if r.get('guard_stops') != 0:
            reasons.append(label + ': guard stops occurred')
    if candidate['context'] < baseline['context']:
        reasons.append('Candidate reduces context')
    for metric, higher in [('prefill_tps', True), ('ttft_s', False), ('decode_tps', True)]:
        if (candidate[metric] < baseline[metric]) if higher else (candidate[metric] > baseline[metric]):
            reasons.append('Speed regression: ' + metric)
    result = dict(schema=1, reviewed_unix=time.time(),
                  baseline_sha256=digest(baseline_path), candidate_sha256=digest(candidate_path),
                  accepted_for_manual_review=not reasons, reasons=reasons,
                  activation='Not performed; review hashes, raw records and deployment diff separately')
    output = stage_path / ('review-' + str(time.time_ns()) + '.json')
    write_json(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('stage')
    create.add_argument('--source', type=Path, required=True)
    create.add_argument('--revision', required=True)
    create.add_argument('--profile', required=True)
    create.add_argument('--name', required=True)
    create.add_argument('--fixture', type=Path, action='append', required=True)
    review = commands.add_parser('evaluate')
    review.add_argument('stage', type=Path)
    review.add_argument('--baseline', type=Path, required=True)
    review.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'stage':
        print(stage(args.source, args.revision, args.profile, args.name, args.fixture))
    else:
        result = evaluate(args.stage, args.baseline, args.candidate)
        print(json.dumps(result, indent=2))
        if not result['accepted_for_manual_review']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
