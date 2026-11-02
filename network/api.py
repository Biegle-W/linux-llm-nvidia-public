#!/usr/bin/env python3
"""Thin authenticated NVIDIA API gateway; only the private hub owns model state."""
import argparse,hmac,http.client,ipaddress,json,select,signal,socket,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from hub_transport import clean_error_body,relay_sse,sse_error
ROOT=Path(__file__).resolve().parents[1]
MAX_BODY=32*1024*1024
API_PATHS={'/v1/chat/completions','/v1/completions','/v1/responses','/router/select','/router/unload'}

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args):pass
    def error(self,status,message,code):
        payload=json.dumps({'error':{'message':message,'type':'server_error' if status>=500 else 'invalid_request_error','code':code}}).encode()
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.send_header('Connection','close');self.end_headers();self.wfile.write(payload);self.close_connection=True
    def authorized(self):
        try:address=ipaddress.ip_address(self.client_address[0])
        except ValueError:return False
        if not any(address in subnet for subnet in self.server.allowed):self.error(403,'Client network is not allowed.','network_denied');return False
        values=self.headers.get_all('Authorization') or []
        if len(values)!=1 or not hmac.compare_digest(values[0].encode(),('Bearer '+self.server.key).encode()):self.error(401,'A valid local API key is required.','invalid_api_key');return False
        return True
    def do_GET(self):self.forward(False)
    def do_POST(self):self.forward(True)
    def forward(self,post):
        if not self.authorized():return
        path=urlsplit(self.path).path
        if post:
            if path not in API_PATHS:self.error(404,'Unknown endpoint.','not_found');return
            values=self.headers.get_all('Content-Length') or []
            if self.headers.get_all('Transfer-Encoding') or len(values)!=1:self.error(400,'Use one Content-Length header.','bad_request');return
            try:length=int(values[0])
            except ValueError:self.error(400,'Invalid Content-Length.','bad_request');return
            if length<0 or length>MAX_BODY:self.error(413,'Request body exceeds the API limit.','request_too_large');return
            self.connection.settimeout(30)
            try:body=self.rfile.read(length)
            except (OSError,TimeoutError):self.error(400,'Incomplete request body.','bad_request');return
            if len(body)!=length:self.error(400,'Incomplete request body.','bad_request');return
        else:
            if path not in ('/health','/v1/models') and not path.startswith('/v1/models/'):self.error(404,'Unknown endpoint.','not_found');return
            body=None
        conn=http.client.HTTPConnection('127.0.0.1',self.server.hub_port,timeout=86400)
        finished=threading.Event();disconnected=threading.Event();started=False;stream=False
        try:
            conn.connect();upstream=conn.sock
            def watch_client():
                while not finished.wait(.25):
                    try:
                        readable,_,_=select.select([self.connection],[],[],0)
                        if not readable or self.connection.recv(1,socket.MSG_PEEK):continue
                    except OSError:pass
                    disconnected.set()
                    try:upstream.shutdown(socket.SHUT_RDWR)
                    except OSError:pass
                    return
            threading.Thread(target=watch_client,daemon=True).start()
            headers={'Authorization':'Bearer '+self.server.key}
            if post:headers['Content-Type']='application/json'
            conn.request('POST' if post else 'GET',path,body,headers);response=conn.getresponse()
            content_type=response.getheader('Content-Type','application/json');stream='text/event-stream' in content_type.lower()
            self.send_response(response.status);self.send_header('Content-Type',content_type);self.send_header('Cache-Control','no-store');self.send_header('Connection','close')
            retry=response.getheader('Retry-After')
            if retry and '\r' not in retry and '\n' not in retry:self.send_header('Retry-After',retry)
            self.end_headers();started=True;self.close_connection=True
            def output(chunk):self.wfile.write(chunk);self.wfile.flush()
            if response.status>=400:output(clean_error_body(response.read(MAX_BODY+1),(self.server.key,)))
            elif stream:relay_sse(response,output,(self.server.key,),responses=path=='/v1/responses')
            else:
                while chunk:=response.read1(65536):output(chunk)
        except (BrokenPipeError,ConnectionResetError):self.close_connection=True
        except (OSError,http.client.HTTPException):
            if disconnected.is_set():return
            if not started:self.error(503,'The private model hub is unavailable.','hub_unavailable')
            elif stream:
                try:self.wfile.write(sse_error({'message':'Model hub stream interrupted.','code':'hub_unavailable','status':503},(self.server.key,),responses=path=='/v1/responses'));self.wfile.flush()
                except OSError:pass
            self.close_connection=True
        finally:finished.set();conn.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,default=ROOT/'data/router/access.json');args=parser.parse_args()
    cfg=json.loads(args.config.read_text());p=Path(cfg['key_file'])
    if p.stat().st_mode&0o077:raise SystemExit('API key must be owner-only.')
    key=p.read_text().strip()
    if len(key)<32:raise SystemExit('A strong local API key is required.')
    allowed=[ipaddress.ip_network('127.0.0.0/8'),ipaddress.ip_network('100.64.0.0/10')]
    for value in cfg['listen']:
        ip=ipaddress.ip_address(value)
        if ip.version!=4 or not any(ip in n for n in allowed):raise SystemExit('Explicit loopback or Tailscale IPv4 listeners are required.')
    servers={};stop=threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
    try:
        while not stop.is_set():
            for address in cfg['listen']:
                if address in servers:continue
                try:server=ThreadingHTTPServer((address,cfg.get('port',10100)),Handler)
                except OSError:continue
                server.daemon_threads=True;server.key=key;server.allowed=allowed;server.hub_port=cfg.get('hub_port',10101);servers[address]=server;threading.Thread(target=server.serve_forever,daemon=True).start()
            stop.wait(2)
    finally:
        for server in servers.values():server.shutdown();server.server_close()

if __name__=='__main__':main()
