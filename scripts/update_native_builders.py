"""Current grouped native adapters; stage only, reuse every model weight."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
from update_transaction import sha,write_json
from native_idle_policy import transform


def cuda_options(root):
    cuda=root/'runtimes/engine-tools/lib/python3.12/site-packages/nvidia/cu13'
    return ['-DCUDAToolkit_ROOT='+str(cuda),'-DCMAKE_CUDA_COMPILER='+str(cuda/'bin/nvcc'),
            '-DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-13','-DCMAKE_CUDA_ARCHITECTURES=86',
            '-DCUDA_cudart_LIBRARY='+str(cuda/'lib/libcudart.so'),
            '-DCUDA_cublas_LIBRARY='+str(cuda/'lib/libcublas.so'),
            '-DCUDA_cublasLt_LIBRARY='+str(cuda/'lib/libcublasLt.so'),
            '-DCMAKE_BUILD_RPATH_USE_ORIGIN=ON','-DCMAKE_BUILD_RPATH=$ORIGIN;'+str(cuda/'lib')]


def file_action(receipt,target,candidate):
    receipt['files'].append({'target':str(target),'candidate':str(candidate)})



def stage_maya_pin(root,profile,revision,candidate,directory,receipt):
    from update_builders import canonical
    from maya_cachebound_runtime import verify
    names={'glm-maya':'maya-glm-runtime.json','deepseek-maya':'maya-unsloth-runtime.json'}
    path=root/'config'/names[profile]
    cfg=json.loads(canonical(root,profile).read_text())
    selected=cfg.get('pinned_runtime',cfg.get('cache_bound_runtime'))
    if selected!={'manifest':'config/'+names[profile]}:raise RuntimeError('Unreviewed Maya manifest selection')
    try:verify(cfg,{'id':profile},root)
    except ValueError as error:raise RuntimeError('Unreviewed Maya runtime identity')from error
    manifest=json.loads(path.read_text());target=root/manifest['binary']['path']
    manifest.update(source_commit=revision,status='Short daily DSH qualification required; see daily ledger',CUDA_toolkit='13.0.88; matching CUDA13 runtime/cuBLAS')
    manifest.pop('release',None);manifest['binary']['sha256']=sha(candidate)
    m=directory/names[profile];write_json(m,manifest);file_action(receipt,target,candidate);file_action(receipt,path,m)


def native(root,component,revision,directory,source,log,receipt):
    from update_builders import run
    kind=component['builder'];build=source/'build';maya=kind=='maya-pair'
    if maya:
        patch=root/'patches/maya-ds4-file-cache-target-v1153.patch'
        run(['patch','--batch','--fuzz=0','-p1','-i',patch],log,source)
        test=directory/'cache-test'
        run(['g++','-O2','-std=c++20','-pthread','-I'+str(source/'src/ds4'),root/'tools/maya-file-cache-bound/test_cache_bound.cpp','-o',test],log)
        run([test,directory],log)
    options=['-DSTRATA_ENABLE_CUDA=ON','-DSTRATA_BUILD_TESTS=ON','-DSTRATA_BUILD_DSV41=ON'] if maya else ['-DGGML_CUDA=ON','-DLLAMA_BUILD_TESTS=ON']
    env=dict(os.environ,CC='gcc-13',CXX='g++-13',MAX_JOBS='2')
    run(['cmake','-S',source,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',*options,*cuda_options(root)],log,env=env)
    run(['cmake','--build',build,'--parallel','2'],log,env=env)
    receipt['ctest']=str(build)
    if maya:
        for profile,binary in [('glm-maya','maya'),('deepseek-maya','maya-ds4')]:
            candidate=build/binary
            linkage=subprocess.check_output(['ldd',str(candidate)],text=True)
            if 'not found'in linkage or 'libcudart.so.13'not in linkage or 'libcublas.so.13'not in linkage:raise RuntimeError('Maya CUDA library mismatch')
            stage_maya_pin(root,profile,revision,candidate,directory,receipt)
        old=root/'runtimes/project-maya'
        # Preserve private launch settings and the installed interpreter, never weights.
        run(['cp','-a','--reflink=auto',old/'.venv',source/'.venv'],log,timeout=1800)
        for p in old.glob('*.json'):
            tracked=subprocess.run(['git','-C',str(old),'ls-files','--error-unmatch',p.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
            if not tracked:
                expected=sha(p);shutil.copy2(p,source/p.name)
                if sha(source/p.name)!=expected:raise RuntimeError('Private Maya config changed during staging')
                receipt.setdefault('protected_files',[]).append({'path':str(p),'sha256':expected})
        p=source/'serve/server.py';p.write_text(transform(p.read_text(),'maya'))
        receipt['directories'].append({'target':str(old),'candidate':str(source)})
    else:
        candidate=build/'bin/llama-server';libs=build/'bin';linkage=subprocess.check_output(['ldd',str(libs/'libggml-cuda.so')],text=True)
        if 'not found'in linkage or 'libcudart.so.13'not in linkage or 'libcublas.so.13'not in linkage:raise RuntimeError('llama.cpp CUDA library mismatch')
        old=root/'runtimes/llama.cpp'
        hashes={str((old/'build/bin'/p.name).relative_to(root)):sha(p)for p in libs.iterdir()if p.is_file()and not p.is_symlink()and p.name.startswith('lib')}
        for name in ['bolt-iq2-runtime.json','flash-iq1s-runtime.json']:
            path=root/'config'/name;manifest=json.loads(path.read_text());manifest.update(source_commit=revision,binary_sha256=sha(candidate),runtime_files_sha256=hashes);manifest.pop('release',None)
            m=directory/name;write_json(m,manifest);file_action(receipt,path,m)
        receipt['directories'].append({'target':str(old),'candidate':str(source)})
    receipt['artifacts']=[{'path':str(p),'sha256':sha(p)}for p in ([build/'maya',build/'maya-ds4']if maya else [build/'bin/llama-server'])]


def download(asset,directory):
    name=asset['name']
    if Path(name).name!=name or not asset['browser_download_url'].startswith('https://github.com/Niko1221/Strata/releases/download/'):
        raise RuntimeError('Unexpected Strata asset URL/name')
    size=asset['size']
    if not 0<size<2*1024**3:raise RuntimeError('Strata package outside bounded size')
    path=directory/name
    with urllib.request.urlopen(asset['browser_download_url'],timeout=120)as response,path.open('xb')as out:
        remaining=size
        while remaining:
            data=response.read(min(1024**2,remaining))
            if not data:break
            out.write(data);remaining-=len(data)
        if remaining or response.read(1):raise RuntimeError('Strata asset size mismatch')
    if asset.get('digest')!='sha256:'+sha(path):raise RuntimeError('Strata release digest mismatch')
    return path


def signed_strata(root,component,revision,directory,source,log,receipt):
    from update_builders import run,latest_release,canonical
    # Confirm discovery did not race a new stable release before package selection.
    from update_builders import upstream
    if upstream(component)!=revision:raise RuntimeError('Stable release changed during staging')
    release=latest_release(component);assets=release['assets'];selected={}
    patterns={'control':r'strata-control-([0-9.]+)-linux-x86_64.tar.gz','qwen':r'strata-engine-([0-9.]+)-linux-x86_64-cuda-cuda13.tar.gz','deepseek':r'strata-dsv41-([0-9.]+)-linux-x86_64-cuda-cuda13.tar.gz'}
    versions={}
    for kind,pattern in patterns.items():
        matches=[a for a in assets if re.fullmatch(pattern,a['name'])]
        if len(matches)!=1:raise RuntimeError('Ambiguous/missing signed Strata package '+kind)
        asset=matches[0];versions[kind]=re.fullmatch(pattern,asset['name'])[1];selected[kind]=str(download(asset,directory))
    if len(set(versions.values()))!=1:raise RuntimeError('Strata control/engine versions differ')
    for name in ['strata-feed.json','strata-feed.json.sig']:
        selected[name]=str(download(next(a for a in assets if a['name']==name),directory))
    # Verification uses upstream's trusted-key and archive-safety implementation in
    # a fresh interpreter. No inherited trust-key override may substitute a signer.
    code='''import sys,json,os
from pathlib import Path
sys.path.insert(0,sys.argv[1]);from strata_control import updater,engine_component as ec,signing
paths=json.loads(sys.argv[2]);dest=Path(sys.argv[3]);os.environ.pop('STRATA_UPDATE_TRUSTED_KEYS',None)
keys=signing.load_trusted_keys();signing.verify_bytes(keys,Path(paths['strata-feed.json']).read_bytes(),json.loads(Path(paths['strata-feed.json.sig']).read_text()));signing.install_component_verifier(keys)
feed=json.loads(Path(paths['strata-feed.json']).read_text())
for key,section in [('control','control'),('qwen','engine'),('deepseek','dsv41')]:
 package=Path(paths[key]);entries=[p for p in feed[section]['packages']if Path(p['url']).name==package.name]
 if len(entries)!=1 or entries[0]['sha256']!=__import__('hashlib').file_digest(package.open('rb'),'sha256').hexdigest():raise RuntimeError('Signed feed asset digest mismatch')
for kind in ['qwen','deepseek']:
 folder=dest/kind;updater.extract(Path(paths[kind]),folder,'tar.gz',6*1024**3)
 manifest=ec.read_manifest(folder);ec.verify_signature(manifest,{**os.environ,ec.ENV_REQUIRE_SIGNED:'1'});ec.verify(manifest,full=True)
updater.extract(Path(paths['control']),dest/'control','tar.gz',6*1024**3,allow_links=True)
'''
    packages=directory/'packages';run([sys.executable,'-c',code,source,json.dumps(selected),packages],log)
    version=versions['control'];terminal=root/'runtimes/strata-terminal/terminal';candidate=directory/'terminal'
    run(['cp','-a','--reflink=auto',terminal,candidate],log,timeout=1800)
    control=candidate/version
    if control.exists():raise RuntimeError('Existing control version must not be replaced silently')
    (packages/'control').rename(control);p=control/'serve/server.py';p.write_text(transform(p.read_text(),'strata'))
    link=candidate/'current'
    if not link.is_symlink():raise RuntimeError('Strata current selector is not a symlink')
    link.unlink();link.symlink_to(version)
    cfg_path=canonical(root,'flash-next-strata');cfg=json.loads(cfg_path.read_text());qwen=packages/'qwen';cfg.update(exe=str(qwen/'strata'),lib_dirs=[str(qwen),str(qwen/'lib')],cwd=str(terminal/version))
    c=directory/'qwen-launch-private.json';write_json(c,cfg);file_action(receipt,cfg_path,c)
    receipt['directories'].append({'target':str(terminal),'candidate':str(candidate)})
    runtime='runtimes/strata-unsloth-029';manifest_path=root/'config/deepseek-unsloth-runtime.json';manifest=json.loads(manifest_path.read_text())
    hashes={k:v for k,v in manifest['sha256'].items()if not k.startswith(runtime+'/source/')and not k.startswith(runtime+'/engine/')}
    server=source/'serve/server.py';before=sha(server);server.write_text(transform(server.read_text(),'strata'))
    names=subprocess.check_output(['git','-C',str(source),'ls-files','-z']).decode().split('\0')
    for name in filter(None,names):
        p=source/name
        if p.is_file():hashes[runtime+'/source/'+name]=sha(p)
    engine=packages/'deepseek'
    for p in engine.rglob('*'):
        if p.is_file():hashes[runtime+'/engine/'+p.relative_to(engine).as_posix()]=sha(p)
    manifest.update(source_commit=revision,release=release['tag_name'],engine_version=version,source_server_unpatched_sha256=before,sha256=hashes,signature_verified=True)
    m=directory/'deepseek-unsloth-runtime.json';write_json(m,manifest);file_action(receipt,manifest_path,m)
    helper=root/'scripts/strata_unsloth_runtime.py';text=helper.read_text();text,count=re.subn(r"ENGINE_VERSION = '[0-9.]+'","ENGINE_VERSION = '"+version+"'",text)
    if count!=1:raise RuntimeError('Strata identity check layout changed')
    compile(text,str(helper),'exec');h=directory/'strata_unsloth_runtime.py';h.write_text(text);file_action(receipt,helper,h)
    receipt['directories'].extend([{'target':str(root/runtime/'engine'),'candidate':str(engine)},{'target':str(root/runtime/'source'),'candidate':str(source)}])


def prepare(root,component,revision,directory,source,log,receipt):
    if component['builder']=='strata-signed':signed_strata(root,component,revision,directory,source,log,receipt)
    else:native(root,component,revision,directory,source,log,receipt)
