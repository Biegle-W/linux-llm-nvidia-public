#!/usr/bin/env python3
"""Install the user's daily 03:00 NVIDIA updater without launching an update now."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
UNITS = ('nvidia-daily-engine-update.service','nvidia-daily-engine-update-recover.service','nvidia-daily-engine-update.timer')


def main():
    os.umask(0o077)
    key = (ROOT/'data/local-api-key').read_text().strip()
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def health():
        req=urllib.request.Request('http://127.0.0.1:10100/health',headers={'Authorization':'Bearer '+key})
        with op.open(req,timeout=5) as f:return json.load(f)
    h=health()
    if any(h.get(k) for k in ('busy','queued','loading_model','active_model','admission_active')):
        raise SystemExit('Router must be idle and unloaded for installation; preserve active work and retry later.')
    if (ROOT/'data/GPU-LOCK').exists(): raise SystemExit('Preserve the existing GPU reservation; retry installation later.')
    unit_dir=Path.home()/'.config/systemd/user';unit_dir.mkdir(parents=True,exist_ok=True)
    backup=ROOT/'data/daily-update/install-preimages';backup.mkdir(mode=0o700,parents=True,exist_ok=True)
    for name in UNITS:
        p=unit_dir/name
        new=(ROOT/'network/systemd'/name).read_text().replace('@ROOT@',str(ROOT))
        if p.exists() and p.read_text()!=new:
            raise SystemExit('An existing different updater unit was preserved: '+name)
        p.write_text(new)
    drop=unit_dir/'nvidia-model-router.service.d/30-daily-update-recovery.conf';drop.parent.mkdir(exist_ok=True)
    text='[Unit]\nRequires=nvidia-daily-engine-update-recover.service\nAfter=nvidia-daily-engine-update-recover.service\n'
    if drop.exists() and drop.read_text()!=text: raise SystemExit('An unrelated router drop-in was preserved')
    drop.write_text(text)
    subprocess.run(['systemd-analyze','--user','verify',*[str(unit_dir/n) for n in UNITS]],check=True)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
    subprocess.run(['systemctl','--user','enable','nvidia-daily-engine-update-recover.service'],check=True)
    subprocess.run(['systemctl','--user','start','nvidia-daily-engine-update-recover.service'],check=True)
    # This restart loads only the new router idle-age/reservation integration.
    # Recheck idle immediately before it; no engine or DSH service is restarted.
    h=health()
    if any(h.get(k) for k in ('busy','queued','loading_model','active_model','admission_active')):
        raise SystemExit('A client became active; router reload and timer activation deferred.')
    subprocess.run(['systemctl','--user','restart','nvidia-model-router.service'],check=True)
    for _ in range(60):
        try:
            h=health()
            if 'idle_for_s' in h:break
        except OSError:pass
        time.sleep(1)
    else:raise SystemExit('Router idle telemetry did not become ready; timer remains disabled')
    subprocess.run(['systemctl','--user','enable','--now','nvidia-daily-engine-update.timer'],check=True)
    details=subprocess.check_output(['systemctl','--user','show','nvidia-daily-engine-update.timer','-p','ActiveState','-p','NextElapseUSecRealtime'],text=True)
    print(details.strip())
    print('Timer enabled. No candidate build or GPU update was started by installation.')


if __name__=='__main__':main()
