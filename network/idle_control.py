"""Owned idle reservations shared with native frontend idle adapters."""
import json
import os
from pathlib import Path
import time


def claim(path, profile):
    owner = {'owner': 'router-idle', 'pid': os.getpid(),
             'nonce': time.monotonic_ns(), 'profile': profile}
    try:
        with Path(path).open('x') as stream:
            json.dump(owner, stream)
    except FileExistsError:
        return None
    return owner


def release(path, owner):
    if owner is None:
        return
    try:
        if json.loads(Path(path).read_text()) == owner:
            Path(path).unlink()
    except (OSError, ValueError):
        pass


def owned_native_idle(path, cgroup_reader=None):
    """Do not mistake another task's reservation for an idle teardown."""
    try:
        value = json.loads(Path(path).read_text())
        if value.get('owner') != 'native-idle' or type(value.get('pid')) is not int:
            return False
        text = (cgroup_reader(value['pid']) if cgroup_reader else
                (Path('/proc') / str(value['pid']) / 'cgroup').read_text())
        return any(line.startswith('0::') and line.endswith('/llm-router-worker.service')
                   for line in text.splitlines())
    except (OSError, ValueError, KeyError):
        return False
