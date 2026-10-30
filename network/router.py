#!/usr/bin/env python3
"""Authenticated OpenAI model/engine router for the qualified NVIDIA catalog."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import signal
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit
from worker_manager import Workers, RouterError, profiles, ROOT
from inference_policy import load_policy
from backend_proxy import BackendProxy, rewrite_model_alias
import web_search

MAX_BODY = 32 * 1024 * 1024


def apply_request_defaults(data, profile):
    """Apply profile defaults while preserving explicit per-request overrides."""
    body = dict(data)
    for key, default in profile.get('request_defaults', {}).items():
        if isinstance(default, dict):
            actual = body.get(key)
            if actual is None:
                actual = {}
            if not isinstance(actual, dict):
                raise RouterError('Invalid request options: ' + key, 'bad_request', 400)
            body[key] = dict(default, **actual)
        elif key not in body:
            body[key] = default
    return body


def protocol_path(value):
    """Allow only endpoint shapes in optional diagnostics; never log arbitrary URLs."""
    try:
        path = urlsplit(value).path
    except ValueError:
        return '<other>'
    if path in ('/health','/router/select','/router/unload'):
        return path
    allowed = {'','v1','v2','api','openai','chat','completions','completion',
               'responses','response','models','messages','stream','generate'}
    if path.startswith('/') and len(path) <= 160 and all(part in allowed for part in path.split('/')):
        return path
    return '<other>'


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        # Optional protocol metadata only. Bodies, credentials, query strings,
        # arbitrary paths and client identities are never logged.
        if not getattr(self.server, 'protocol_diagnostics', False) or format != '"%s" %s %s':
            return
        try:
            status = int(args[1])
        except (IndexError, TypeError, ValueError):
            return
        method = self.command if self.command in ('GET','POST','HEAD','OPTIONS','PUT','DELETE') else 'OTHER'
        try:
            print(json.dumps({'event':'api_protocol','method':method,
                              'path':protocol_path(self.path),'status':status}), flush=True)
        except OSError:
            pass  # Diagnostics must not break a request.

    def reply(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        if status == 429:
            self.send_header('Retry-After', '5')
        if status == 401:
            self.send_header('WWW-Authenticate', 'Bearer realm="local-llm"')
        self.end_headers()
        self.wfile.write(payload)

    def error(self, status, message, code):
        self.reply(status, {'error': {'message': str(message).replace(self.server.key, '[redacted]'),
                                     'type': 'invalid_request_error' if status < 500 else 'backend_error',
                                     'code': code}})

    def auth(self):
        self.close_connection = True
        self.connection.settimeout(60)
        address = ipaddress.ip_address(self.client_address[0])
        if not any(address in net for net in self.server.allowed):
            self.error(403, 'Client network is not allowed.', 'network_denied')
            return False
        value = self.headers.get('Authorization', '')
        supplied = value[7:].encode() if value.startswith('Bearer ') else b''
        if not supplied or not hmac.compare_digest(supplied, self.server.key.encode()):
            self.error(401, 'A valid local API key is required.', 'invalid_api_key')
            return False
        return True

    def catalog(self):
        w = self.server.workers
        backend = w.backend_models() if w.active and w.loading is None else []
        ready = any(model.get('status', {}).get('value') != 'unloaded' for model in backend)
        return {p['id']: {'id': p['id'], 'object': 'model', 'created': 0, 'owned_by': 'local-nvidia',
                         'name': p['model'] + ' / ' + p['engine'], 'engine': p['engine'],
                         'quant': p['weight_quant'], 'context_window': p['allocated_context'],
                         'max_model_len': p['allocated_context'], 'auto_start': True,
                         'loaded': ready and w.active == p['id'] and w.loading is None}
                for p in profiles().values()}

    def do_GET(self):
        if not self.auth():
            return
        path = urlsplit(self.path).path
        if path == '/health':
            w = self.server.workers
            return self.reply(200, {'status': 'ok', 'active_model': w.active, 'loading_model': w.loading,
                                    'busy': w.busy, 'models': len(profiles()),
                                    'idle_unloading_model': getattr(w, 'idle_unloading', None),
                                    'idle_timeout_seconds': w.idle_timeout,
                                    'idle_for_s': max(0, time.monotonic() - w.last_activity),
                                    **w.request_status()})
        models = self.catalog()
        if path == '/v1/models':
            return self.reply(200, {'object': 'list', 'data': list(models.values())})
        if path.startswith('/v1/models/'):
            model = models.get(unquote(path[len('/v1/models/'):]))
            return self.reply(200, model) if model else self.error(404, 'Unknown model.', 'model_not_found')
        self.error(404, 'Unknown endpoint.', 'not_found')

    def read_body(self):
        if len(self.headers.get_all('Content-Length') or []) != 1:
            raise RouterError('One content length is required.', 'bad_request', 400)
        if self.headers.get('Transfer-Encoding'):
            raise RouterError('Chunked request bodies are unsupported.', 'bad_request', 400)
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise RouterError('Invalid content length.', 'bad_request', 400)
        if not 0 < length <= MAX_BODY:
            raise RouterError('Body must be between 1 byte and 32 MiB.', 'body_size', 413)
        body = self.rfile.read(length)
        if len(body) != length:
            raise RouterError('Incomplete request body.', 'bad_request', 400)
        try:
            data = json.loads(body)
        except ValueError:
            raise RouterError('Invalid JSON.', 'bad_request', 400)
        if not isinstance(data, dict):
            raise RouterError('A JSON object is required.', 'bad_request', 400)
        return data

    def do_POST(self):
        if not self.auth():
            return
        path = urlsplit(self.path).path
        if path not in ('/v1/chat/completions', '/v1/completions', '/v1/responses', '/router/select', '/router/unload'):
            return self.error(404, 'Unknown endpoint.', 'not_found')
        try:
            data = self.read_body()
            if path == '/router/unload':
                w = self.server.workers
                w.unload()
                return self.reply(200, {'status': 'unloaded'})
            name = data.get('model')
            if not isinstance(name, str) or name not in profiles():
                raise RouterError('Choose an ID from GET /v1/models.', 'model_not_found', 404)
            profile = profiles()[name]
            if path == '/v1/chat/completions':
                data = apply_request_defaults(data, profile)
            if path == '/v1/completions' and profile['engine'] in ('Strata', 'Maya'):
                raise RouterError('This engine supports chat completions.', 'unsupported_endpoint', 400)
            if 'stream' in data and not isinstance(data['stream'], bool):
                raise RouterError('stream must be a boolean.', 'bad_request', 400)
            search_options = web_search.plan(data) if path == '/v1/responses' else None
            if search_options and search_options.get('disabled'):
                data = web_search.strip_tools(data)
                search_options = None
            if data.get('stream') and path != '/router/select':
                return self.stream(name, path, data, search_options)
            if path == '/router/select':
                self.server.workers.acquire(name, clear_guard=True)
            else:
                self.server.workers.acquire(name)
            try:
                if path == '/router/select':
                    return self.reply(200, {'status': 'ready', 'model': name,
                                            'context_window': profile['allocated_context']})
                self.forward(name, path, data, search_options)
            finally:
                self.server.workers.release()
        except RouterError as e:
            self.error(e.status, str(e), e.code)
        except (ValueError, TimeoutError):
            self.error(400, 'Invalid or incomplete request.', 'bad_request')
        except (BrokenPipeError, ConnectionResetError):
            pass
        except OSError:
            self.error(503, 'Worker connection failed; inspect the local service journal.', 'backend_unavailable')

    def proxy(self):
        return BackendProxy(self.server.key, self.server.workers.backend_models)

    def open_backend(self, path, data):
        return self.proxy().open(path, data)

    def forward(self, name, path, data, search_options=None):
        if search_options:
            return self.reply(200, web_search.execute(data, name, self.proxy(), search_options))
        conn = self.open_backend(path, data)
        try:
            response = conn.getresponse()
            payload, kind = self.proxy().response(response, name)
            self.send_response(response.status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)
        finally:
            conn.close()

    def stream(self, name, path, data, search_options=None):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        lock = threading.Lock()
        done = threading.Event()
        acquired = False
        conn = None
        sequence = 0

        def write(payload):
            with lock:
                self.wfile.write(payload)
                self.wfile.flush()

        def heartbeat():
            while not done.wait(10):
                try:
                    write(b': waiting for local inference\n\n')
                except OSError:
                    done.set()

        def progress():
            if done.is_set():
                raise BrokenPipeError('Client disconnected')

        def emit_event(value):
            nonlocal sequence
            value['sequence_number'] = sequence
            sequence += 1
            write(('event: ' + value['type'] + '\ndata: ' + json.dumps(value) + '\n\n').encode())

        threading.Thread(target=heartbeat, daemon=True).start()
        try:
            write(b': local inference router\n\n')
            self.server.workers.acquire(name, progress)
            acquired = True
            if search_options:
                web_search.execute(data, name, self.proxy(), search_options, emit_event, progress)
                return
            conn = self.open_backend(path, data)
            response = conn.getresponse()
            if response.status != 200:
                raise self.proxy().stream_error(response)
            while line := response.readline():
                if line.startswith(b'data:') and line[5:].strip() != b'[DONE]':
                    try:
                        value = json.loads(line[5:])
                        rewrite_model_alias(value, name)
                        line = b'data: ' + json.dumps(value).encode() + b'\n'
                    except ValueError:
                        pass
                write(line)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (RouterError, OSError) as e:
            try:
                message = str(e).replace(self.server.key, '[redacted]')
                code = getattr(e, 'code', 'backend_unavailable')
                if path == '/v1/responses':
                    emit_event({'type':'error','code':code,'message':message,'param':None})
                else:
                    write(b'data: ' + json.dumps({'error': {'message':message,'code':code,
                          'status':getattr(e,'status',503)}}).encode() + b'\n\ndata: [DONE]\n\n')
            except OSError:
                pass
        finally:
            done.set()
            if conn:
                conn.close()
            if acquired:
                self.server.workers.release()


def main():
    from visible_terminal import open_monitor
    open_monitor("NVIDIA model router", "nvidia-model-router.service")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'data/router/access.json')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    key_file = Path(cfg['key_file'])
    if key_file.stat().st_mode & 0o077:
        raise SystemExit('API key must be owner-only.')
    key = key_file.read_text().strip()
    if len(key) < 32:
        raise SystemExit('A strong API key is required.')
    allowed = [ipaddress.ip_network('127.0.0.0/8'), ipaddress.ip_network('100.64.0.0/10')]
    for value in cfg['listen']:
        ip = ipaddress.ip_address(value)
        if ip.version != 4 or not any(ip in n for n in allowed):
            raise SystemExit('Explicit loopback or Tailscale IPv4 listeners are required.')
    workers = Workers(key, idle_timeout=load_policy()['idle_timeout_s'])
    servers = {}
    stop = threading.Event()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(sig, lambda *_: stop.set())
    try:
        while not stop.is_set():
            for address in cfg['listen']:
                if address in servers:
                    continue
                try:
                    server = ThreadingHTTPServer((address, cfg.get('port', 10100)), Handler)
                except OSError:
                    continue  # Tailscale may acquire its address after the user service starts.
                server.daemon_threads = True
                server.workers, server.key, server.allowed = workers, key, allowed
                server.protocol_diagnostics = cfg.get('protocol_diagnostics') is True
                servers[address] = server
                threading.Thread(target=server.serve_forever, daemon=True).start()
            workers.idle_tick()
            stop.wait(5)
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
