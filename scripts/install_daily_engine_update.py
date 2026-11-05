#!/usr/bin/env python3
"""Install the user's daily 03:00 NVIDIA updater without launching an update now."""
import json
import hashlib
import shutil
import os
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
UNITS = ('nvidia-daily-engine-update.service','nvidia-daily-engine-update-recover.service','nvidia-daily-engine-update.timer')



def managed_preimage(name,text,root=ROOT):
    if name=='nvidia-daily-engine-update.timer':
        return '[Timer]'in text and 'Unit=nvidia-daily-engine-update.service'in text
    if name not in UNITS:return False
    return 'WorkingDirectory='+str(root)in text and str(root/'scripts/daily_')in text


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
    state=subprocess.check_output(['systemctl','--user','show','nvidia-daily-engine-update.service','-p','ActiveState','--value'],text=True).strip()
    if state in ('active','activating','deactivating'):raise SystemExit('An updater is running; preserve its jobs and retry later.')
    backup=ROOT/'data/daily-update/install-preimages'/str(time.time_ns());backup.mkdir(mode=0o700,parents=True,exist_ok=False)
    rendered={name:(ROOT/'network/systemd'/name).read_text().replace('@ROOT@',str(ROOT))for name in UNITS}
    # Validate the entire replacement set before writing any file.
    for name,new in rendered.items():
        p=unit_dir/name
        if p.is_symlink():raise SystemExit('An updater unit symlink was preserved: '+name)
        if p.exists()and p.read_text()!=new and not managed_preimage(name,p.read_text()):
            raise SystemExit('An unrelated updater unit was preserved: '+name)
    for name,new in rendered.items():
        p=unit_dir/name
        if p.exists()and p.read_text()!=new:
            shutil.copy2(p,backup/name)
            (backup/(name+'.sha256')).write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'\n')
        temporary=p.with_suffix(p.suffix+'.install-tmp');temporary.write_text(new);temporary.replace(p)
    drop=unit_dir/'nvidia-model-router.service.d/30-daily-update-recovery.conf';drop.parent.mkdir(exist_ok=True)
    text='[Unit]\nRequires=nvidia-daily-engine-update-recover.service\nAfter=nvidia-daily-engine-update-recover.service\n'
    if drop.exists() and drop.read_text()!=text: raise SystemExit('An unrelated router drop-in was preserved')
    drop.write_text(text)
    subprocess.run(['systemd-analyze','--user','verify',*[str(unit_dir/n) for n in UNITS]],check=True)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
    subprocess.run(['systemctl','--user','enable','nvidia-daily-engine-update-recover.service'],check=True)
    subprocess.run(['systemctl','--user','start','nvidia-daily-engine-update-recover.service'],check=True)
    # The existing API/hub already expose idle/reservation telemetry. Installing
    # updater units does not require restarting either service or resetting age.
    h=health()
    if 'idle_for_s'not in h or any(h.get(k)for k in ('busy','queued','loading_model','active_model','admission_active')):
        raise SystemExit('Admission changed; timer activation deferred without restarting serving.')
    subprocess.run(['systemctl','--user','enable','--now','nvidia-daily-engine-update.timer'],check=True)
    details=subprocess.check_output(['systemctl','--user','show','nvidia-daily-engine-update.timer','-p','ActiveState','-p','NextElapseUSecRealtime'],text=True)
    print(details.strip())
    print('Timer enabled. No candidate build or GPU update was started by installation.')


if __name__=='__main__':main()
