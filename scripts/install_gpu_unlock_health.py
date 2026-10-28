#!/usr/bin/env python3
"""Prepare a reviewable bundle; install root-owned, event-triggered unlock checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

MARKER = 'Managed by Local-LLM GPU unlock health'
ROOT = Path(__file__).resolve().parents[1]
LIBEXEC = '/usr/local/libexec/gpu-unlock-health.py'
TRIGGER = '/usr/local/libexec/gpu-unlock-health-trigger'
CONFIG = '/etc/gpu-unlock-health.json'
STATE = '/var/lib/gpu-unlock-health'
DESTINATIONS = {LIBEXEC, TRIGGER, CONFIG, '/usr/local/bin/gpu-unlock-health',
                '/etc/systemd/system/gpu-unlock-health-boot.service',
                '/etc/systemd/system/gpu-unlock-health-update.service',
                '/etc/systemd/system/gpu-unlock-health.path',
                '/etc/apt/apt.conf.d/99-local-llm-gpu-unlock-health',
                '/etc/kernel/postinst.d/zzzz-local-llm-gpu-unlock-health',
                '/etc/update-motd.d/95-local-llm-gpu-unlock-health'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def service(event):
    return f'''# {MARKER}
[Unit]
Description=Verify GPU unlock {event} health
After=local-fs.target systemd-udev-trigger.service nvidia-persistenced.service
RequiresMountsFor=/boot /var/lib
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -I {LIBEXEC} {event}
ExecStopPost=/usr/bin/python3 -I {LIBEXEC} {event}-result
TimeoutStartSec=15min
Restart=on-failure
RestartPreventExitStatus=1 2
RestartSec=60
StateDirectory=gpu-unlock-health
StateDirectoryMode=0755
RuntimeDirectory=gpu-unlock-health
RuntimeDirectoryMode=0755
RuntimeDirectoryPreserve=yes
UMask=0022
Nice=19
IOSchedulingClass=idle
MemoryMax=1G
CPUQuota=50%
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
CapabilityBoundingSet=~CAP_SYS_MODULE
SystemCallFilter=~@module
ReadOnlyPaths=/usr/lib/modules
ProtectControlGroups=yes
PrivateTmp=yes
RestrictAddressFamilies=AF_UNIX AF_NETLINK
Environment=PATH=/usr/sbin:/usr/bin:/sbin:/bin
Environment=LC_ALL=C
''' + ('\n[Install]\nWantedBy=multi-user.target\n' if event == 'boot' else '')


def payloads(config, checker):
    trigger = f'''#!/bin/sh
# {MARKER}
# Queue only; never fail a package transaction or modify the unlock.
if [ -d /run/systemd/system ]; then
    /usr/bin/systemctl --no-block start gpu-unlock-health-update.service || /usr/bin/logger -p daemon.warning -t gpu-unlock-health 'Could not queue GPU unlock verification'
fi
exit 0
'''
    wrapper = f'#!/bin/sh\n# {MARKER}\nexec /usr/bin/python3 -I {LIBEXEC} "$@"\n'
    hook = f'#!/bin/sh\n# {MARKER}\nexec {TRIGGER}\n'
    motd = f'#!/bin/sh\n# {MARKER}\n/usr/bin/python3 -I {LIBEXEC} status --brief || :\n'
    path = f'''# {MARKER}
[Unit]
Description=Watch package and boot-image changes for GPU unlock checks

[Path]
PathChanged=/var/lib/dpkg/status
PathChanged=/boot
Unit=gpu-unlock-health-update.service

[Install]
WantedBy=multi-user.target
'''
    return {
        LIBEXEC: (checker, 0o755), TRIGGER: (trigger.encode(), 0o755),
        CONFIG: ((json.dumps(config, indent=2)+'\n').encode(), 0o644),
        '/usr/local/bin/gpu-unlock-health': (wrapper.encode(), 0o755),
        '/etc/systemd/system/gpu-unlock-health-boot.service': (service('boot').encode(), 0o644),
        '/etc/systemd/system/gpu-unlock-health-update.service': (service('update').encode(), 0o644),
        '/etc/systemd/system/gpu-unlock-health.path': (path.encode(), 0o644),
        '/etc/apt/apt.conf.d/99-local-llm-gpu-unlock-health':
            ((f'// {MARKER}\nDPkg::Post-Invoke {{ "{TRIGGER}"; }};\n').encode(), 0o644),
        '/etc/kernel/postinst.d/zzzz-local-llm-gpu-unlock-health': (hook.encode(), 0o755),
        '/etc/update-motd.d/95-local-llm-gpu-unlock-health': (motd.encode(), 0o755)}


def configuration():
    text = Path('/etc/default/grub.d/99-local-llm-gpu-unlock.cfg').read_text()
    match = re.findall(r'gpu_unlock\.targets=([^\s"\']+)', text)
    if len(match) != 1:
        raise ValueError('Review the existing explicit unlock targets first')
    targets = []
    for bdf in match[0].split(','):
        if not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', bdf):
            raise ValueError('Refusing non-explicit PCI targets')
        path = Path('/sys/bus/pci/devices') / bdf
        vendor = (path/'vendor').read_text().strip()
        device = (path/'device').read_text().strip()
        if vendor != '0x10de' or device not in ('0x2206', '0x2208', '0x2503', '0x2504'):
            raise ValueError('Unsupported or changed unlock target')
        targets.append({'bdf': bdf, 'vendor': vendor, 'device': device})
    if not targets or len({x['bdf'] for x in targets}) != len(targets):
        raise ValueError('Empty or duplicate targets')
    return {'managed_by': 'linux-llm-nvidia-gpu-unlock-health', 'schema': 1,
            'target_kernel': 'auto', 'targets': targets, 'unlock_version': '1.0.0',
            'reviewed_source': 'af28cbbfd3d922a659227ecfb7369adfd924cf03',
            'grub_dropin': '/etc/default/grub.d/99-local-llm-gpu-unlock.cfg',
            'dracut_dropin': '/etc/dracut.conf.d/99-local-llm-gpu-unlock.conf'}


def prepare(output):
    config = configuration()
    values = payloads(config, (ROOT/'scripts/gpu_unlock_health.py').read_bytes())
    assert set(values) == DESTINATIONS
    output.mkdir(parents=True, exist_ok=False)
    files = []
    for number, (target, (data, mode)) in enumerate(sorted(values.items())):
        name = f'{number:02d}-' + Path(target).name
        (output/name).write_bytes(data)
        files.append({'source': name, 'target': target, 'sha256': sha(data), 'mode': mode})
    manifest = {'managed_by': 'linux-llm-nvidia-gpu-unlock-health', 'files': files}
    raw = (json.dumps(manifest, indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(raw)
    print(json.dumps({'bundle': str(output.resolve()), 'manifest_sha256': sha(raw),
                      'installer_sha256': sha(Path(__file__).read_bytes()),
                      'files': len(files), 'targets': config['targets']}, indent=2))


def read_bundle(bundle, expected):
    raw = (bundle/'manifest.json').read_bytes()
    if sha(raw) != expected:
        raise ValueError('Bundle manifest changed after review')
    manifest = json.loads(raw)
    files = manifest['files']
    if len(files) != len(DESTINATIONS) or {x['target'] for x in files} != DESTINATIONS:
        raise ValueError('Unexpected installation destinations')
    values = {}
    for item in files:
        if Path(item['source']).name != item['source'] or item['mode'] not in (0o644, 0o755):
            raise ValueError('Invalid bundle source/mode')
        data = (bundle/item['source']).read_bytes()
        if sha(data) != item['sha256']:
            raise ValueError('Bundle payload changed after review: ' + item['source'])
        values[item['target']] = (data, item['mode'])
    return values, manifest


def trusted_parent(path):
    for parent in [path.parent, *path.parent.parents]:
        if parent.is_symlink():
            raise ValueError('Refusing symlink installation parent: ' + str(parent))
        if parent.exists():
            info = parent.stat()
            if info.st_uid != 0 or info.st_mode & 0o022:
                raise ValueError('Installation parent is not root-controlled: ' + str(parent))


def install(bundle, expected):
    if os.geteuid() != 0:
        raise ValueError('Administrator authentication is required for system installation')
    os.umask(0o022)
    values, manifest = read_bundle(bundle, expected)  # Hold verified bytes; never execute from the bundle.
    backups = {}
    for target in values:
        path = Path(target)
        trusted_parent(path)
        if path.is_symlink():
            raise ValueError('Refusing existing symlink: ' + target)
        if path.exists():
            raw = path.read_bytes()
            if path.stat().st_uid != 0 or path.stat().st_mode & 0o022:
                raise ValueError('Preserve non-root-controlled file: ' + target)
            if MARKER.encode() not in raw[:256]:
                if target != CONFIG or json.loads(raw).get('managed_by') != 'linux-llm-nvidia-gpu-unlock-health':
                    raise ValueError('Preserve unrelated file: ' + target)
            backups[target] = (raw, path.stat().st_mode & 0o777)
        else:
            backups[target] = None
    state = Path(STATE)
    trusted_parent(state)
    if state.is_symlink() or state.exists() and (state.stat().st_uid != 0 or state.stat().st_mode & 0o022):
        raise ValueError('State directory is not root-controlled')
    state.mkdir(mode=0o755, parents=True, exist_ok=True)
    backup = state / ('install-preimages-' + str(time.time_ns()))
    backup.mkdir(mode=0o700)
    for number, (target, previous) in enumerate(backups.items()):
        if previous is not None:
            (backup/str(number)).write_bytes(previous[0])
    completed = []
    try:
        for target, (data, mode) in values.items():
            path = Path(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            trusted_parent(path)
            temporary = path.with_name('.' + path.name + '.gpu-unlock-health-tmp')
            fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                os.fchmod(stream.fileno(), mode)
                os.fchown(stream.fileno(), 0, 0)
            temporary.replace(path)
            completed.append(target)
        subprocess.run(['/usr/bin/systemctl', 'daemon-reload'], check=True)
        subprocess.run(['/usr/bin/systemd-analyze', 'verify', '/etc/systemd/system/gpu-unlock-health-boot.service', '/etc/systemd/system/gpu-unlock-health-update.service', '/etc/systemd/system/gpu-unlock-health.path'], check=True)
        subprocess.run(['/usr/bin/systemctl', 'enable', 'gpu-unlock-health.path', 'gpu-unlock-health-boot.service'], check=True)
        subprocess.run(['/usr/bin/systemctl', 'start', 'gpu-unlock-health.path'], check=True)
        subprocess.run(['/usr/bin/systemctl', 'start', 'gpu-unlock-health-boot.service'], check=False)
        # Exercise the exact kernel/APT queue command without installing/upgrading any package.
        subprocess.run([TRIGGER], check=True)
        subprocess.run(['/usr/bin/systemctl', 'start', 'gpu-unlock-health-update.service'], check=False)
        result = subprocess.run(['/usr/bin/python3', '-I', LIBEXEC, 'status', '--brief'], check=False)
        if not (state/'boot.json').exists() or not (state/'update.json').exists():
            raise RuntimeError('Health services did not save their initial reports')
        (state/'install-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps({'installed': True, 'initial_health_verified': result.returncode == 0,
                          'status_command': 'gpu-unlock-health status --brief'}))
    except BaseException:
        subprocess.run(['/usr/bin/systemctl', 'disable', '--now', 'gpu-unlock-health.path', 'gpu-unlock-health-boot.service'], check=False)
        subprocess.run(['/usr/bin/systemctl', 'stop', 'gpu-unlock-health-update.service'], check=False)
        for target in reversed(completed):
            path = Path(target)
            if path.is_symlink() or not path.exists() or sha(path.read_bytes()) != sha(values[target][0]):
                continue  # Preserve concurrent administrator edits.
            old = backups[target]
            if old is None:
                path.unlink()
            else:
                path.write_bytes(old[0])
                path.chmod(old[1])
        subprocess.run(['/usr/bin/systemctl', 'daemon-reload'], check=False)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'install'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args()
    if args.action == 'prepare':
        if args.output is None: parser.error('prepare requires --output')
        prepare(args.output)
    else:
        if args.bundle is None or not args.manifest_sha256: parser.error('install requires reviewed bundle and manifest hash')
        install(args.bundle, args.manifest_sha256)


if __name__ == '__main__':
    main()
