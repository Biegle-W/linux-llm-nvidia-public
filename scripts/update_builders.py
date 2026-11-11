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


def latest_release(component):
    import urllib.request
    repo=component['upstream'].removeprefix('https://github.com/').removesuffix('.git')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise RuntimeError('Unexpected release repository')
    request=urllib.request.Request('https://api.github.com/repos/'+repo+'/releases/latest',headers={'Accept':'application/vnd.github+json','User-Agent':'NVIDIA-engine-maintenance'})
    with urllib.request.urlopen(request,timeout=30)as response:release=json.load(response)
    if release.get('draft') or release.get('prerelease') or not release.get('tag_name'):raise RuntimeError('No stable release')
    return release


def upstream(component):
    ref='HEAD'
    if component.get('channel')=='stable':
        ref='refs/tags/'+latest_release(component)['tag_name']
        text=subprocess.check_output(['git','ls-remote',component['upstream'],ref,ref+'^{}'],text=True,timeout=90)
        lines=text.splitlines();peeled=[line for line in lines if line.endswith('^{}')]
        revision=(peeled or lines)[0].split()[0] if lines else ''
    else:
        text=subprocess.check_output(['git','ls-remote','--symref',component['upstream'],'HEAD'],text=True,timeout=90)
        expected=component.get('default_branch')
        if expected and 'ref: refs/heads/'+expected+'\tHEAD' not in text:raise RuntimeError('Default fork branch changed; patch review required')
        revision=next((line.split()[0] for line in text.splitlines()if not line.startswith('ref:')),'')
    if not re.fullmatch('[0-9a-f]{40}',revision):raise RuntimeError('Invalid upstream revision')
    return revision


def canonical(root, profile):
    if profile == 'flash-next-strata':
        return Path.home() / '.local/state/strata/launch/qwen-flash-next.json'
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
        run([py, '-m', 'pip', 'install', '--upgrade', '-r', source / 'docker/requirements.txt'], log, timeout=3600)
        package = Path(subprocess.check_output([str(py), '-c', 'import importlib.util; print(importlib.util.find_spec("vllm").origin)'], text=True).strip()).parent
        if not package.resolve().is_relative_to(env.resolve()):
            raise RuntimeError('Candidate package escapes copied environment')
        import shutil
        wheel_version=subprocess.check_output([str(py),'-c','import importlib.metadata as m; print(m.version("vllm"))'],text=True).strip()
        # Copied patched files absent from a new wheel would survive pip uninstall.
        shutil.rmtree(package)
        run([py,'-m','pip','install','--force-reinstall','--no-deps','vllm=='+wheel_version],log,timeout=3600)
        run(['bash', source / 'patches/apply.sh', package], log)
        run(['bash', source / 'patches/apply.sh', '--kvarn', package], log)
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
        patch = root / json.loads((root/'config/sglang-runtime.json').read_text())['patch']
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
    elif kind in ('maya-pair','llamacpp','strata-signed'):
        from update_native_builders import prepare
        prepare(root,component,revision,directory,source,log,receipt)
    else:
        raise RuntimeError('Retired builder; migrate to current grouped runtime adapter')
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
