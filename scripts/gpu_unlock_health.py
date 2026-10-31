#!/usr/bin/env python3
# Managed by Local-LLM GPU unlock health
"""Read-only GPU unlock checks for boot and completed package transactions."""
import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

CONFIG = Path('/etc/gpu-unlock-health.json')
STATE = Path('/var/lib/gpu-unlock-health')
TOOLS = {'dpkg-query': '/usr/bin/dpkg-query', 'dkms': '/usr/sbin/dkms',
         'modinfo': '/usr/sbin/modinfo', 'lsinitramfs': '/usr/bin/lsinitramfs',
         'lsinitrd': '/usr/bin/lsinitrd', 'journalctl': '/usr/bin/journalctl',
         'nvidia-smi': '/usr/bin/nvidia-smi'}
PACKAGE = re.compile(r'^(?:linux-(?:image|headers|modules|generic|hwe|firmware)|(?:lib)?nvidia|gpu-unlock)')
BDF = re.compile(r'^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$')


def run(name, *args, timeout=180):
    return subprocess.check_output([TOOLS[name], *args], text=True, timeout=timeout,
                                   stderr=subprocess.PIPE, env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'})


def load(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None


def atomic(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    temporary.chmod(0o644)
    temporary.replace(path)


def targets_from(text):
    matches = re.findall(r'gpu_unlock\.targets=([^\s"\']+)', text)
    if len(matches) != 1:
        raise ValueError('Expected one explicit gpu_unlock.targets argument')
    targets = matches[0].split(',')
    if len(targets) != len(set(targets)) or not all(BDF.fullmatch(x) for x in targets):
        raise ValueError('Invalid or duplicate explicit GPU targets')
    return set(targets)


def package_versions(text):
    rows = []
    for line in text.splitlines():
        parts = line.split('\t')
        if len(parts) == 3 and PACKAGE.match(parts[0]):
            if parts[2] == 'installed':
                rows.append(parts[:2])
            elif parts[2] not in ('config-files', 'not-installed'):
                raise ValueError('Relevant package is not configured: ' + parts[0] + ' (' + parts[2] + ')')
    return sorted(rows)


def normalize_bdf(value):
    domain, bus, slot = value.strip().lower().split(':')
    return f'{int(domain, 16):04x}:{bus}:{slot}'


def evaluate_boot(log, expected, cards):
    """Require per-card success before the first NVIDIA initialization marker."""
    unlocks = {}
    nvidia = []
    errors = []
    for record in log:
        message = record.get('MESSAGE', '')
        if not isinstance(message, str):
            continue
        stamp = int(record.get('__MONOTONIC_TIMESTAMP', record.get('_SOURCE_MONOTONIC_TIMESTAMP', 0)))
        match = re.search(r'pci ([0-9a-f:.]+): gpu_unlock: unlocked\b', message)
        if match and match[1] in expected:
            unlocks[match[1]] = stamp
        if 'NVRM: loading NVIDIA' in message or 'nvidia-nvlink: Nvlink Core is being initialized' in message:
            nvidia.append(stamp)
        if 'gpu_unlock:' in message and not message.startswith('gpu_unlock: module verification failed:') and re.search(r'\b(?:failed|failure|timeout|timed out)\b', message, re.I):
            errors.append(message)
        if 'NVRM: Xid' in message:
            errors.append(message)
    if not nvidia or min(nvidia) <= 0:
        raise ValueError('No ordered NVIDIA initialization evidence in this boot journal')
    for target in expected:
        if target not in unlocks or not 0 < unlocks[target] < min(nvidia):
            raise ValueError('Missing successful pre-NVIDIA unlock evidence for ' + target)
        if target not in cards:
            raise ValueError('Selected GPU missing from nvidia-smi: ' + target)
    if errors:
        raise ValueError('Unlock/NVIDIA errors in current boot: ' + '; '.join(errors[:3]))
    return {'unlocked_before_nvidia': sorted(expected), 'unlock_monotonic_us': unlocks,
            'nvidia_first_monotonic_us': min(nvidia), 'driver_versions': sorted({cards[x] for x in expected})}


def locks_busy(paths, contents):
    wanted = set()
    for path in paths:
        try:
            stat = path.stat()
            wanted.add((os.major(stat.st_dev), os.minor(stat.st_dev), stat.st_ino))
        except FileNotFoundError:
            pass
    for line in contents.splitlines():
        for token in line.split():
            if re.fullmatch(r'[0-9a-fA-F]+:[0-9a-fA-F]+:[0-9]+', token):
                major, minor, inode = token.split(':')
                if (int(major, 16), int(minor, 16), int(inode)) in wanted:
                    return True
    return False


def settle(timeout=600):
    deadline = time.monotonic() + timeout
    previous = None
    stable = 0
    while time.monotonic() < deadline:
        stat = Path('/var/lib/dpkg/status').stat()
        signature = (stat.st_ino, stat.st_mtime_ns, stat.st_size)
        busy = locks_busy([Path('/var/lib/dpkg/lock'), Path('/var/lib/dpkg/lock-frontend')],
                          Path('/proc/locks').read_text())
        stable = stable + 1 if not busy and signature == previous else 0
        if stable >= 3:
            return
        previous = signature
        time.sleep(2)
    raise TimeoutError('Package transaction still active; retry after it completes')


def target_kernel(config):
    if config.get('target_kernel', 'auto') != 'auto':
        kernel = config['target_kernel']
    else:
        defaults = [Path('/etc/default/grub'), *sorted(Path('/etc/default/grub.d').glob('*.cfg'))]
        value = '0'
        for path in defaults:
            if path.exists():
                for line in path.read_text().splitlines():
                    match = re.fullmatch(r'\s*GRUB_DEFAULT\s*=\s*([^#]+?)\s*', line)
                    if match:
                        value = match[1].strip().strip('"\'')
        if value != '0':
            raise ValueError('Custom GRUB default requires an explicit target_kernel policy')
        path = Path('/boot/vmlinuz')
        if not path.is_symlink():
            raise ValueError('Missing /boot/vmlinuz symlink; cannot identify next default kernel')
        kernel = path.resolve(strict=True).name.removeprefix('vmlinuz-')
    if not re.fullmatch(r'[A-Za-z0-9_.+-]+', kernel):
        raise ValueError('Invalid target kernel name')
    return kernel


def fingerprint(config, kernel, packages):
    paths = [Path('/boot/initrd.img-' + kernel), Path('/boot/vmlinuz-' + kernel),
             Path('/boot/grub/grub.cfg'), Path(config['grub_dropin']), Path(config['dracut_dropin'])]
    if config.get('selection_mode') == 'boot-model-ids':
        paths.extend([Path(config['auto_hook']), Path(config['auto_module_setup']), Path('/etc/modprobe.d/local-llm-dynamic-p2p.conf')])
    for module in ['gpu_unlock', 'nvidia']:
        try:
            paths.append(Path(run('modinfo', '-k', kernel, '-F', 'filename', module).strip()))
        except (OSError, subprocess.SubprocessError):
            pass
    stamps = []
    for path in paths:
        try:
            stat = path.stat()
            stamps.append([str(path), stat.st_mtime_ns, stat.st_size])
        except OSError:
            stamps.append([str(path), None, None])
    fingerprint_config = dict(config)
    if config.get('selection_mode') == 'boot-model-ids':
        fingerprint_config['targets'] = sorted((x['vendor'], x['device']) for x in config['targets'])
    evidence = {'kernel': kernel, 'packages': packages, 'files': stamps, 'config': fingerprint_config}
    return hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()


def resolve_config(config, base=Path('/sys/bus/pci/devices')):
    if config.get('selection_mode') != 'boot-model-ids':
        return config
    approved = {'0x2206', '0x2208', '0x2503'}
    if set(config.get('approved_device_ids', [])) != approved:
        raise ValueError('Auto selection must retain exactly the approved three models')
    found = []
    for device in sorted(base.glob('*')):
        if (device / 'vendor').read_text().strip() != '0x10de':
            continue
        if not (device / 'class').read_text().startswith('0x03'):
            continue
        model = (device / 'device').read_text().strip()
        if model in approved:
            if not BDF.fullmatch(device.name):
                raise ValueError('Invalid discovered GPU address')
            found.append({'bdf': device.name, 'vendor': '0x10de', 'device': model})
    if len(found) != 3 or {x['device'] for x in found} != approved:
        raise ValueError('Expected exactly one GPU of each approved model')
    return dict(config, targets=found)


def check_preboot(config, kernel):
    expected = {item['bdf'] for item in config['targets']}
    auto = config.get('selection_mode') == 'boot-model-ids'
    grub_text = Path(config['grub_dropin']).read_text()
    if auto:
        if 'local_llm_gpu_unlock=auto' not in grub_text or 'gpu_unlock.targets=' in grub_text:
            raise ValueError('Auto unlock opt-in missing or stale explicit targets remain')
    elif targets_from(grub_text) != expected:
        raise ValueError('GRUB unlock target list differs from the approved GPU identities')
    for item in config['targets']:
        device = Path('/sys/bus/pci/devices') / item['bdf']
        for name in ['vendor', 'device']:
            if (device / name).read_text().strip() != item[name]:
                raise ValueError('GPU identity/topology changed at ' + item['bdf'])
    dracut_text = Path(config['dracut_dropin']).read_text()
    if auto:
        if 'local-llm-gpu-unlock' not in dracut_text or 'force_drivers' in dracut_text:
            raise ValueError('Dynamic early unlock module missing or conflicting force-load present')
    elif not re.search(r'force_drivers\+?=.*\bgpu_unlock\b', dracut_text):
        raise ValueError('Dracut no longer requests early gpu_unlock loading')
    dkms = run('dkms', 'status')
    pattern = r'^gpu-unlock/' + re.escape(config['unlock_version']) + r',\s*' + re.escape(kernel) + r',.*:\s*installed\s*$'
    if not re.search(pattern, dkms, re.M):
        raise ValueError('gpu-unlock DKMS is not installed for target kernel ' + kernel)
    version = run('modinfo', '-k', kernel, '-F', 'version', 'gpu_unlock').strip()
    if version != config['unlock_version']:
        raise ValueError('Unlock module version differs from reviewed configuration')
    driver = run('modinfo', '-k', kernel, '-F', 'version', 'nvidia').strip()
    if not driver:
        raise ValueError('NVIDIA module unavailable for target kernel')
    image = '/boot/initrd.img-' + kernel
    listing = [line.removeprefix('./') for line in run('lsinitramfs', image).splitlines()]
    module = re.compile(r'(?:usr/)?lib/modules/' + re.escape(kernel) + r'/.*gpu_unlock\.ko(?:\.(?:xz|gz|zst))?$')
    if not any(module.fullmatch(line) for line in listing):
        raise ValueError('Target initramfs lacks its gpu_unlock kernel module')
    firmware = run('modinfo', '-k', kernel, '-F', 'firmware', 'gpu_unlock').splitlines()
    if not firmware:
        raise ValueError('Unlock module declares no firmware; review module provenance')
    for name in firmware:
        pattern = re.compile(r'(?:usr/)?lib/firmware/' + re.escape(name) + r'(?:\.(?:xz|gz|zst))?$')
        if not any(pattern.fullmatch(line) for line in listing):
            raise ValueError('Target initramfs lacks firmware: ' + name)
    if auto:
        hooks = [line for line in listing if line.endswith('/hooks/pre-udev/00-unlock-auto.sh')]
        if len(hooks) != 1:
            raise ValueError('Target initramfs lacks the unique automatic unlock hook')
        early = run('lsinitrd', '-f', hooks[0], image)
        wanted = Path(config['auto_hook']).read_text()
        if early.strip() != wanted.strip():
            raise ValueError('Automatic unlock hook differs from the installed reviewed copy')
    else:
        early = run('lsinitrd', '-f', 'etc/cmdline.d/20-force_drivers.conf', image)
        if 'rd.driver.pre=gpu_unlock' not in early.split():
            raise ValueError('Target initramfs lacks the pre-driver unlock request')
    if not any(line.endswith('/dracut-pre-udev.service') for line in listing):
        raise ValueError('Target initramfs lacks the dracut pre-udev service')
    lines = [line.strip() for line in Path('/boot/grub/grub.cfg').read_text().splitlines()]
    entries = [line for line in lines if re.match(r'linux(?:efi)?\s', line)
               and re.search(r'vmlinuz-' + re.escape(kernel) + r'(?:\s|$)', line) and 'recovery' not in line.split()]
    if not entries or any(('local_llm_gpu_unlock=auto' not in line.split() or 'gpu_unlock.targets=' in line) if auto else targets_from(line) != expected for line in entries):
        raise ValueError('Generated normal GRUB entries do not preserve the selected unlock targets')
    return {'target_kernel': kernel, 'unlock_version': version, 'target_nvidia_version': driver,
            'firmware_files_verified': len(firmware), 'initramfs_verified': True, 'grub_verified': True}


def check_boot(config, kernel, preboot):
    expected = {item['bdf'] for item in config['targets']}
    cmdline = Path('/proc/cmdline').read_text()
    if config.get('selection_mode') == 'boot-model-ids':
        if 'local_llm_gpu_unlock=auto' not in cmdline.split() or 'gpu_unlock.targets=' in cmdline:
            raise ValueError('Running kernel lacks the automatic unlock opt-in')
    elif targets_from(cmdline) != expected:
        raise ValueError('Running kernel lacks the approved unlock target argument')
    deadline = time.monotonic() + 90
    while True:
        bound = all((Path('/sys/bus/pci/devices') / target / 'driver').resolve().name == 'nvidia' for target in expected)
        if bound:
            break
        if time.monotonic() >= deadline:
            raise ValueError('Selected GPUs did not bind to NVIDIA within the boot grace period')
        time.sleep(2)
    output = run('nvidia-smi', '--query-gpu=pci.bus_id,driver_version', '--format=csv,noheader,nounits', timeout=30)
    cards = {normalize_bdf(row[0]): row[1].strip() for row in csv.reader(output.splitlines())}
    records = [json.loads(line) for line in run('journalctl', '-k', '-b', '--no-pager', '-o', 'json').splitlines()]
    result = evaluate_boot(records, expected, cards)
    running_driver = run('modinfo', '-k', platform.release(), '-F', 'version', 'nvidia').strip()
    if result['driver_versions'] != [running_driver]:
        raise ValueError('Loaded NVIDIA driver differs from the module installed for the running kernel')
    result.update(running_kernel=platform.release(), running_nvidia_version=running_driver)
    # A new default kernel may already be installed on an otherwise valid old boot.
    result['next_boot_pending'] = platform.release() != kernel or running_driver != preboot['target_nvidia_version']
    return result


def state_view(boot, update, boot_id):
    current = boot if boot and boot.get('boot_id') == boot_id else None
    if current and current.get('status') in ('checking', 'pending_transaction'):
        return 'BOOT CHECK PENDING', current
    if current and current.get('status') == 'failed':
        return 'FAILED', current
    newer = update if update and (not current or update.get('time', 0) >= current.get('time', 0)) else None
    if newer and newer.get('status') in ('checking', 'pending_transaction'):
        return 'UPDATE CHECK PENDING', newer
    if newer and newer.get('status') == 'failed':
        return 'FAILED', newer
    if not current:
        return 'PENDING BOOT CHECK', update or boot
    if newer and newer.get('fingerprint') != current.get('fingerprint'):
        return 'PENDING REBOOT VERIFICATION', newer
    if current.get('status') == 'verified' and not current.get('boot', {}).get('next_boot_pending'):
        return 'VERIFIED', current
    return 'PENDING REBOOT VERIFICATION', current


def status(state, brief=False):
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    name, record = state_view(load(state / 'boot.json'), load(state / 'update.json'), boot_id)
    if brief:
        print('GPU unlock: ' + name + (': ' + record['error'] if record and record.get('error') else ''))
    else:
        print(json.dumps({'summary': name, 'record': record}, indent=2))
    return 1 if name == 'FAILED' else 0 if name == 'VERIFIED' else 2


def audit(config, state, event, force=False):
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    row = {'event': event, 'time': time.time(), 'boot_id': boot_id, 'status': 'checking',
           'running_kernel': platform.release(), 'performance_tested': False}
    previous = load(state / 'update.json')
    state.mkdir(parents=True, exist_ok=True)
    atomic(state / (event + '.json'), row)
    atomic(state / 'latest.json', row)
    try:
        settle()
        config = resolve_config(config)
        row['resolved_targets'] = config['targets']
        packages = package_versions(run('dpkg-query', '-W', '-f=${binary:Package}\t${Version}\t${db:Status-Status}\n'))
        kernel = target_kernel(config)
        row['fingerprint'] = fingerprint(config, kernel, packages)
        if event == 'update' and not force and previous and previous.get('fingerprint') == row['fingerprint'] and previous.get('status') in ('ready_pending_boot', 'verified_current_boot'):
            atomic(state / 'update.json', previous)
            atomic(state / 'latest.json', previous)
            print('GPU unlock: no relevant kernel/NVIDIA/boot-image change; retained prior check')
            return 1 if previous.get('status') == 'failed' else 0
        row['preboot'] = check_preboot(config, kernel)
        row['packages'] = packages
        if event == 'boot':
            row['boot'] = check_boot(config, kernel, row['preboot'])
            row['status'] = 'verified'
        else:
            boot = load(state / 'boot.json')
            verified = boot and boot.get('boot_id') == boot_id and boot.get('status') == 'verified' and boot.get('fingerprint') == row['fingerprint']
            row['status'] = 'verified_current_boot' if verified else 'ready_pending_boot'
    except TimeoutError as error:
        row.update(status='pending_transaction', error=str(error))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        detail = str(error)
        if isinstance(error, subprocess.CalledProcessError):
            detail += ': ' + (error.stderr or '').strip()[:1500]
        row.update(status='failed', error=detail)
    state.mkdir(parents=True, exist_ok=True)
    atomic(state / (event + '.json'), row)
    atomic(state / 'latest.json', row)
    print('GPU unlock: ' + row['status'] + (': ' + row['error'] if row.get('error') else ''), flush=True)
    return 75 if row['status'] == 'pending_transaction' else 1 if row['status'] == 'failed' else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'boot', 'update', 'boot-result', 'update-result'], nargs='?', default='status')
    parser.add_argument('--brief', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.action == 'status':
        return status(STATE, args.brief)
    if os.geteuid() != 0:
        parser.error('System health checks run as root through their installed service')
    if args.action.endswith('-result'):
        event = args.action.removesuffix('-result')
        record = load(STATE / (event + '.json')) or {}
        result = os.environ.get('SERVICE_RESULT', 'unknown')
        if result != 'success' and record.get('status') not in ('failed', 'pending_transaction'):
            record.update(event=event, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                          time=time.time(), status='failed', error='Health service terminated: ' + result)
            STATE.mkdir(parents=True, exist_ok=True)
            atomic(STATE / (event + '.json'), record)
            atomic(STATE / 'latest.json', record)
        return 0
    config = load(CONFIG)
    if not config or config.get('managed_by') != 'linux-llm-nvidia-gpu-unlock-health':
        parser.error('Missing managed root-owned configuration')
    expected = [item['bdf'] for item in config['targets']]
    if not expected or len(set(expected)) != len(expected) or not all(BDF.fullmatch(x) for x in expected):
        parser.error('Invalid explicit target list')
    with Path('/run/gpu-unlock-health/check.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        return audit(config, STATE, args.action, args.force)


if __name__ == '__main__':
    raise SystemExit(main())
