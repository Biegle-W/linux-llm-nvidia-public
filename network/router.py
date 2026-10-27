#!/usr/bin/env python3
"""Authenticated OpenAI model/engine router for the qualified NVIDIA catalog."""
import argparse
import hmac
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import signal
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit
from worker_manager import Workers, RouterError, profiles, ROOT

MAX_BODY = 32 * 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        # Bodies, credentials, query strings, and client identities are never logged.
        pass

    def reply(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
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
        ready = bool(w.backend_models()) if w.active and w.loading is None else False
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
                                    'busy': w.busy, 'models': len(profiles())})
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
        if path not in ('/v1/chat/completions', '/v1/completions', '/router/select', '/router/unload'):
            return self.error(404, 'Unknown endpoint.', 'not_found')
        try:
            data = self.read_body()
            if path == '/router/unload':
                w = self.server.workers
                if not w.lock.acquire(timeout=1):
                    raise RouterError('A reply or switch is active; retry later.', 'backend_busy', 409)
                try:
                    w.stop_owned()
                finally:
                    w.lock.release()
                return self.reply(200, {'status': 'unloaded'})
            name = data.get('model')
            if not isinstance(name, str) or name not in profiles():
                raise RouterError('Choose an ID from GET /v1/models.', 'model_not_found', 404)
            profile = profiles()[name]
            if path == '/v1/completions' and profile['engine'] in ('Strata', 'Maya'):
                raise RouterError('This engine supports chat completions.', 'unsupported_endpoint', 400)
            if 'stream' in data and not isinstance(data['stream'], bool):
                raise RouterError('stream must be a boolean.', 'bad_request', 400)
            if data.get('stream') and path != '/router/select':
                return self.stream(name, path, data)
            if path == '/router/select':
                self.server.workers.acquire(name, clear_guard=True)
            else:
                self.server.workers.acquire(name)
            try:
                if path == '/router/select':
                    return self.reply(200, {'status': 'ready', 'model': name,
                                            'context_window': profile['allocated_context']})
                self.forward(name, path, data)
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

    def backend_body(self, data):
        models = self.server.workers.backend_models()
        if not models:
            raise RouterError('Worker is not ready.', 'backend_unavailable')
        body = dict(data)
        body['model'] = models[0]['id']
        return json.dumps(body).encode()

    def open_backend(self, path, data):
        connection = http.client.HTTPConnection('127.0.0.1', 10000, timeout=7200)
        connection.request('POST', path, self.backend_body(data),
                           {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.server.key})
        return connection

    def forward(self, name, path, data):
        conn = self.open_backend(path, data)
        try:
            response = conn.getresponse()
            value = json.loads(response.read())
            if isinstance(value, dict) and 'model' in value:
                value['model'] = name
            self.reply(response.status, value)
        finally:
            conn.close()

    def stream(self, name, path, data):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        lock = threading.Lock()
        done = threading.Event()
        acquired = False
        conn = None

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

        threading.Thread(target=heartbeat, daemon=True).start()
        try:
            write(b': local inference router\n\n')
            self.server.workers.acquire(name, progress)
            acquired = True
            conn = self.open_backend(path, data)
            response = conn.getresponse()
            if response.status != 200:
                raise RouterError('Worker rejected the request; check its endpoint parameters.', 'backend_error', response.status)
            while line := response.readline():
                if line.startswith(b'data:') and line[5:].strip() != b'[DONE]':
                    try:
                        value = json.loads(line[5:])
                        if 'model' in value:
                            value['model'] = name
                        line = b'data: ' + json.dumps(value).encode() + b'\n'
                    except ValueError:
                        pass
                write(line)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (RouterError, OSError) as e:
            try:
                write(b'data: ' + json.dumps({'error': {'message': str(e).replace(self.server.key, '[redacted]'),
                      'code': getattr(e, 'code', 'backend_unavailable')}}).encode() + b'\n\ndata: [DONE]\n\n')
            except OSError:
                pass
        finally:
            done.set()
            if conn:
                conn.close()
            if acquired:
                self.server.workers.release()


def main():
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
    workers = Workers(key)
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
                servers[address] = server
                threading.Thread(target=server.serve_forever, daemon=True).start()
            stop.wait(5)
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
