"""Exact process ownership for the nightly updater's existing GPU reservation."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def owner_valid(owner, root=ROOT):
    try:
        if owner.get('owner') != 'nvidia-daily-update' or not isinstance(owner.get('nonce'),str) or len(owner['nonce']) != 48:
            return False
        process = Path('/proc')/str(owner['pid'])
        if process.stat().st_uid != os.getuid(): return False
        if (process/'stat').read_text().split(') ',1)[1].split()[19] != owner['start_ticks']: return False
        return str(Path(root)/'scripts/daily_engine_update.py').encode() in (process/'cmdline').read_bytes().split(b'\0')
    except (OSError,ValueError,KeyError,IndexError,TypeError): return False


def allowed_reservation(path, owner, root=ROOT):
    try:
        return owner is not None and json.loads(Path(path).read_text()) == owner and owner_valid(owner,root)
    except (OSError,ValueError,TypeError): return False
