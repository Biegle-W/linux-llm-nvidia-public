#!/usr/bin/env python3
"""Visible desktop consoles for guarded workers and foreground test harnesses."""
import argparse
import fcntl
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'data/visible-terminals'
BACKEND_UNITS = {'llm-test-qwen27b.service', 'llm-router-worker.service'}


def service_state(unit):
    result = subprocess.run(['systemctl', '--user', 'show', unit,
                             '-p', 'ActiveState', '-p', 'InvocationID'],
                            capture_output=True, text=True)
    return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)


def backend_finished(unit, seen_invocation, state):
    """Only backend viewers follow worker lifetime; router/DSH/harnesses stay open."""
    return (unit in BACKEND_UNITS and bool(seen_invocation)
            and (state.get('ActiveState') not in ('active', 'activating')
                 or state.get('InvocationID') != seen_invocation))


def close_registered_monitor(unit):
    """Retire an explicitly selected project viewer, never its service or terminal app."""
    if not unit.endswith('.service') or '/' in unit:
        raise ValueError('Expected a service name')
    marker = STATE / (unit + '.json')
    try:
        record = json.loads(marker.read_text())
        pid = record['pid']
        command = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
        if (str(Path(__file__).resolve()).encode() not in command
                or b'watch' not in command or unit.encode() not in command):
            return
        os.kill(pid, signal.SIGTERM)
        for _ in range(40):
            if not (Path('/proc') / str(pid)).exists():
                break
            time.sleep(.1)
    except (OSError, ValueError, KeyError, TypeError):
        return


def close_backend_monitor(unit):
    """Ordinary engine teardown cannot close router/DSH/harness viewers."""
    if unit in BACKEND_UNITS:
        close_registered_monitor(unit)


def desktop_env():
    env = dict(os.environ)
    result = subprocess.run(['systemctl', '--user', 'show-environment'], capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        key, _, value = line.partition('=')
        if key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY'):
            env[key] = value
    return env


def terminal_command(title, command):
    """Native iconic startup, before mapping; no focus-and-minimize race."""
    config = json.loads((ROOT / 'config/terminal-runtime.json').read_text())
    for relative, expected in config['sha256'].items():
        path = ROOT / relative
        if not path.resolve().is_relative_to(ROOT.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Minimized terminal runtime changed; verify/reinstall before launch')
    return [str(ROOT / config['binary']), '-iconic', '-class', 'NvidiaLLMTerminal',
            '-T', title, '-geometry', '132x34', '-fa', 'Monospace', '-fs', '11',
            '-e', *command]


def launch_terminal(command):
    # Keep GUI consoles outside the inference worker's guarded cgroup.
    env = desktop_env()
    config = json.loads((ROOT / 'config/terminal-runtime.json').read_text())
    env['LD_LIBRARY_PATH'] = str(ROOT / config['library_directory']) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env['XAPPLRESDIR'] = str(ROOT / config['app_defaults_directory'])
    launcher = ['systemd-run', '--user', '--collect', '--quiet', '--unit=llm-terminal-' + uuid.uuid4().hex]
    for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY', 'LD_LIBRARY_PATH', 'XAPPLRESDIR'):
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
    if unit in BACKEND_UNITS and service_state(unit).get('ActiveState') not in ('active', 'activating'):
        close_backend_monitor(unit)
    try:
        previous = json.loads(marker.read_text())
        cmdline = Path(f"/proc/{previous['pid']}/cmdline").read_bytes()
        if b'visible_terminal.py' in cmdline and unit.encode() in cmdline:
            return
    except (OSError, ValueError, KeyError):
        pass
    command = ['/usr/bin/python3',
               str(Path(__file__).resolve()), 'watch', '--title', title, '--unit', unit]
    for log in logs:
        command += ['--log', str(log)]
    launch_terminal(terminal_command(title, command))
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
        marker.write_text(json.dumps({'pid': os.getpid(), 'unit': args.unit,
                                     'window_id': os.environ.get('WINDOWID'),
                                     'starts_minimized': True}))
        print(f'{args.title}\nLive guarded-service console: {args.unit}', flush=True)
        print(f'Stop backend: systemctl --user stop {args.unit}\nClosing this console does not stop the worker.\n', flush=True)
        if args.unit == 'llm-router-worker.service':
            print('Native web UI: http://127.0.0.1:10000/ (open when convenient)', flush=True)
        elif args.unit == 'nvidia-dsh.service':
            print('Harness UI: http://127.0.0.1:3080/ (open when convenient)', flush=True)
        children = []
        def terminate(*_):
            raise SystemExit(0)
        signal.signal(signal.SIGTERM, terminate)
        seen_invocation = None
        startup_deadline = time.monotonic() + 30
        initial = service_state(args.unit)
        if initial.get('ActiveState') in ('active', 'activating'):
            seen_invocation = initial.get('InvocationID')
        try:
            children.append(subprocess.Popen(['journalctl', '--user', '-u', args.unit, '-n', '30', '-f', '-o', 'cat']))
            if args.log:
                children.append(subprocess.Popen(['tail', '-n', '30', '-F', '--', *args.log]))
            while all(child.poll() is None for child in children):
                current = service_state(args.unit)
                if args.unit in BACKEND_UNITS and not seen_invocation and time.monotonic() > startup_deadline:
                    print('Backend never started; closing its pending console.', flush=True)
                    break
                if backend_finished(args.unit, seen_invocation, current):
                    print('Owned backend stopped or switched; closing this backend console.', flush=True)
                    break
                if current.get('ActiveState') in ('active', 'activating'):
                    seen_invocation = current.get('InvocationID') or seen_invocation
                time.sleep(.5)
        except KeyboardInterrupt:
            pass
        finally:
            for child in children:
                child.terminate()
            for child in children:
                child.wait()
            try:
                if json.loads(marker.read_text()).get('pid') == os.getpid():
                    marker.unlink(missing_ok=True)
            except (OSError, ValueError):
                pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['open', 'watch', 'run', 'foreground', 'launch', 'selection'])
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
        if args.mode in ('run', 'launch'):
            STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
            receipt = STATE / ('harness-' + uuid.uuid4().hex + '.json')
            launch_terminal(terminal_command(args.title, [
                            '/usr/bin/python3', str(Path(__file__).resolve()),
                            'foreground' if args.mode == 'run' else 'selection',
                            '--title', args.title, '--receipt', str(receipt), '--', *command]))
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
                args.receipt.write_text(json.dumps({'pid': os.getpid(), 'command': command,
                                                   'visible_tty': os.ttyname(sys.stdout.fileno()),
                                                   'window_id': os.environ.get('WINDOWID'),
                                                   'starts_minimized': True}))
            print(args.title, flush=True)
            result = subprocess.run(command, cwd=ROOT)
            print(f'\nFinished with exit code {result.returncode}.', flush=True)
            if args.mode == 'foreground' or result.returncode:
                input('Press Enter to close this terminal. ')
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
