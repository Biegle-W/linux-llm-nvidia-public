#!/usr/bin/env python3
"""Visible desktop consoles for guarded workers and foreground test harnesses."""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
import signal
import shlex
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


def viewer_finished(unit, seen_invocation, state):
    """End confirmed finished viewers; persistent services can keep their live console."""
    if not seen_invocation:
        return False
    if state.get('ActiveState') in ('inactive', 'failed'):
        return True
    current = state.get('InvocationID')
    return bool(unit in BACKEND_UNITS and current and current != seen_invocation)


def backend_finished(unit, seen_invocation, state):
    """Backend teardown remains scoped; it cannot retire router/DSH viewers."""
    return unit in BACKEND_UNITS and viewer_finished(unit, seen_invocation, state)


def pending_viewer_expired(seen_invocation, state, deadline, now):
    return (not seen_invocation and now > deadline
            and state.get('ActiveState') in ('inactive', 'failed'))


def write_receipt(path, record):
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(json.dumps(record) + '\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run_foreground(command, title, receipt, starts_minimized=False):
    """Keep a real child PTY, durable output/exit status, and no post-exit prompt."""
    receipt.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    transcript = receipt.with_suffix('.log')
    fd = os.open(transcript, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    record = {'pid': os.getpid(), 'command': command,
              'visible_tty': os.ttyname(sys.stdout.fileno()),
              'window_id': os.environ.get('WINDOWID'), 'starts_minimized': starts_minimized,
              'state': 'running', 'started_at': time.time(), 'transcript': str(transcript)}
    write_receipt(receipt, record)
    print(title, flush=True)
    code = 127
    try:
        # util-linux script preserves interactive selectors and isatty-dependent commands.
        # Its --return propagates failure too; the transcript is private and remains on disk.
        env = dict(os.environ, SHELL='/bin/sh')
        result = subprocess.run(['/usr/bin/script', '--quiet', '--return', '--flush',
                                 '--command', shlex.join(command), str(transcript)],
                                cwd=ROOT, env=env)
        code = result.returncode
    except OSError as error:
        with transcript.open('a') as stream:
            stream.write('Launch failed: ' + str(error) + '\n')
        print('Launch failed; details saved in the terminal transcript.', flush=True)
    except KeyboardInterrupt:
        code = 130
    finally:
        record.update(state='finished', exit_code=code, finished_at=time.time())
        write_receipt(receipt, record)
    print(f'\nFinished with exit code {code}; transcript: {transcript}', flush=True)
    return code


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


def terminal_command(title, command, minimized=False):
    """Attention tasks map normally; backend monitors request native iconic startup."""
    config = json.loads((ROOT / 'config/terminal-runtime.json').read_text())
    for relative, expected in config['sha256'].items():
        path = ROOT / relative
        if not path.resolve().is_relative_to(ROOT.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Minimized terminal runtime changed; verify/reinstall before launch')
    return [str(ROOT / config['binary']), *(['-iconic'] if minimized else []), '-class', 'NvidiaLLMTerminal',
            '-T', title, '-geometry', '132x34', '-fa', 'Monospace', '-fs', '11',
            '-e', *command]


def focus_terminal(window_id):
    """Restore and activate an owned attention window; backend monitors never call this."""
    env = desktop_env()
    old_auth = os.environ.get('XAUTHORITY')
    if env.get('XAUTHORITY'):
        os.environ['XAUTHORITY'] = env['XAUTHORITY']
    x = ctypes.CDLL('libX11.so.6')
    x.XOpenDisplay.argtypes = [ctypes.c_char_p]; x.XOpenDisplay.restype = ctypes.c_void_p
    x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]; x.XDefaultRootWindow.restype = ctypes.c_ulong
    x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; x.XInternAtom.restype = ctypes.c_ulong
    x.XMapRaised.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x.XRaiseWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x.XSetInputFocus.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    x.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)), ctypes.POINTER(ctypes.c_uint)]
    x.XFlush.argtypes = [ctypes.c_void_p]; x.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x.XFree.argtypes = [ctypes.c_void_p]
    class Data(ctypes.Union):
        _fields_ = [('l', ctypes.c_long * 5)]
    class Message(ctypes.Structure):
        _fields_ = [('type', ctypes.c_int), ('serial', ctypes.c_ulong), ('send_event', ctypes.c_int),
                    ('display', ctypes.c_void_p), ('window', ctypes.c_ulong), ('message_type', ctypes.c_ulong),
                    ('format', ctypes.c_int), ('data', Data)]
    class Event(ctypes.Union):
        _fields_ = [('message', Message), ('pad', ctypes.c_long * 24)]
    x.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.POINTER(Event)]
    x.XGetWindowProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long,
        ctypes.c_long, ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
    try:
        display = x.XOpenDisplay(env.get('DISPLAY', '').encode() or None)
    finally:
        if old_auth is None:
            os.environ.pop('XAUTHORITY', None)
        else:
            os.environ['XAUTHORITY'] = old_auth
    if not display:
        raise RuntimeError('Cannot activate attention terminal: no X11 display')
    try:
        root = x.XDefaultRootWindow(display); window = int(window_id)
        atom = x.XInternAtom(display, b'_NET_ACTIVE_WINDOW', 0)
        x.XMapRaised(display, window)
        event = Event(); event.message.type = 33; event.message.display = display
        event.message.window = window; event.message.message_type = atom; event.message.format = 32
        event.message.data.l[0] = 2  # User-requested activation of this owned terminal.
        x.XSendEvent(display, root, 0, (1 << 20) | (1 << 19), ctypes.byref(event)); x.XFlush(display)
        for attempt in range(40):
            # Some reparenting window managers ignore the activation message.
            # Focus only this owned attention client and raise its own frame.
            if attempt == 10:
                tree_root = ctypes.c_ulong(); parent = ctypes.c_ulong()
                children = ctypes.POINTER(ctypes.c_ulong)(); nchildren = ctypes.c_uint()
                if x.XQueryTree(display, window, ctypes.byref(tree_root), ctypes.byref(parent),
                                ctypes.byref(children), ctypes.byref(nchildren)):
                    frame = parent.value if parent.value != root else window
                    x.XRaiseWindow(display, frame)
                if children:
                    x.XFree(children)
                x.XSetInputFocus(display, window, 2, 0)  # RevertToParent, CurrentTime.
                x.XFlush(display)
            actual = ctypes.c_ulong(); fmt = ctypes.c_int(); count = ctypes.c_ulong(); left = ctypes.c_ulong()
            value = ctypes.POINTER(ctypes.c_ubyte)()
            rc = x.XGetWindowProperty(display, root, atom, 0, 1, 0, 0, ctypes.byref(actual), ctypes.byref(fmt),
                ctypes.byref(count), ctypes.byref(left), ctypes.byref(value))
            active = ctypes.cast(value, ctypes.POINTER(ctypes.c_ulong))[0] if rc == 0 and value and count.value else 0
            if value:
                x.XFree(value)
            if active == window:
                return True
            time.sleep(.05)
        raise RuntimeError('Window manager did not confirm attention-terminal activation')
    finally:
        x.XCloseDisplay(display)


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
    if service_state(unit).get('ActiveState') in ('inactive', 'failed'):
        close_registered_monitor(unit)
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
    launch_terminal(terminal_command(title, command, minimized=True))
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
                if pending_viewer_expired(seen_invocation, current, startup_deadline, time.monotonic()):
                    print('Service never started; closing its pending console.', flush=True)
                    break
                if viewer_finished(args.unit, seen_invocation, current):
                    print('Owned service stopped or backend switched; closing its console.', flush=True)
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
    presentation = parser.add_mutually_exclusive_group()
    presentation.add_argument('--attention', action='store_true', help='bring a command requiring input/authentication to the front')
    presentation.add_argument('--minimized', action='store_true', help='open without taking focus')
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
            minimized = args.minimized or (args.mode == 'run' and not args.attention)
            STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
            receipt = STATE / ('harness-' + uuid.uuid4().hex + '.json')
            launch_terminal(terminal_command(args.title, [
                            '/usr/bin/python3', str(Path(__file__).resolve()),
                            'foreground' if args.mode == 'run' else 'selection',
                            '--title', args.title, '--receipt', str(receipt),
                            *(['--minimized'] if minimized else []), '--', *command], minimized=minimized))
            for _ in range(100):
                if receipt.exists():
                    record = json.loads(receipt.read_text())
                    if record.get('state') == 'running' and not minimized:
                        focus_terminal(record['window_id'])
                    print('Visible ' + ('minimized' if minimized else 'attention') + ' harness started; receipt:', receipt)
                    return
                time.sleep(.1)
            raise RuntimeError('Visible harness terminal did not start')
        else:
            if not sys.stdout.isatty():
                raise SystemExit('Harness must run in a visible terminal')
            receipt = args.receipt or STATE / ('harness-' + uuid.uuid4().hex + '.json')
            if args.minimized:
                raise SystemExit(run_foreground(command, args.title, receipt, starts_minimized=True))
            raise SystemExit(run_foreground(command, args.title, receipt))



if __name__ == '__main__':
    main()
