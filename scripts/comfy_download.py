"""Download only the pinned ComfyUI candidates onto the resident-model SATA SSD."""
import hashlib
import json
from pathlib import Path
import sys
import subprocess
from storage_policy import ensure_sata_mount
from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parents[1]

def main():
    config = json.loads((ROOT / 'config/comfy-runtime.json').read_text())
    ensure_sata_mount(ROOT)
    target = (ROOT / config['checkpoint_directory']).resolve(strict=True)
    device = subprocess.check_output(['findmnt','-n','-o','SOURCE','--target',str(target)],text=True).strip().split('[',1)[0]
    inventory = subprocess.check_output(['lsblk','--inverse','--noheadings','--raw','--output','TYPE,TRAN','--',device],text=True)
    assert {parts[1] for line in inventory.splitlines() if len(parts:=line.split())==2 and parts[0]=='disk'} == {'sata'}, 'Resident weights require SATA'
    chosen = sys.argv[1:]
    receipts = []
    for model in config['models']:
        if chosen and model['id'] not in chosen:
            continue
        for row in model['files']:
            print('Downloading/verifying ' + row['file'], flush=True)
            path = Path(hf_hub_download(model['repo'], row['file'], revision=model['revision'], local_dir=target))
            assert path.stat().st_size == row['bytes']
            with path.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            assert actual == row['sha256'], 'Publisher hash mismatch: ' + row['file']
            receipts.append(dict(row, publisher_sha256_matched=True, model=model['id']))
            print('Publisher SHA256 PASS: ' + path.name, flush=True)
    output = ROOT / 'data/comfy-qualification-20261105'
    output.mkdir(exist_ok=True)
    (output / ('download-' + ('-'.join(chosen) or 'all') + '.json')).write_text(json.dumps(receipts, indent=2) + '\n')

if __name__ == '__main__':
    main()
