#!/usr/bin/env python3
"""Export reviewed reference files to the matching public checkout; never push history."""
import argparse
from pathlib import Path
import re
import subprocess

FILES = (
    'README.md', '.gitignore', 'docs/MIGRATION-HANDOFF.md', 'docs/REPOSITORY-MAP.md', 'docs/LOCAL-SETUP.md',
    'docs/VALIDATION-20261026.md', 'docs/BENCHMARK-20261026.md',
    'scripts/build_native_llama.sh', 'scripts/check_local_api.py',
    'scripts/start_model.sh', 'scripts/native_linux_gpu_unlock.py',
    'scripts/test_native_linux_gpu_unlock.py', 'docs/UNLOCK-SETUP-20261026.md', 'scripts/sync_public.py', 'docs/PUBLIC-SYNC.md',
)
BLOCK = re.compile(r'/(?:home|Users)/[^/\s]+|GPU-[0-9a-fA-F-]{16,}|'
                   r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|'
                   r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|'
                   r'[A-Za-z0-9._%+-]+@(?!example\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    target = args.checkout.resolve()
    origin = subprocess.check_output(['git', '-C', str(target), 'remote', 'get-url', 'origin'], text=True).strip()
    if origin not in ('https://github.com/Biegle-W/linux-llm-nvidia-public.git',
                      'git@github.com:Biegle-W/linux-llm-nvidia-public.git'):
        raise SystemExit('Refusing export to an unexpected repository.')
    if subprocess.check_output(['git', '-C', str(target), 'status', '--porcelain'], text=True).strip():
        raise SystemExit('Public checkout must be clean before export.')
    exports = {}
    for relative in FILES:
        content = (source / relative).read_text()
        if relative == 'README.md':
            content = content.replace('# Linux LLM NVIDIA\n', '# Linux LLM NVIDIA — public reference\n', 1)
        if BLOCK.search(content.replace('git@github.com:', '')):
            raise SystemExit(f'Privacy check failed for {relative}; review locally.')
        exports[relative] = content
    for relative, content in exports.items():
        destination = target / relative
        if destination.is_symlink() or any(parent.is_symlink() for parent in destination.parents if parent != target.parent):
            raise SystemExit(f'Refusing symlink destination: {relative}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)
        destination.chmod((source / relative).stat().st_mode & 0o777)
    print(f'Exported {len(exports)} reviewed files. Review git diff before committing and pushing.')


if __name__ == '__main__':
    main()
