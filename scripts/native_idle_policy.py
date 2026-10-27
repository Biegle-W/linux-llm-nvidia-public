#!/usr/bin/env python3
"""Prepare/apply a narrow GPU-lock-aware idle adapter to pinned native controls."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

MARKER = '# Managed NVIDIA idle reservation'


def transform(text, family):
    newline = '\r\n' if '\r\n' in text else '\n'
    source = text.replace('\r\n', '\n')
    if MARKER in source:
        return text
    tree = ast.parse(source)
    service = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Service')
    method = next(node for node in service.body if isinstance(node, ast.FunctionDef) and node.name == 'unload')
    lines = source.splitlines(keepends=True)
    body = ''.join(lines[method.lineno - 1:method.end_lineno])
    assert body.count('        try:\n') == 1
    body = body.replace('        try:\n', '        idle_owner = None\n        lock_path = getattr(self, "idle_lock_path", None)\n        try:\n', 1)
    anchor = '            self.engine.close()' if family == 'maya' else '            self.engine.unload()'
    assert body.count(anchor) == 1
    reservation = '''            # Managed NVIDIA idle reservation: FIFO ownership makes native request admission atomic.
            if idle_for is not None and lock_path:
                idle_owner = {"owner": "native-idle", "pid": os.getpid(), "nonce": time.monotonic_ns()}
                try:
                    with Path(lock_path).open("x") as stream:
                        json.dump(idle_owner, stream)
                except FileExistsError:
                    idle_owner = None
                    return "busy"
'''
    if family == 'maya':
        reservation += '''            if idle_owner is not None and self.vision is not None and hasattr(self.vision, "_stop"):
                with self.vision.lock:
                    self.vision._stop()
'''
    body = body.replace(anchor, reservation + anchor, 1)
    old_activity = '            if idle_for is not None and time.time() - (self.last_request_at or self.started_at) < idle_for:'
    assert body.count(old_activity) == 1
    body = body.replace(old_activity, '''            managed_last = self.last_request_at or self.started_at
            activity_path = getattr(self, "idle_activity_path", None)
            if idle_for is not None and activity_path:
                try:
                    managed_last = max(managed_last, float(Path(activity_path).read_text()))
                except (OSError, ValueError):
                    return "busy"
            if idle_for is not None and time.time() - managed_last < idle_for:''', 1)
    old = '        finally:\n            self.fifo.release()'
    assert body.count(old) == 1
    body = body.replace(old, '''        finally:
            try:
                if idle_owner is not None and json.loads(Path(lock_path).read_text()) == idle_owner:
                    Path(lock_path).unlink()
            except (OSError, ValueError):
                pass
            finally:
                self.fifo.release()''', 1)
    lines[method.lineno - 1:method.end_lineno] = [body]
    source = ''.join(lines)
    if family == 'maya':
        anchor = '    svc.idle_unload_s = max(0.0, a.idle_unload if a.idle_unload is not None else float(cfg.get("idle_unload_s") or 0))'
    else:
        anchor = '    svc.idle_unload_s = a.idle_unload if a.idle_unload is not None else float(cfg.get("idle_unload_s") or 0)'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '\n    svc.idle_lock_path = cfg.get("idle_lock_path")\n    svc.idle_activity_path = cfg.get("idle_activity_path")', 1)
    sleep = 'time.sleep(max(1.0, min(30.0, self.idle_unload_s / 4)))'
    assert source.count(sleep) == 1
    source = source.replace(sleep, 'time.sleep(max(1.0, min(5.0 if getattr(self, "idle_lock_path", None) else 30.0, self.idle_unload_s / 4)))', 1)
    status_anchor = '                now = time.time()\n                if s.get("busy"):'
    assert source.count(status_anchor) == 1
    loading = ('svc._engine_start.locked() or svc.reloading()' if family == 'maya'
               else 'svc.fifo.locked() and not s.get("busy")')
    source = source.replace(status_anchor, '                s["loading"] = bool(' + loading + ')\n' + status_anchor, 1)
    compile(source, '<native-idle-adapter>', 'exec')
    return source.replace('\n', newline)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--family', choices=['maya', 'strata'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    raw = args.source.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    patched = transform(raw.decode(), args.family).encode()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'before.py').write_bytes(raw)
    (args.output / 'after.py').write_bytes(patched)
    record = {'family': args.family, 'before_sha256': before,
              'after_sha256': hashlib.sha256(patched).hexdigest(), 'applied': False}
    if args.apply:
        if args.expected_sha256 != before:
            raise SystemExit('Review the current source hash before applying this adapter.')
        args.source.write_bytes(patched)
        record['applied'] = True
    (args.output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
