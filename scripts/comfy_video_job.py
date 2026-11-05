"""Run one prompt through isolated GPU-only encoding/render phases in the UI cgroup."""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from comfy_video_trial import graph,output,audit
from comfy_video_entries import dimensions

ROOT=Path(__file__).resolve().parents[1]

def stop(child):
    if child is None:return
    if child.poll() is None:child.terminate()
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)

def run(work):
    request=json.loads((work/'request.json').read_text())
    entries=json.loads((ROOT/'config/comfy-video-entries.json').read_text())['models']
    entry=next(x for x in entries if x['id']==request['entry'])
    width,height=dimensions(request.get('resolution','512x288'))
    pins=json.loads((ROOT/'config/comfy-video-trial.json').read_text())
    assert os.environ.get('COMFY_VIDEO_ENTRY')==entry['id'],'Cross-entry generation forbidden'
    assert len(request['prompt'])<=4000 and request['prompt'].strip()
    assert type(request['seed']) is int and 0<=request['seed']<2**64
    for port in ([8189,7777] if entry['render_stage']=='mesh' else [8189]):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            probe.bind(('127.0.0.1',port))
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def http(path,body=None):
        req=urllib.request.Request('http://127.0.0.1:8189'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
        with opener.open(req,timeout=10) as response:return json.load(response)
    stages=[];child=mesh=None
    try:
        for stage in (entry['prepare_stage'],entry['render_stage']):
            stage_work=work/('prepare' if stage in ('prepare','mesh-prepare') else 'render');stage_work.mkdir()
            (stage_work/'images').mkdir();(stage_work/'user').mkdir()
            (stage_work/'video-stage.json').write_text(json.dumps({'stage':stage,'width':width,'height':height}))
            env=dict(os.environ,COMFY_VIDEO_WORK=str(stage_work),COMFY_VIDEO_AUDIT_DIR=str(stage_work/'forward-audits'),COMFY_VIDEO_ENTRY_CHILD='1')
            if stage=='mesh':
                weights=next(x['file'] for x in pins['models'][1]['files'] if x['file'].endswith('Q4_0.gguf'))
                mesh=subprocess.Popen([str(ROOT/pins['python']),str(ROOT/'scripts/comfy_mesh_gguf.py'),'--weights',str(ROOT/pins['checkpoint_directory']/weights),'--bind','127.0.0.1','--port','7777','--device','cuda:0','--dtype','bfloat16','--n-blocks','20'],env=dict(env,CUDA_VISIBLE_DEVICES='1',COMFYUI_PATH=str(ROOT/pins['ComfyUI']['path'])),cwd=ROOT/pins['ComfyUI']['path'])
            command=[str(ROOT/pins['python']),str(ROOT/pins['ComfyUI']['path']/'main.py'),'--listen','127.0.0.1','--port','8189','--disable-auto-launch','--gpu-only','--disable-dynamic-vram','--disable-async-offload','--disable-cuda-malloc','--use-pytorch-cross-attention','--reserve-vram','0.5','--offline','--disable-all-custom-nodes','--whitelist-custom-nodes','nvidia_video',*(['comfyui_mesh'] if stage=='mesh' else []),'--extra-model-paths-config',str(Path(os.environ['COMFY_VIDEO_WORK'])/'extra-model-paths.yaml'),'--output-directory',str(stage_work/'images'),'--user-directory',str(stage_work/'user')]
            child=subprocess.Popen(command,env=env,cwd=ROOT/pins['ComfyUI']['path'])
            deadline=time.monotonic()+180
            while True:
                assert child.poll() is None,'Owned phase backend exited'
                if mesh is not None:assert mesh.poll() is None,'Owned Mesh backend exited'
                try:
                    http('/system_stats')
                    if mesh is not None:
                        with socket.create_connection(('127.0.0.1',7777),timeout=1):pass
                    break
                except OSError:
                    if time.monotonic()>deadline:raise TimeoutError('Video phase startup timed out')
                    time.sleep(0.5)
            prompt=graph(stage,request['seed'],width,height)
            if stage in ('prepare','mesh-prepare'):prompt['9']['inputs']['prompt']=request['prompt']
            started=time.monotonic();answer=http('/prompt',{'prompt':prompt});ident=answer['prompt_id'];deadline=started+1200
            while True:
                assert child.poll() is None,'Owned phase backend exited'
                if mesh is not None:
                    if (stage_work/'mesh-stop-request').exists():
                        stop(mesh);mesh=None;(stage_work/'mesh-server-stopped').touch()
                    else:assert mesh.poll() is None,'Owned Mesh backend exited'
                history=http('/history/'+ident)
                if ident in history:break
                if time.monotonic()>deadline:raise TimeoutError('Video generation timed out')
                time.sleep(0.25)
            result=history[ident];(stage_work/'history.json').write_text(json.dumps(result)+'\n')
            assert result['status']['status_str']=='success','Video phase failed; inspect owned backend log'
            stages.append(output(ROOT,stage_work,stage,request['seed'],time.monotonic()-started))
            stop(child);child=None;stop(mesh);mesh=None
        result=dict(video=stages[-1]['video'],stages=stages,forward_audit=audit(work))
        (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    finally:stop(child);stop(mesh)

def main():
    def interrupted(*_):raise KeyboardInterrupt('Owned video job interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    work=Path(sys.argv[1]).resolve()
    try:run(work)
    except BaseException as error:
        (work/'error.json').write_text(json.dumps({'error':type(error).__name__+': '+str(error)})+'\n');raise

if __name__=='__main__':main()
