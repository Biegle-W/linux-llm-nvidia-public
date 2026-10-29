#!/usr/bin/env python3
"""Build an isolated Linux Maya cache-target candidate; never overwrite the installed runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_MODEL_SHA256 = '96a5e7ccb71803ebd9e05eb9ac401b5404eec96808055e4acf2f771458232024'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'linux':
        raise SystemExit('This candidate is for Linux only.')
    native = ROOT / 'runtimes/project-maya'
    original = native / 'src/ds4/ds4_model.cu'
    if digest(original) != BASE_MODEL_SHA256:
        raise SystemExit('Maya source changed; review/rebase the patch before building.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if subprocess.check_output(['stat', '-f', '-c', '%T', str(output)], text=True).strip() == 'tmpfs':
        raise SystemExit('Use disk-backed output storage for the clean-file eviction test.')
    copied = output / 'src/ds4'
    copied.mkdir(parents=True)
    shutil.copy2(original, copied / original.name)
    patch = ROOT / 'patches/maya-ds4-file-cache-target.patch'
    build = native / 'build'
    with (output / 'build.log').open('w') as log:
        def run(command, cwd=None):
            subprocess.run(command, cwd=cwd, check=True, stdout=log, stderr=subprocess.STDOUT)
        run(['patch', '--batch', '-p1', '-d', str(output), '-i', str(patch)])
        test = output / 'test_cache_bound'
        run(['g++', '-O2', '-std=c++20', '-pthread', '-I' + str(copied),
             str(ROOT / 'tools/maya-file-cache-bound/test_cache_bound.cpp'), '-o', str(test)])
        run([str(test), str(output)])
        commands = subprocess.check_output(['ninja', '-C', str(build), '-t', 'commands', 'maya-ds4'], text=True).splitlines()
        compile_command = next(c for c in commands if ' -c ' in c and '/ds4_model.cu' in c)
        link_command = next(c for c in reversed(commands) if ' -o maya-ds4 ' in c)
        compile_args = shlex.split(compile_command)
        old_object = compile_args[compile_args.index('-o') + 1]
        new_object = output / 'candidate.o'
        compile_args = [x.replace(str(original), str(copied / original.name)).replace(old_object, str(new_object))
                        for x in compile_args]
        compile_args += ['-I' + str(copied), '-I' + str(native / 'src/ds4')]
        if Path(compile_args[0]).name != 'nvcc' or any(x in compile_args for x in ['&&', ';']):
            raise RuntimeError('Unsupported compile command; review the local build configuration.')
        run(compile_args, build)
        link_args = shlex.split(link_command)
        if link_args[:2] == [':', '&&']: link_args = link_args[2:]
        if link_args[-2:] == ['&&', ':']: link_args = link_args[:-2]
        if Path(link_args[0]).name not in ['c++', 'g++'] or any(x in link_args for x in ['&&', ';']):
            raise RuntimeError('Unsupported link command; review the local build configuration.')
        link_args = [str(new_object) if x == old_object else x.replace(
            '--dependency-file=CMakeFiles/maya-ds4.dir/link.d', '--dependency-file=' + str(output / 'candidate-link.d'))
            for x in link_args]
        binary = output / 'maya-ds4'
        link_args[link_args.index('-o') + 1] = str(binary)
        run(link_args, build)
    receipt = {'base_source_sha256': BASE_MODEL_SHA256,
               'patched_source_sha256': digest(copied / original.name),
               'controller_header_sha256': digest(copied / 'bounded_file_cache.hpp'),
               'patch_sha256': digest(patch), 'binary_sha256': digest(binary),
               'clean_file_eviction_and_concurrent_read_test': 'passed',
               'production_source_unchanged': digest(original) == BASE_MODEL_SHA256}
    (output / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if not receipt['production_source_unchanged']:
        raise RuntimeError('Production source changed during this build; inspect before proceeding.')
    print('Candidate built and CPU-tested; installation/selection requires separate qualification.')
    print(binary)


if __name__ == '__main__':
    main()
