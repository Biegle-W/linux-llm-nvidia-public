#!/usr/bin/env python3
"""Check physical checkpoint placement for the maintained model storage policy."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def ensure_sata_mount(root):
    """Use the private UUID mapping; never replace an unexpected mounted drive."""
    mapping = root / 'data/storage-mount.json'
    if not mapping.exists():
        return
    config = json.loads(mapping.read_text())
    mountpoint = config['mountpoint']
    uuid = config['uuid']
    if not Path(mountpoint).is_absolute() or not uuid or any(c not in '0123456789abcdefABCDEF-' for c in uuid):
        raise RuntimeError('Invalid private SATA mount mapping.')
    command = ['findmnt', '--mountpoint', mountpoint, '--noheadings', '--output', 'UUID']
    mounted = subprocess.run(command, capture_output=True, text=True)
    if mounted.returncode == 0:
        if mounted.stdout.strip() != uuid:
            raise RuntimeError('Unexpected drive occupies the SATA model mount; nothing was changed.')
        return
    result = subprocess.run(['udisksctl', 'mount', '--block-device', '/dev/disk/by-uuid/' + uuid,
                             '--no-user-interaction'], capture_output=True, text=True, timeout=30)
    if result.returncode or subprocess.run(command, capture_output=True, text=True).stdout.strip() != uuid:
        raise RuntimeError('SATA model drive could not be mounted automatically. Mount it in Files/Disks and retry.')


def verify_storage(profile, root=ROOT):
    """Follow file links and reject checkpoints on the wrong physical transport."""
    storage = profile['storage']
    if storage['required_transport'] == 'sata':
        ensure_sata_mount(root)
    folder = (root / storage['checkpoint_directory']).resolve(strict=True)
    files = sorted(p for p in folder.iterdir() if p.suffix in ('.safetensors', '.gguf') and p.is_file())
    if not files:
        raise RuntimeError(f"{profile['id']}: checkpoint files are missing; check the storage mount.")
    devices = {}
    for path in files:
        resolved = path.resolve(strict=True)
        device = subprocess.check_output(
            ['findmnt', '-n', '-o', 'SOURCE', '--target', str(resolved)], text=True).strip().split('[', 1)[0]
        if not device.startswith('/dev/') or '\n' in device:
            raise RuntimeError('Checkpoint storage must resolve to one local block device per file.')
        if device not in devices:
            inventory = subprocess.check_output(
                ['lsblk', '--inverse', '--noheadings', '--raw', '--output', 'TYPE,TRAN', '--', device], text=True)
            transports = {parts[1] for line in inventory.splitlines()
                          if len(parts := line.split()) == 2 and parts[0] == 'disk'}
            if transports != {storage['required_transport']}:
                raise RuntimeError(f"{profile['id']}: checkpoint storage requires {storage['required_transport']}; "
                                   f"found {', '.join(sorted(transports)) or 'unknown transport'}. "
                                   'See docs/STORAGE-POLICY.md.')
            devices[device] = storage['required_transport']
    return {'profile': profile['id'], 'resolved_directory': str(folder),
            'transport': storage['required_transport'], 'devices': sorted(devices), 'weight_files': len(files)}


def main():
    from profile_catalog import load_catalog
    profiles = load_catalog()['profiles']
    if len(sys.argv) > 2:
        raise SystemExit('Usage: storage_policy.py [profile-id]')
    if len(sys.argv) == 2:
        profiles = [p for p in profiles if p['id'] == sys.argv[1]]
        if not profiles:
            raise SystemExit('Unknown maintained profile.')
    try:
        print(json.dumps([verify_storage(p) for p in profiles], indent=2))
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit('Storage preflight failed: ' + str(error))


if __name__ == '__main__':
    main()
