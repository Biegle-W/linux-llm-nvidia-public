"""Loopback backend transport, separate from HTTP access and worker lifecycle.

Only the configured local backend credential is sent upstream. External client
headers, cookies and query strings never enter this transport.
"""
import http.client
import json
from worker_manager import RouterError


class BackendProxy:
    def __init__(self, key, models):
        self.key, self.models = key, models

    def open(self, path, data):
        models = self.models()
        if not models:
            raise RouterError('Worker is not ready.', 'backend_unavailable')
        body = dict(data)
        body['model'] = models[0]['id']
        connection = http.client.HTTPConnection('127.0.0.1', 10000, timeout=7200)
        try:
            connection.request('POST', path, json.dumps(body).encode(),
                               {'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + self.key})
        except BaseException:
            connection.close()
            raise
        return connection

    def response(self, response, alias):
        payload = response.read()
        kind = response.getheader('Content-Type', 'application/json')
        try:
            value = json.loads(payload)
        except (ValueError, UnicodeDecodeError):
            pass  # Keep plain-text backend errors and their original HTTP status.
        else:
            if isinstance(value, dict) and 'model' in value:
                value['model'] = alias
                payload = json.dumps(value).encode()
        if response.status >= 400:
            payload = payload.replace(self.key.encode(), b'[redacted]')
        return payload, kind

    def stream_error(self, response):
        payload = response.read(65536)
        try:
            message = json.loads(payload)['error']['message']
        except (ValueError, UnicodeDecodeError, KeyError, TypeError):
            message = payload.decode(errors='replace')
        message = str(message).replace(self.key, '[redacted]')[:500]
        return RouterError(message or 'Worker rejected the request.',
                           'backend_error', response.status)
