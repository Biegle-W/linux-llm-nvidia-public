#!/usr/bin/env python3
"""Require this boot's root-owned bidirectional P2P proof before model loading."""
import json
from pathlib import Path

REPORT=Path('/run/local-llm-p2p/verified.json')
def require_verified_pair(report=REPORT,boot_path=Path('/proc/sys/kernel/random/boot_id'),module_path=Path('/sys/module/nvidia/srcversion')):
    try:
        info=report.stat()
        if info.st_uid!=0 or info.st_mode & 0o022:
            raise ValueError('peer proof must be root-owned and not writable by other users')
        row=json.loads(report.read_text())
        if not row.get('passed') or row['boot_id']!=boot_path.read_text().strip() or row['nvidia_srcversion']!=module_path.read_text().strip():
            raise ValueError('missing current-boot peer correctness proof')
    except (OSError,ValueError,KeyError) as e:
        raise RuntimeError('GPU P2P startup check failed. Check local-llm-acs-pair.service and gpu-unlock-health; repair/reboot before loading a model. '+str(e)) from e
    return row
if __name__=='__main__':
    print(json.dumps(require_verified_pair()))
