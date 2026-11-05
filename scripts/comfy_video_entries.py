"""Selected ComfyUI video entries and their bounded interactive workflows."""
import hashlib
import json
import os
import signal
import time
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PROMPT='A red fox standing in snow slowly turns its head toward the camera and blinks. Gentle snowflakes drift through the air. Static camera, natural sunrise light, realistic smooth motion.'

def stop_job_group(process):
    # Descendants retain the owned job PGID even if its leader has crashed.
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait(timeout=5)
    deadline=time.monotonic()+5
    while True:
        try:os.killpg(process.pid,0)
        except ProcessLookupError:break
        if time.monotonic()>=deadline:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            break
        time.sleep(0.1)

def entry(identifier):
    return next(row for row in json.loads((ROOT/'config/comfy-video-entries.json').read_text())['models'] if row['id']==identifier)

def graph(identifier,seed=27001,prompt=PROMPT):
    entry(identifier)
    return {'1':{'class_type':'NvidiaVideoEntry','inputs':dict(entry=identifier,prompt=prompt,seed=seed)},'9':{'class_type':'SaveVideo','inputs':dict(video=['1',0],filename_prefix=identifier+'-'+str(seed),format='mp4')}}

def output(root,work,identifier,seed,elapsed):
    files=list((work/'images').rglob('*'+str(seed)+'*.mp4'));assert len(files)==1
    video=files[0]
    code="import av,json,sys; c=av.open(sys.argv[1]); v=list(c.decode(video=0)); c=av.open(sys.argv[1]); a=list(c.decode(audio=0)) if c.streams.audio else []; print(json.dumps(dict(frames=len(v),width=v[0].width,height=v[0].height,audio_samples=sum(x.samples for x in a))))"
    dimensions=json.loads(subprocess.check_output([str(root/'runtimes/env-comfy-video/bin/python'),'-c',code,str(video)],text=True))
    assert (dimensions['width'],dimensions['height'],dimensions['frames'])==(512,288,33)
    assert bool(dimensions['audio_samples'])==(identifier=='ltx23-mesh')
    return dict(seed=seed,wall_s=elapsed,video=str(video),sha256=hashlib.sha256(video.read_bytes()).hexdigest(),**dimensions)

if __name__=='__main__':
    for row in json.loads((ROOT/'config/comfy-video-entries.json').read_text())['models']:
        identifier=row['id'];api=graph(identifier)
        nodes=[dict(id=1,type='NvidiaVideoEntry',title=row['name']+' —512x288 /33frames',pos=[0,0],size=[490,300],flags={},order=0,mode=0,inputs=[],outputs=[dict(name='VIDEO',type='VIDEO',links=[1])],properties={'Node name for S&R':'NvidiaVideoEntry'},widgets_values=[identifier,PROMPT,27001,'fixed']),dict(id=9,type='SaveVideo',pos=[560,0],size=[530,400],flags={},order=1,mode=0,inputs=[dict(name='video',type='VIDEO',link=1)],outputs=[dict(name='video',type='VIDEO',links=None)],properties={'Node name for S&R':'SaveVideo'},widgets_values=[identifier,'mp4','auto','auto'],widgets_values_named={'filename_prefix':identifier,'format':'mp4','format.codec':'auto','codec':'auto'})]
        folder=ROOT/'config/comfy-workflows'
        (folder/(identifier+'.api.json')).write_text(json.dumps(api,indent=2)+'\n')
        (folder/(identifier+'.json')).write_text(json.dumps(dict(last_node_id=9,last_link_id=1,nodes=nodes,links=[[1,1,0,9,0,'VIDEO']],groups=[],config={},extra={'ds':{'scale':1,'offset':[0,0]}},version=0.4),indent=2)+'\n')
