#!/usr/bin/env python3
"""Track model weights on both drives: what each file is used by, and what nothing uses.

Read-only. A weight file counts as used when one of these claims it:
  * a router entry in config/maintained-profiles.json (storage.checkpoint_directory),
  * a ComfyUI image entry (config/comfy-runtime.json) or video entry
    (config/comfy-video-entries.json -> config/comfy-video-trial.json),
  * an extra reference in config/weights-inventory.json whose owner still exists
    (helper files such as MTP heads, packs, vision encoders, updater inputs).
Everything else under the tracked roots is reported as unused (or as a duplicate of a used
file when size and sampled content match), unless config/weights-inventory.json lists it under
"kept" with a reason. Claimed paths that are missing on disk are reported too.

Usage:
  python3 scripts/weights_tracker.py            # print report, write data/weights-tracker/
  python3 scripts/weights_tracker.py --json     # print the JSON report
  python3 scripts/weights_tracker.py --fail-on-unused   # exit 1 if anything unused/missing
  python3 scripts/weights_tracker.py --install-timer    # daily user timer (04:30)
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GiB = 1024 ** 3
SAMPLE = 16 * 1024 * 1024


def load(rel):
    return json.loads((ROOT / rel).read_text())


def absolute(path):
    p = Path(path)
    return Path(os.path.normpath(p if p.is_absolute() else ROOT / p))


def resolve(path):
    return Path(os.path.realpath(absolute(path)))


def mount_point(cfg):
    """SATA mount from the owner-only storage record (keeps the user name out of tracked config)."""
    rec = ROOT / cfg.get('sata_mount_record', 'data/storage-mount.json')
    try:
        return Path(json.loads(rec.read_text())['mountpoint'])
    except (OSError, KeyError, ValueError):
        return None


def roots(cfg):
    """(top, extensions_only) per configured root; missing SATA mount is skipped."""
    out = []
    for r in cfg['roots']:
        if 'repo' in r:
            out.append((ROOT / r['repo'], r.get('extensions_only', False)))
        else:
            mp = mount_point(cfg)
            if mp is not None:
                out.append((mp / r['mount_relative'], r.get('extensions_only', False)))
    return out


def claims(cfg):
    """Return (claims, owners, problems): claims = list of (resolved path, owner, why)."""
    out, problems = [], []
    registry = load('config/maintained-profiles.json')['profiles']
    owners = {'router:' + p['id'] for p in registry}
    for p in registry:
        storage = p.get('storage') or {}
        d = storage.get('checkpoint_directory')
        if d:
            out.append((d, 'router:' + p['id'], 'registry checkpoint_directory'))
    comfy = load('config/comfy-runtime.json')
    for m in comfy.get('models', []):
        owners.add('comfy:' + m['id'])
        for f in m.get('files', []):
            out.append((Path(comfy['checkpoint_directory']) / f['file'], 'comfy:' + m['id'], 'config/comfy-runtime.json'))
    entries = load('config/comfy-video-entries.json')['models']
    trial = load('config/comfy-video-trial.json')
    by_trial = {m['id']: m for m in trial.get('models', [])}
    for e in entries:
        owners.add('comfy-video:' + e['id'])
        t = by_trial.get(e.get('trial_id'))
        if t is None:
            problems.append('comfy video entry %s has no trial model %s' % (e['id'], e.get('trial_id')))
            continue
        for f in t.get('files', []):
            out.append((Path(trial['checkpoint_directory']) / f['file'], 'comfy-video:' + e['id'], 'config/comfy-video-trial.json'))
    for x in cfg.get('extra_references', []):
        owner = x['owner']
        if owner.startswith('updater:'):
            src, _, needle = owner[len('updater:'):].partition('#')
            alive = needle and needle in (ROOT / src).read_text() if (ROOT / src).is_file() else False
            if alive:
                owners.add(owner)
        elif owner not in owners:
            problems.append('extra reference %s names retired owner %s' % (x['path'], owner))
            continue
        if owner.startswith('updater:') and owner not in owners:
            problems.append('extra reference %s: updater no longer mentions %s' % (x['path'], owner))
            continue
        out.append((x['path'], owner, x['why']))
    return [(absolute(c), resolve(c), o, w) for c, o, w in out], owners, problems


def is_weight(path, size, cfg, extensions_only=False):
    if path.suffix.lower() in cfg['weight_extensions'] and size >= cfg['min_weight_bytes']:
        return True
    return not extensions_only and size >= cfg['min_bytes']


def drive_of(real, cfg):
    mp = mount_point(cfg)
    return 'SATA' if mp is not None and (real == mp or mp in real.parents) else 'NVMe'


def scan(cfg):
    """One record per inode, with every path it was reached by (symlinks, hardlinks)."""
    by_inode = {}
    for top, extensions_only in roots(cfg):
        if not top.exists():
            continue
        visited = set()
        for dirpath, dirnames, filenames in os.walk(top, followlinks=True):
            real_dir = os.path.realpath(dirpath)
            if real_dir in visited:  # a symlink loop or a second link to the same folder
                dirnames[:] = []; continue
            visited.add(real_dir)
            for name in filenames:
                p = Path(dirpath) / name
                try:
                    st = p.stat()
                except OSError:
                    continue
                if not is_weight(p, st.st_size, cfg, extensions_only):
                    continue
                real = Path(os.path.realpath(p))
                f = by_inode.setdefault((st.st_dev, st.st_ino), {'path': real, 'size': st.st_size, 'drive': drive_of(real, cfg), 'aliases': set()})
                f['aliases'].update({Path(os.path.normpath(p)), real})
    return list(by_inode.values())


_hashes = {}


def sample_hash(path):
    if path in _hashes:
        return _hashes[path]
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        h.update(fh.read(SAMPLE))
        size = os.fstat(fh.fileno()).st_size
        if size > 2 * SAMPLE:
            fh.seek(size - SAMPLE); h.update(fh.read(SAMPLE))
    _hashes[path] = h.hexdigest()
    return _hashes[path]


def under(path, claim):
    return path == claim or claim in path.parents


def matches(f, lit, real):
    return any(under(a, lit) or under(a, real) for a in f['aliases'])


def drive_usage(cfg):
    rows = []
    mp = mount_point(cfg)
    for name, where in (('NVMe', Path('/')), ('SATA', mp)):
        if where is None or not where.exists():
            rows.append({'drive': name, 'mounted': False}); continue
        st = os.statvfs(where)
        total, free = st.f_blocks * st.f_frsize, st.f_bavail * st.f_frsize
        rows.append({'drive': name, 'mounted': True, 'total': total, 'used': total - st.f_bfree * st.f_frsize, 'available': free})
    return rows


def build_report(cfg):
    claimed, owners, problems = claims(cfg)
    files = scan(cfg)
    kept = [(absolute(k['path']) if 'path' in k else mount_point(cfg) / k['mount_relative'], k['why']) for k in cfg.get('kept', [])]
    kept = [(k, Path(os.path.realpath(k)), why) for k, why in kept]
    used_by_size = {}
    for f in files:
        f['owners'] = sorted({o for lit, real, o, _ in claimed if matches(f, lit, real)})
        f['kept'] = next((why for lit, real, why in kept if matches(f, lit, real)), None)
        if f['owners']:
            used_by_size.setdefault(f['size'], []).append(f)
    for f in files:
        if f['owners'] or f['kept']:
            f['status'] = 'used' if f['owners'] else 'kept'
            continue
        f['status'], f['duplicate_of'] = 'unused', None
        for g in used_by_size.get(f['size'], []):
            if sample_hash(f['path']) == sample_hash(g['path']):
                f['status'], f['duplicate_of'] = 'duplicate', str(g['path']); break
    missing = sorted({(str(lit), o) for lit, real, o, _ in claimed if not real.exists()})
    summary = {}
    for f in files:
        s = summary.setdefault(f['drive'], {}).setdefault(f['status'], [0, 0])
        s[0] += 1; s[1] += f['size']
    return {
        'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'drives': drive_usage(cfg),
        'summary': summary,
        'unused': [{'path': str(f['path']), 'drive': f['drive'], 'bytes': f['size'], 'status': f['status'], 'duplicate_of': f.get('duplicate_of')}
                   for f in sorted(files, key=lambda f: -f['size']) if f['status'] in ('unused', 'duplicate')],
        'kept': [{'path': str(f['path']), 'bytes': f['size'], 'why': f['kept']} for f in files if f['status'] == 'kept'],
        'used': [{'path': str(f['path']), 'drive': f['drive'], 'bytes': f['size'], 'owners': f['owners']} for f in sorted(files, key=lambda f: str(f['path'])) if f['status'] == 'used'],
        'missing': [{'path': p, 'owner': o} for p, o in missing],
        'problems': problems,
    }


def gb(n):
    return '%.1f GB' % (n / 1e9)


def markdown(r):
    lines = ['# Weights tracker report', '', 'Generated %s by `scripts/weights_tracker.py` (read-only).' % r['time'], '',
             '| Drive | Size | Used | Available | Used weights | Unused / duplicate weights |', '|---|---:|---:|---:|---:|---:|']
    for d in r['drives']:
        s = r['summary'].get(d['drive'], {})
        u = s.get('used', [0, 0]); x = [a + b for a, b in zip(s.get('unused', [0, 0]), s.get('duplicate', [0, 0]))]
        if not d.get('mounted'):
            lines.append('| %s | not mounted | | | | |' % d['drive']); continue
        lines.append('| %s | %s | %s (%d%%) | %s | %s (%d files) | %s (%d files) |' % (
            d['drive'], gb(d['total']), gb(d['used']), round(100 * d['used'] / d['total']), gb(d['available']), gb(u[1]), u[0], gb(x[1]), x[0]))
    lines += ['', '## Unused or duplicate weights', '']
    lines += ['- %s `%s` — %s%s' % (gb(u['bytes']), u['path'], u['status'], (' of `%s`' % u['duplicate_of']) if u['duplicate_of'] else '') for u in r['unused']] or ['None.']
    if r['kept']:
        lines += ['', '## Kept on purpose', ''] + ['- %s `%s` — %s' % (gb(k['bytes']), k['path'], k['why']) for k in r['kept']]
    lines += ['', '## Missing claimed paths', ''] + (['- `%s` (%s)' % (m['path'], m['owner']) for m in r['missing']] or ['None.'])
    if r['problems']:
        lines += ['', '## Config problems', ''] + ['- ' + p for p in r['problems']]
    lines += ['', '## Used weights', '']
    lines += ['- %s `%s` — %s' % (gb(u['bytes']), u['path'], ', '.join(u['owners'])) for u in r['used']]
    return '\n'.join(lines) + '\n'


def install_timer():
    unit_dir = Path.home() / '.config/systemd/user'
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / 'nvidia-weights-tracker.service').write_text(
        '[Unit]\nDescription=Report unused model weights on the NVIDIA server (read-only)\n\n[Service]\nType=oneshot\n'
        'ExecStart=/usr/bin/python3 %s\nNice=10\nIOSchedulingClass=idle\n' % (ROOT / 'scripts/weights_tracker.py'))
    (unit_dir / 'nvidia-weights-tracker.timer').write_text(
        '[Unit]\nDescription=Daily unused-weights report\n\n[Timer]\nOnCalendar=*-*-* 04:30:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n')
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', '--user', 'enable', '--now', 'nvidia-weights-tracker.timer'], check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--fail-on-unused', action='store_true')
    ap.add_argument('--no-write', action='store_true')
    ap.add_argument('--install-timer', action='store_true')
    a = ap.parse_args(argv)
    if a.install_timer:
        install_timer(); return 0
    cfg = load('config/weights-inventory.json')
    r = build_report(cfg)
    md = markdown(r)
    if not a.no_write:
        out = ROOT / 'data/weights-tracker'; out.mkdir(parents=True, exist_ok=True)
        prev = json.loads((out / 'latest.json').read_text()) if (out / 'latest.json').exists() else None
        (out / 'latest.json').write_text(json.dumps(r, indent=1) + '\n')
        (out / 'latest.md').write_text(md)
        new = sorted({u['path'] for u in r['unused']} - {u['path'] for u in (prev or {}).get('unused', [])}) if prev else []
        with open(out / 'history.jsonl', 'a') as h:
            h.write(json.dumps({'time': r['time'], 'unused_bytes': sum(u['bytes'] for u in r['unused']),
                                'unused_files': len(r['unused']), 'missing': len(r['missing']), 'new_unused': new}) + '\n')
    print(json.dumps(r, indent=1) if a.json else md, end='')
    return 1 if a.fail_on_unused and (r['unused'] or r['missing'] or r['problems']) else 0


if __name__ == '__main__':
    sys.exit(main())
