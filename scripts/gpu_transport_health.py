#!/usr/bin/env python3
"""Attest the direct CPU x8/x8 pair with CUDA peer capability disabled."""
import ctypes, json, os, subprocess, sys
from pathlib import Path

POLICY = Path('/etc/local-llm-gpu-transport.json')
REPORT = Path('/run/local-llm-transport/verified.json')

def trusted_json(path):
    stat = path.stat()
    if stat.st_uid != 0 or stat.st_mode & 0o022:
        raise ValueError('GPU policy/proof must be root-owned and not writable by others')
    return json.loads(path.read_text())

def check_identity(row, boot_id, srcversion):
    if row.get('mode') != 'host-staged' or not row.get('passed') or row.get('boot_id') != boot_id or row.get('nvidia_srcversion') != srcversion:
        raise ValueError('Missing current-boot host-staged GPU proof')
    if row.get('peer_access') != [0, 0]:
        raise ValueError('CUDA peer access must be unavailable in both directions')
    return row

def require_host_staged():
    policy = trusted_json(POLICY)
    if policy != {'schema': 1, 'mode': 'host-staged', 'board': 'MPG Z690 CARBON WIFI (MS-7D30)'}:
        raise ValueError('Unrecognized GPU transport policy')
    return check_identity(trusted_json(REPORT), Path('/proc/sys/kernel/random/boot_id').read_text().strip(), Path('/sys/module/nvidia/srcversion').read_text().strip())

def boot_proof():
    assert os.geteuid() == 0
    REPORT.unlink(missing_ok=True)
    trusted_json(POLICY)
    subprocess.run(['/usr/local/bin/gpu-unlock-health', 'status', '--brief'], check=True)
    assert Path('/sys/class/dmi/id/board_name').read_text().strip() == 'MPG Z690 CARBON WIFI (MS-7D30)'
    for bdf, device, parent in [('0000:01:00.0','0x2208','0000:00:01.0'), ('0000:02:00.0','0x2206','0000:00:01.1')]:
        p = Path('/sys/bus/pci/devices') / bdf
        assert (p/'vendor').read_text().strip() == '0x10de'
        assert (p/'device').read_text().strip() == device
        assert p.resolve().parent.name == parent
        assert (p/'current_link_width').read_text().strip() == '8'
        assert (p/'driver').resolve().name == 'nvidia'
    cuda = ctypes.CDLL('libcuda.so.1')
    assert cuda.cuInit(0) == 0
    count = ctypes.c_int()
    assert cuda.cuDeviceGetCount(ctypes.byref(count)) == 0 and count.value == 2
    peers = []
    for a,b in [(0,1),(1,0)]:
        result = ctypes.c_int()
        assert cuda.cuDeviceCanAccessPeer(ctypes.byref(result),a,b) == 0
        peers.append(result.value)
    assert peers == [0,0], 'Stock driver must not advertise CUDA P2P'
    row = dict(mode='host-staged', passed=True, peer_access=peers, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), nvidia_srcversion=Path('/sys/module/nvidia/srcversion').read_text().strip(), topology='CPU PCIe4 x8/x8; no switch')
    REPORT.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(row,indent=2)+'\n')
    REPORT.chmod(0o644)
    print(json.dumps(require_host_staged()))

if __name__ == '__main__':
    boot_proof() if sys.argv[1:] == ['boot'] else print(json.dumps(require_host_staged()))
