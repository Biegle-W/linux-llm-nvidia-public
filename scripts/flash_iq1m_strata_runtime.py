"""Verify the separate native Strata IQ1_M preset before guarded serving."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def prepare_config(profile,root=ROOT,home=None):
    root=Path(root)
    if (profile['id']!='flash-next-iq1m-strata' or profile['allocated_context']!=131072
            or profile['runtime_manifest']!='config/flash-iq1m-strata-runtime.json'):
        raise ValueError('Unexpected IQ1_M profile/context/manifest')
    pins=json.loads((root/profile['runtime_manifest']).read_text())
    if len(pins['files'])!=3 or any(not row['file'].startswith('Qwen3.8-Flash-Next-UD-IQ1_M-') for row in pins['files']):
        raise ValueError('Expected three pinned IQ1_M shards')
    for name,digest in pins['runtime_files_sha256'].items():
        with (root/name).open('rb') as stream:
            actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=digest:
            raise ValueError('IQ1_M runtime/pack hash mismatch: '+name)
    directory=root/profile['storage']['checkpoint_directory']
    for row in pins['files']:
        if row['publisher_sha256_matched'] is not True or (directory/row['file']).stat().st_size!=row['bytes']:
            raise ValueError('IQ1_M checkpoint receipt/size mismatch')
    source=(Path.home() if home is None else Path(home))/'.local/state/strata/launch/qwen-flash-next-iq1m.json'
    config=json.loads(source.read_text())
    args=config['args']
    if hashlib.sha256(json.dumps(args,separators=(',',':')).encode()).hexdigest()!=pins['args_sha256']:
        raise ValueError('IQ1_M canonical arguments changed')
    for flag,expected in [('--pack',str(root/pins['pack_directory'])),
                          ('--native',str(directory/pins['files'][0]['file'])),
                          ('--ple-gguf',str(directory/pins['files'][-1]['file'])),
                          ('--max-context','131072'),('--vram-reserve-mib','1024')]:
        if flag not in args or args[args.index(flag)+1]!=expected:
            raise ValueError('IQ1_M preset differs from selected setting: '+flag)
    if (config['exe']!=str(root/pins['binary']) or config.get('gpu')!=[0,1]
            or config.get('tokenizer')!=str(root/pins['pack_directory']/'tokenizer')
            or config.get('layer_split')!='auto' or '--resident-experts' not in args
            or '--mmap-experts' not in args):
        raise ValueError('IQ1_M engine/device/cache selection mismatch')
    return source
