"""Durable candidate activation. Uncommitted changes recover to production."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as f:
        os.fchmod(f.fileno(), 0o600)
        json.dump(data, f, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(path.parent)


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def replace_file(source, target, mode):
    target = Path(target)
    tmp = target.with_name(target.name + '.update-tmp')
    with Path(source).open('rb') as src, tmp.open('wb') as out:
        shutil.copyfileobj(src, out)
        os.fchmod(out.fileno(), mode); out.flush(); os.fsync(out.fileno())
    os.replace(tmp, target); fsync_dir(target.parent)


class Transaction:
    def __init__(self, journal):
        self.path = Path(journal)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {'phase': 'empty', 'actions': []}

    def begin(self, component, revision, owner):
        if self.data['phase'] not in ('empty', 'committed', 'rolled-back'):
            raise RuntimeError('Unrecovered provisional runtime')
        self.data = {'phase': 'prepared', 'component': component, 'revision': revision, 'owner': owner, 'started_unix':time.time(), 'actions': []}
        write_json(self.path, self.data)

    def file(self, target, candidate):
        target, candidate = Path(target).resolve(), Path(candidate).resolve()
        backup = self.path.parent / 'preimages' / str(len(self.data['actions']))
        backup.parent.mkdir(mode=0o700, exist_ok=True)
        shutil.copy2(target, backup)
        with backup.open('rb') as f: os.fsync(f.fileno())
        mode = stat.S_IMODE(target.stat().st_mode)
        action = {'kind': 'file', 'target': str(target), 'backup': str(backup),
                  'old_sha': sha(target), 'new_sha': sha(candidate), 'mode': mode}
        self.data['actions'].append(action); write_json(self.path, self.data)
        replace_file(candidate, target, mode)

    def directory(self, target, candidate):
        target, candidate = Path(target), Path(candidate)
        if target.is_symlink() or candidate.is_symlink():
            raise RuntimeError('Environment directory must not be a symlink')
        backup = target.with_name(target.name + '.before-' + self.path.parent.name)
        if backup.exists(): raise RuntimeError('Environment preimage already exists')
        action = {'kind': 'directory', 'target': str(target), 'backup': str(backup), 'candidate': str(candidate)}
        self.data['actions'].append(action); write_json(self.path, self.data)
        os.rename(target, backup); fsync_dir(target.parent)
        os.rename(candidate, target); fsync_dir(target.parent)

    def commit(self):
        self.data['phase'] = 'committed'; write_json(self.path, self.data)

    def rollback(self):
        if self.data['phase'] in ('empty', 'committed', 'rolled-back'): return
        for action in reversed(self.data['actions']):
            target, backup = Path(action['target']), Path(action['backup'])
            if action['kind'] == 'file':
                if not backup.is_file() or sha(backup) != action['old_sha']:
                    raise RuntimeError('Rollback preimage changed')
                if target.exists() and sha(target) not in (action['old_sha'], action['new_sha']):
                    raise RuntimeError('External runtime edit preserved; manual recovery required')
                replace_file(backup, target, action['mode'])
            elif backup.exists():
                failed = target.with_name(target.name + '.rejected-' + self.path.parent.name)
                if target.exists():
                    if failed.exists(): raise RuntimeError('Rejected runtime already preserved')
                    os.rename(target, failed)
                os.rename(backup, target); fsync_dir(target.parent)
        self.data['phase'] = 'rolled-back'; write_json(self.path, self.data)
