#!/usr/bin/env python3
"""Keep the scheduled coordinator in one visible foreground terminal until exit."""
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import time
import uuid
from visible_terminal import launch_terminal,terminal_command,desktop_env
ROOT=Path(__file__).resolve().parents[1]


def main():
    os.umask(0o077)
    env=desktop_env();settings=json.loads((ROOT/'config/daily-update.json').read_text())
    if not env.get('DISPLAY'):
        # Discovery is always safe headlessly. GPU work needs the explicit policy.
        args=sys.argv[1:]
        if settings.get('scheduled_visibility')!='guarded-headless' and '--check-only'not in args:
            print('No graphical desktop: discovery only; GPU updates deferred by visible-terminal policy.',flush=True)
            args=['--check-only']
        child=subprocess.Popen(['/usr/bin/python3',str(ROOT/'scripts/daily_engine_update.py'),*args])
        def cancel_child(*_):
            if child.poll() is None:child.terminate()
        signal.signal(signal.SIGTERM,cancel_child);signal.signal(signal.SIGINT,cancel_child)
        return child.wait()
    receipt=ROOT/'data/daily-update/consoles'/('coordinator-'+uuid.uuid4().hex+'.json')
    receipt.parent.mkdir(parents=True,exist_ok=True)
    command=['/usr/bin/python3',str(ROOT/'scripts/visible_terminal.py'),'foreground',
             '--title','NVIDIA daily engine update','--receipt',str(receipt),'--',
             '/usr/bin/python3',str(ROOT/'scripts/daily_engine_update.py'),*sys.argv[1:]]
    unit=launch_terminal(terminal_command('NVIDIA daily engine update',command,minimized=False),
        unit_properties=('MemoryHigh=6G','MemoryMax=8G','OOMPolicy=stop','Nice=10',
                         'IOSchedulingClass=best-effort','IOSchedulingPriority=7','TimeoutStopSec=600','KillMode=mixed'))
    def stop_owned(*_):
        subprocess.run(['systemctl','--user','stop',unit],check=False)
        raise SystemExit(143)
    signal.signal(signal.SIGTERM,stop_owned);signal.signal(signal.SIGINT,stop_owned)
    deadline=time.monotonic()+30
    while not receipt.exists():
        if time.monotonic()>deadline:raise RuntimeError('Visible updater terminal did not start; no hidden GPU work was launched')
        time.sleep(.2)
    while True:
        record=json.loads(receipt.read_text())
        if record.get('state')=='finished':return int(record['exit_code'])
        pid=record.get('pid')
        if pid and not Path('/proc',str(pid)).exists():raise RuntimeError('Updater terminal exited without a completion receipt; recovery remains responsible')
        time.sleep(1)


if __name__=='__main__':raise SystemExit(main())
