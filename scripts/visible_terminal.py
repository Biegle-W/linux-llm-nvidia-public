#!/usr/bin/env python3
"""Visible desktop consoles for guarded workers and foreground test harnesses."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'data/visible-terminals'


def desktop_env():
    env = dict(os.environ)
    result = subprocess.run(['systemctl', '--user', 'show-environment'], capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        key, _, value = line.partition('=')
        if key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY'):
            env[key] = value
    return env


def launch_terminal(command):
    # Keep GUI consoles outside the inference worker's guarded cgroup.
    env = desktop_env()
    launcher = ['systemd-run', '--user', '--collect', '--quiet', '--unit=llm-terminal-' + uuid.uuid4().hex]
    for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY'):
        if key in env:
            launcher.append('--setenv=' + key + '=' + env[key])
    subprocess.Popen([*launcher, *command], env=env, start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_monitor(title, unit, logs=()):
    """Open one console per service, and require a viewer-start handshake."""
    if not unit.endswith('.service') or '/' in unit:
        raise ValueError('Expected a user service name')
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = STATE / (unit + '.json')
    try:
        previous = json.loads(marker.read_text())
        cmdline = Path(f"/proc/{previous['pid']}/cmdline").read_bytes()
        if b'visible_terminal.py' in cmdline and unit.encode() in cmdline:
            return
    except (OSError, ValueError, KeyError):
        pass
    command = ['/usr/bin/ptyxis', '--new-window', '--title', title, '--', '/usr/bin/python3',
               str(Path(__file__).resolve()), 'watch', '--title', title, '--unit', unit]
    for log in logs:
        command += ['--log', str(log)]
    launch_terminal(command)
    for _ in range(100):
        try:
            current = json.loads(marker.read_text())
            os.kill(current['pid'], 0)
            return
        except (OSError, ValueError, KeyError):
            time.sleep(.1)
    raise RuntimeError('Visible terminal did not start; refusing a hidden launch')


def watch(args):
    if not sys.stdout.isatty():
        raise SystemExit('Backend console must run in a visible terminal')
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = STATE / (args.unit + '.json')
    with (STATE / (args.unit + '.lock')).open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        marker.write_text(json.dumps({'pid': os.getpid(), 'unit': args.unit}))
        print(f'{args.title}\nLive guarded-service console: {args.unit}', flush=True)
        print(f'Stop backend: systemctl --user stop {args.unit}\nClosing this console does not stop the worker.\n', flush=True)
        children = []
        try:
            children.append(subprocess.Popen(['journalctl', '--user', '-u', args.unit, '-n', '30', '-f', '-o', 'cat']))
            if args.log:
                children.append(subprocess.Popen(['tail', '-n', '30', '-F', '--', *args.log]))
            while all(child.poll() is None for child in children):
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            for child in children:
                child.terminate()
            for child in children:
                child.wait()
            marker.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['open', 'watch', 'run', 'foreground'])
    parser.add_argument('--title', default='Local LLM')
    parser.add_argument('--unit')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--log', action='append', default=[])
    args, args_command = parser.parse_known_args()
    args.command = args_command
    if args.mode in ('open', 'watch'):
        if not args.unit:
            parser.error('--unit is required')
        if args.mode == 'open':
            open_monitor(args.title, args.unit, args.log)
        else:
            watch(args)
    else:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command:
            parser.error('a command is required after --')
        if args.mode == 'run':
            STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
            receipt = STATE / ('harness-' + uuid.uuid4().hex + '.json')
            launch_terminal(['/usr/bin/ptyxis', '--new-window', '--title', args.title, '--',
                            '/usr/bin/python3', str(Path(__file__).resolve()), 'foreground', '--title', args.title, '--receipt', str(receipt),
                            '--', *command])
            for _ in range(100):
                if receipt.exists():
                    print('Visible harness started; receipt:', receipt)
                    return
                time.sleep(.1)
            raise RuntimeError('Visible harness terminal did not start')
        else:
            if not sys.stdout.isatty():
                raise SystemExit('Harness must run in a visible terminal')
            if args.receipt:
                args.receipt.write_text(json.dumps({'pid': os.getpid(), 'command': command, 'visible_tty': os.ttyname(sys.stdout.fileno())}))
            print(args.title, flush=True)
            result = subprocess.run(command, cwd=ROOT)
            print(f'\nFinished with exit code {result.returncode}.', flush=True)
            input('Press Enter to close this terminal. ')
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
