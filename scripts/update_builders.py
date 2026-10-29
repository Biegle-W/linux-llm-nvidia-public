"""Isolated NVIDIA engine builds. No production changes occur here."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from update_transaction import sha, write_json


def run(command, log, cwd=None, env=None, timeout=10800):
    with Path(log).open('a') as f:
        subprocess.run([str(x) for x in command], cwd=cwd, env=env, stdout=f,
                       stderr=subprocess.STDOUT, check=True, timeout=timeout)


def upstream(component):
    text = subprocess.check_output(['git', 'ls-remote', component['upstream'], 'HEAD'], text=True, timeout=90)
    revision = text.split()[0]
    if not re.fullmatch('[0-9a-f]{40}', revision): raise RuntimeError('Invalid upstream revision')
    return revision


def canonical(root, profile):
    if profile == 'flash-next-strata':
        return Path.home() / '.local/state/strata/launch/qwen-flash-next.json'
    if profile == 'deepseek-strata':
        wrapper = json.loads((Path.home() / '.config/strata/profiles/deepseek-maya-s.json').read_text())
        if wrapper.get('overrides'): raise RuntimeError('Unreviewed Strata overrides')
        return Path(wrapper['source_config'])
    catalog = json.loads((root / 'config/maintained-profiles.json').read_text())
    selected = next(x for x in catalog['profiles'] if x['id'] == profile)
    return root / selected['runtime_selector']['path']


def build(root, component, revision, directory):
    root, directory = Path(root), Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    source, log = directory / 'source', directory / 'build.log'
    run(['git', 'clone', '--no-checkout', component['upstream'], source], log, timeout=600)
    run(['git', 'checkout', '--detach', revision], log, source, timeout=120)
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != revision:
        raise RuntimeError('Source revision mismatch')
    run(['git', 'submodule', 'update', '--init', '--recursive', '--depth', '1'], log, source, timeout=1800)
    kind = component['builder']; receipt = {'component': component['id'], 'revision': revision, 'files': [], 'directories': []}
    if kind == 'hyperqwen':
        env = directory / 'environment'
        run(['cp', '-a', '--reflink=auto', root / 'runtimes/env-hyperqwen', env], log, timeout=1800)
        py = env / 'bin/python'
        run([py, '-m', 'ensurepip', '--upgrade'], log, timeout=180)
        run([py, '-m', 'pip', 'install', '-r', source / 'docker/requirements.txt'], log, timeout=3600)
        package = Path(subprocess.check_output([str(py), '-c', 'import importlib.util; print(importlib.util.find_spec("vllm").origin)'], text=True).strip()).parent
        if not package.resolve().is_relative_to(env.resolve()):
            raise RuntimeError('Candidate package escapes copied environment')
        run(['bash', source / 'patches/apply.sh', package], log)
        # Keep production's separately qualified KVarN and launcher choices. A changed
        # patch layout fails rather than silently rebuilding different architecture.
        production_env = subprocess.check_output([str(root / 'runtimes/env-hyperqwen/bin/python'), '-c',
            'import importlib.metadata as m; print(m.version("vllm"))'], text=True).strip()
        receipt['production_vllm_version'] = production_env
        run([py, '-m', 'compileall', '-q', package], log)
        # New wheel console scripts name the staging interpreter. Activation moves
        # this environment to the canonical path, so retain valid shebangs there.
        old_prefix = ('#!' + str(env)).encode()
        for script in (env / 'bin').iterdir():
            if script.is_file() and not script.is_symlink():
                raw = script.read_bytes()
                if raw.startswith(old_prefix):
                    script.write_bytes(raw.replace(old_prefix, ('#!' + str(root / 'runtimes/env-hyperqwen')).encode(), 1))
        receipt['directories'].append({'target': str(root / 'runtimes/env-hyperqwen'), 'candidate': str(env)})
    elif kind == 'sglang':
        patch = root / 'scripts/patches/sglang-hetero-ct-w4a8-mtp.patch'
        run(['patch', '--batch', '--fuzz=0', '-p1', '-i', patch], log, source)
        run([sys.executable, '-m', 'compileall', '-q', source / 'python/sglang'], log)
        sys.path.insert(0, str(root / 'scripts'))
        from sglang_runtime import tree_digest
        manifest = json.loads((root / 'config/sglang-runtime.json').read_text())
        manifest.update(source_commit=revision, package_directory=str((source / 'python').relative_to(root)),
                        package_tree_sha256=tree_digest(source / 'python/sglang'),
                        cache_directory=str((directory / 'cache').relative_to(root)))
        candidate = directory / 'sglang-runtime.json'; write_json(candidate, manifest)
        receipt['files'].append({'target': str(root / 'config/sglang-runtime.json'), 'candidate': str(candidate)})
    else:
        base_model_sha = sha(source / 'src/ds4/ds4_model.cu') if kind == 'maya-ds4' else None
        if kind == 'maya-ds4':
            patch = root / 'patches/maya-ds4-file-cache-target.patch'
            run(['patch', '--batch', '--fuzz=0', '-p1', '-i', patch], log, source)
            test = directory / 'cache-test'
            run(['g++', '-O2', '-std=c++20', '-pthread', '-I' + str(source / 'src/ds4'),
                 root / 'tools/maya-file-cache-bound/test_cache_bound.cpp', '-o', test], log)
            run([test, directory], log)
        target = {'strata': 'strata', 'strata-ds4': 'strata-dsv41', 'maya': 'maya', 'maya-ds4': 'maya-ds4'}[kind]
        build_dir = directory / 'build'
        nvcc = root / 'runtimes/engine-tools/lib/python3.12/site-packages/nvidia/cu13/bin/nvcc'
        env = dict(os.environ, CC='gcc-13', CXX='g++-13', MAX_JOBS='2')
        args = ['cmake', '-S', source, '-B', build_dir, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release',
                '-DSTRATA_ENABLE_CUDA=ON', '-DCMAKE_CUDA_ARCHITECTURES=86', '-DSTRATA_BUILD_TESTS=ON',
                '-DCMAKE_CUDA_COMPILER=' + str(nvcc), '-DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-13']
        if kind == 'strata-ds4': args.append('-DSTRATA_BUILD_DSV41=ON')
        run(args, log, env=env)
        run(['cmake', '--build', build_dir, '--parallel', '2'], log, env=env)
        binary = build_dir / target
        if not binary.is_file(): raise RuntimeError('Missing candidate binary')
        cfg = json.loads(canonical(root, component['profiles'][0]).read_text())
        receipt['artifacts'] = [{'path':str(binary),'sha256':sha(binary)}]
        if kind == 'maya-ds4':
            # This selected controller intentionally verifies one fixed project
            # path. Preserve it with a durable binary+manifest transaction.
            receipt['files'].append({'target':cfg['exe'],'candidate':str(binary)})
        else:
            # Never overwrite shared Strata component-package files. Select this
            # immutable project-local build through the normal canonical preset.
            cfg['exe'] = str(binary)
        # Resolve new shared libraries from the same build as the new executable.
        # Model/cache/context arguments and the frontend remain unchanged.
        cfg['lib_dirs'] = [str(build_dir)] + [x for x in cfg.get('lib_dirs',[]) if x != str(build_dir)]
        candidate_cfg = directory / 'native-runtime-private.json'; write_json(candidate_cfg,cfg)
        receipt['files'].append({'target':str(canonical(root,component['profiles'][0])),'candidate':str(candidate_cfg)})
        receipt['ctest'] = str(build_dir)
        if kind == 'maya-ds4':
            manifest = json.loads((root / 'config/maya-cachebound-runtime.json').read_text())
            manifest.update(base_source_commit=revision, base_source_sha256=base_model_sha,
                            status='daily-update artifact; qualification recorded separately in the daily ledger')
            manifest['binary']['sha256'] = sha(binary)
            candidate = directory / 'maya-cachebound-runtime.json'; write_json(candidate, manifest)
            receipt['files'].append({'target': str(root / 'config/maya-cachebound-runtime.json'), 'candidate': str(candidate)})
    for action in receipt['files']:
        action['sha256'] = sha(action['candidate'])
        action['expected_old_sha256'] = sha(action['target'])
    write_json(directory / 'build-receipt.json', receipt)
    return receipt


def kernel_tests(receipt, directory):
    if 'ctest' not in receipt: return
    build_dir = receipt['ctest']; log = Path(directory) / 'kernel-tests.log'
    listing = subprocess.check_output(['ctest', '--test-dir', build_dir, '-N'], text=True, timeout=30)
    if not re.search(r'Total Tests:\s*[1-9]', listing) or not re.search(r'kernel|cuda|gpu|parity|attn|moe|rows|ds4',listing,re.I):
        raise RuntimeError('Native candidate has no registered correctness tests')
    for gpu in ('0', '1'):
        run(['ctest', '--test-dir', build_dir, '--output-on-failure', '--timeout', '120'],
            log, env=dict(os.environ, CUDA_VISIBLE_DEVICES=gpu), timeout=3600)
        if re.search(r'\*\*\*Skipped|Not Run|No tests were found|(?:^|\s)0% tests passed',log.read_text()):
            raise RuntimeError('Native correctness coverage was skipped/incomplete')
