"""Publish only reviewed ledger/pin files; retain independent public history."""
import hashlib
import os
import subprocess
from pathlib import Path
import sys


def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def audit_payload(root):
    sys.path.insert(0,str(root/'scripts'))
    import sync_public
    key = (root/'data/local-api-key').read_text().strip()
    hashes = {}
    manifest=__import__('json').loads((root/'assets/samples/comfy/manifest.json').read_text());media={}
    for row in manifest['samples']:
        media['assets/samples/comfy/'+row['file']]={'bytes':row['bytes'],'sha256':row['sha256']}
        if row.get('poster'):media['assets/samples/comfy/'+row['poster']]={'bytes':row['poster_bytes'],'sha256':row['poster_sha256']}
    for name in sync_public.FILES:
        raw = (root/name).read_bytes()
        if name in sync_public.SAMPLE_MEDIA:
            sync_public.validate_sample_media(name,raw,media)
        elif name != 'assets/icons/hyperqwen.png':
            text = sync_public.strip_private_workflow(raw.decode())
            if name == 'README.md': text = text.replace('# Linux LLM NVIDIA\n','# Linux LLM NVIDIA — public reference\n',1)
            if key in text or sync_public.BLOCK.search(sync_public.privacy_scan_text(name,text)):
                raise RuntimeError('Public payload privacy check failed: '+name)
            for forbidden in ('CODEX_'+'THREAD_ID','codex-'+'checkpoints','context-'+'window-status.py','NVIDIA-'+'SWAP-POLICY-AUTHORIZATION'):
                if forbidden in text: raise RuntimeError('Private workflow in public payload: '+name)
            raw = text.encode()
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return hashes


def commit(root,message,files=()):
    env=dict(os.environ,GIT_AUTHOR_NAME='LLM Maintenance',GIT_AUTHOR_EMAIL='llm-maintenance@example.invalid',
             GIT_COMMITTER_NAME='LLM Maintenance',GIT_COMMITTER_EMAIL='llm-maintenance@example.invalid')
    command=['git','-C',str(root),'commit','-m',message]
    if files: command.extend(['--',*files])
    subprocess.run(command,check=True,env=env)



def push_if_ahead(root,allowed):
    """Retry committed-but-unpushed owned records without pushing unrelated work."""
    if git(root,'branch','--show-current')!='main':raise RuntimeError('Automatic publication requires main')
    commits=git(root,'rev-list','--reverse','origin/main..HEAD').splitlines()
    for revision in commits:
        identity=git(root,'show','-s','--format=%an%n%ae%n%cn%n%ce',revision).splitlines()
        if identity!=['LLM Maintenance','llm-maintenance@example.invalid']*2:
            raise RuntimeError('Unrelated unpublished identity preserved; push deferred')
        parents=git(root,'rev-list','--parents','-n','1',revision).split()
        if len(parents)!=2:raise RuntimeError('Unreviewed unpublished history preserved; push deferred')
        paths=set(git(root,'diff-tree','--no-commit-id','--name-only','-r',revision).splitlines())
        if not paths or not paths.issubset(set(allowed)):
            raise RuntimeError('Unrelated unpublished files preserved; push deferred')
    if commits:
        subprocess.run(['git','-C',str(root),'-c','credential.helper=','-c','credential.helper=!gh auth git-credential','push','origin','main'],check=True,timeout=120)


def publish(root, owned):
    root = Path(root); public = root.parent/'linux-llm-nvidia-public'
    if git(root,'diff','--name-only','--cached'): raise RuntimeError('Unrelated staged changes preserved; publication deferred')
    dirty = set(git(root,'diff','--name-only').splitlines())
    if not dirty.issubset(set(owned)): raise RuntimeError('Unrelated tracked edits preserved; publication deferred')
    if git(public,'status','--porcelain'): raise RuntimeError('Public checkout is not clean; publication deferred')
    hashes = audit_payload(root)
    changed = [p for p in owned if git(root,'status','--porcelain','--',p)]
    if changed:
        subprocess.run(['git','-C',str(root),'add','--',*changed],check=True)
        commit(root,'Record qualified nightly NVIDIA engine update',changed)
    push_if_ahead(root,owned)
    subprocess.run([sys.executable,str(root/'scripts/sync_public.py'),str(public)],check=True)
    for name,expected in hashes.items():
        if hashlib.sha256((public/name).read_bytes()).hexdigest()!=expected: raise RuntimeError('Export byte identity mismatch: '+name)
    if git(public,'diff','--name-only'):
        subprocess.run(['git','-C',str(public),'add','--',*hashes],check=True)
        commit(public,'Publish qualified nightly NVIDIA engine results')
    push_if_ahead(public,hashes)
