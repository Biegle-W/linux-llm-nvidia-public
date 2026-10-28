#!/usr/bin/env python3
"""Install the NVIDIA router, DSH services, commands and desktop entries."""
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


def main():
    os.umask(0o077)
    tail = json.loads(subprocess.check_output(['tailscale', 'status', '--json'], text=True))
    if tail.get('BackendState') != 'Running':
        raise SystemExit('Connect Tailscale before installing network listeners.')
    ts = next(x for x in tail['Self']['TailscaleIPs'] if ':' not in x)
    data = ROOT / 'data/router';data.mkdir(parents=True, exist_ok=True)
    (ROOT / 'data/dsh-workspace').mkdir(parents=True, exist_ok=True)
    (data / 'access.json').write_text(json.dumps({'listen': ['127.0.0.1', ts], 'port': 10100,
                       'key_file': str(ROOT / 'data/local-api-key'),
                       'idle_timeout_s': load_policy()['idle_timeout_s'], 'lifecycle_telemetry': True}, indent=2) + '\n')
    (data / 'access.json').chmod(0o600)
    key = ROOT / 'data/local-api-key'
    if key.stat().st_mode & 0o077 or len(key.read_text().strip()) < 32:
        raise SystemExit('A strong owner-only local API key is required.')
    services = {
      'nvidia-model-router': ('NVIDIA model and engine OpenAI router',
          f'/usr/bin/python3 "{ROOT}/network/router.py"', '', '1G'),
      'nvidia-dsh': ('DeepSeek Harness for NVIDIA local models',
          f'"{ROOT}/dsh/run" web --host 127.0.0.1 --port 3080 --no-open',
          'After=nvidia-model-router.service\nWants=nvidia-model-router.service\n', '2G')}
    for name, (description, command, after, memory) in services.items():
        text = (MARKER + '\n[Unit]\nDescription=' + description + '\n' + after + '\n[Service]\n'
                'Type=simple\nExecStart=' + command + '\nWorkingDirectory=' + str(ROOT / 'data/dsh-workspace') + '\n'
                'Environment=PYTHONUNBUFFERED=1\nUMask=0077\nRestart=on-failure\nRestartSec=5\n'
                'NoNewPrivileges=true\nMemoryMax=' + memory + '\n')
        if name == 'nvidia-dsh':
            log = ROOT / 'data/dsh-web.log';log.touch(mode=0o600, exist_ok=True)
            text += 'StandardOutput=append:' + str(log) + '\nStandardError=append:' + str(log) + '\n'
        text += '\n[Install]\nWantedBy=default.target\n'
        write_managed(Path.home() / '.config/systemd/user' / (name + '.service'), text)
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
    subprocess.run(['systemctl', '--user', 'enable', '--now', 'nvidia-model-router.service', 'nvidia-dsh.service'], check=True)
    for path in [*(Path.home() / 'Desktop' / (label.replace(' ', '-') + '.desktop') for label in engines.values()), Path.home() / 'Desktop/DSH.desktop']:
        subprocess.run(['gio', 'set', str(path), 'metadata::trusted', 'true'], capture_output=True)
    print('Installed router, DSH, four engine shortcuts, and DSH shortcut.')
    print('Loopback API: http://127.0.0.1:10100/v1')
    print('Tailscale API: http://' + ts + ':10100/v1')


if __name__ == '__main__':
    main()
