#!/usr/bin/env python3
"""Install pinned, verified terminal packages locally; never mutate system packages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT / 'config/terminal-runtime.json').read_text())
    target = ROOT / 'runtimes/visible-terminal'
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='llm-terminal-') as temporary:
        temporary = Path(temporary)
        for package in config['packages']:
            subprocess.run(['apt-get', 'download', package['package'] + '=' + package['version']],
                           cwd=temporary, check=True)
            archives = list(temporary.glob(package['package'] + '_*.deb'))
            if len(archives) != 1 or hashlib.sha256(archives[0].read_bytes()).hexdigest() != package['sha256']:
                raise RuntimeError('Terminal package SHA256 mismatch')
            subprocess.run(['dpkg-deb', '-x', str(archives[0]), str(target)], check=True)
    for path in target.rglob('*'):
        if path.is_file() and not path.is_symlink():
            path.chmod(path.stat().st_mode & 0o777)
    for relative, expected in config['sha256'].items():
        path = ROOT / relative
        if not path.resolve().is_relative_to(ROOT.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Installed terminal runtime hash mismatch')
    env = dict(os.environ, LD_LIBRARY_PATH=str(ROOT / config['library_directory']))
    libraries = subprocess.check_output(['ldd', str(ROOT / config['binary'])], text=True, env=env)
    if 'not found' in libraries:
        raise RuntimeError('Terminal runtime has unresolved dependencies')
    print('Verified project-local minimized terminal runtime; system packages unchanged.')


if __name__ == '__main__':
    main()
