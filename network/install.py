#!/usr/bin/env python3
"""Install the NVIDIA router, DSH services, commands and desktop entries."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
MARKER = '# Managed by linux-llm-nvidia'
sys.path.insert(0, str(ROOT / 'scripts'))
from inference_policy import load_policy


def write_managed(path, text, mode=0o644):
    if path.exists() and MARKER not in path.read_text():
        raise RuntimeError('Refusing to replace an unrelated file: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(mode)


def remove_managed_menu(path):
    if path.is_file() and not path.is_symlink():
        text = path.read_text()
        if MARKER in text and str(ROOT) in text:
            path.unlink()


def engine_desktop(engine, label, icon):
    web = ' --web' if engine in ('strata', 'maya') else ''
    return (MARKER + '\n[Desktop Entry]\nVersion=1.0\nType=Application\nName=' + label + '\n'
            'Comment=Select a guarded backend in a visible minimized terminal\n'
            f'Exec=/usr/bin/python3 "{ROOT}/scripts/visible_terminal.py" launch --title "{label} selection" -- '
            f'/usr/bin/python3 "{ROOT}/scripts/router_client.py" --engine {engine} --desktop{web}\n'
            f'Icon={icon}\nTerminal=false\nCategories=Development;\n')


def api_service_units(root=ROOT):
    root=Path(root)
    result={}
    for name,description,entry,dependency in [
        ('nvidia-model-hub','NVIDIA private guarded model hub','hub.py',''),
        ('nvidia-model-router','NVIDIA authenticated API gateway','api.py','After=nvidia-model-hub.service\nWants=nvidia-model-hub.service\n')]:
        result[name]=(MARKER+'\n[Unit]\nDescription='+description+'\n'+dependency+'\n[Service]\n'
                      'Type=simple\nExecStart=/usr/bin/python3 "'+str(root/'network'/entry)+'"\nWorkingDirectory='+str(root)+'\n'
                      'Environment=PYTHONUNBUFFERED=1\nEnvironment=NVIDIA_API_ONLY=1\nUMask=0077\n'
                      'KillMode=process\nRestart=on-failure\nRestartSec=5\nNoNewPrivileges=true\nMemoryMax=1G\n'
                      '\n[Install]\nWantedBy=default.target\n')
    return result


def dsh_service_unit(root=ROOT):
    """The optional loopback client service runs without a desktop session."""
    root = Path(root)
    return (MARKER+'\n[Unit]\nDescription=DeepSeek Harness client for NVIDIA API\n'
            'After=nvidia-model-router.service\nWants=nvidia-model-router.service\n\n[Service]\nType=simple\n'
            'ExecStart="'+str(root/'dsh/run')+'" web --host 127.0.0.1 --port 3080 --no-open\nWorkingDirectory='+str(root/'data/dsh-workspace')+'\n'
            'Environment=PYTHONUNBUFFERED=1\nEnvironment=NVIDIA_DSH_HEADLESS=1\nUMask=0077\nRestart=on-failure\nRestartSec=5\nNoNewPrivileges=true\nMemoryMax=2G\n'
            'StandardOutput=append:'+str(root/'data/dsh-web.log')+'\n'
            'StandardError=append:'+str(root/'data/dsh-web.log')+'\n'
            '\n[Install]\nWantedBy=default.target\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-clients',action='store_true',help='also install/start the optional DSH client and desktop selectors')
    args=parser.parse_args()
    os.umask(0o077)
    tail = json.loads(subprocess.check_output(['tailscale', 'status', '--json'], text=True))
    if tail.get('BackendState') != 'Running':
        raise SystemExit('Connect Tailscale before installing network listeners.')
    ts = next(x for x in tail['Self']['TailscaleIPs'] if ':' not in x)
    data = ROOT / 'data/router';data.mkdir(parents=True, exist_ok=True)
    (ROOT / 'data/dsh-workspace').mkdir(parents=True, exist_ok=True)
    (data / 'access.json').write_text(json.dumps({'listen': ['127.0.0.1', ts], 'port': 10100,
                       'key_file': str(ROOT / 'data/local-api-key'),
                       'idle_timeout_s': load_policy()['idle_timeout_s'], 'lifecycle_telemetry': True, 'hub_port':10101, 'api_only':True}, indent=2) + '\n')
    (data / 'access.json').chmod(0o600)
    key = ROOT / 'data/local-api-key'
    if key.stat().st_mode & 0o077 or len(key.read_text().strip()) < 32:
        raise SystemExit('A strong owner-only local API key is required.')
    units=api_service_units()
    if args.with_clients:
        units['nvidia-dsh'] = dsh_service_unit()
    for name,text in units.items():
        write_managed(Path.home()/'.config/systemd/user'/(name+'.service'),text)
    if not args.with_clients:
        subprocess.run(['systemctl','--user','daemon-reload'],check=True)
        subprocess.run(['systemctl','--user','enable','--now','nvidia-model-hub.service','nvidia-model-router.service'],check=True)
        print('Installed headless NVIDIA API gateway and private model hub; clients remain separate.')
        return
    engines = {'hyperqwen': 'HyperQwen vLLM', 'sglang': 'SGLang', 'strata': 'Strata', 'maya': 'Maya'}
    for engine, label in engines.items():
        icon = ROOT / 'assets/icons' / (engine + ('.png' if engine == 'hyperqwen' else '.svg'))
        desktop = engine_desktop(engine, label, icon)
        name = label.replace(' ', '-') + '.desktop'
        write_managed(Path.home() / 'Desktop' / name, desktop, 0o755)
        remove_managed_menu(Path.home() / 'Desktop' / ('LLM-' + engine + '.desktop'))
        remove_managed_menu(Path.home() / '.local/share/applications' / ('LLM-' + engine + '.desktop'))
        remove_managed_menu(Path.home() / '.local/share/applications' / name)
        command = '#!/bin/sh\n' + MARKER + '\nexec /usr/bin/python3 ' + shlex.quote(str(ROOT / 'scripts/router_client.py')) + ' --engine ' + engine + ' "$@"\n'
        write_managed(Path.home() / '.local/bin' / ('llm-' + engine), command, 0o755)
    desktop = (MARKER + '\n[Desktop Entry]\nVersion=1.0\nType=Application\nName=DeepSeek Harness (DSH)\n'
               'Comment=Open the local multi-engine DeepSeek Harness\n'
               f'Exec=/usr/bin/python3 "{ROOT}/scripts/open_dsh.py"\n'
               f'Icon={ROOT}/assets/icons/dsh.svg\nTerminal=false\nCategories=Development;\n')
    write_managed(Path.home() / 'Desktop/DSH.desktop', desktop, 0o755)
    remove_managed_menu(Path.home() / '.local/share/applications/DSH.desktop')
    write_managed(Path.home() / '.local/bin/dsh', '#!/bin/sh\n' + MARKER + '\nif [ "$#" -eq 0 ]; then\n  exec /usr/bin/python3 ' + shlex.quote(str(ROOT / 'scripts/open_dsh.py')) + '\nfi\nexec ' + shlex.quote(str(ROOT / 'dsh/run')) + ' "$@"\n', 0o755)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', '--user', 'enable', '--now', 'nvidia-model-hub.service', 'nvidia-model-router.service', 'nvidia-dsh.service'], check=True)
    for path in [*(Path.home() / 'Desktop' / (label.replace(' ', '-') + '.desktop') for label in engines.values()), Path.home() / 'Desktop/DSH.desktop']:
        subprocess.run(['gio', 'set', str(path), 'metadata::trusted', 'true'], capture_output=True)
    print('Installed router, DSH, four engine shortcuts, and DSH shortcut.')
    print('Loopback API: http://127.0.0.1:10100/v1')
    print('Tailscale API: http://' + ts + ':10100/v1')


if __name__ == '__main__':
    main()
