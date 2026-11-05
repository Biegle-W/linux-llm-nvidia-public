"""Selected ComfyUI video entries and their bounded interactive workflows."""
import hashlib
import json
import os
import signal
import time
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
RESOLUTIONS={'512x288':(512,288),'720p':(1280,720),'1080p':(1920,1080)}

def dimensions(resolution):
    assert resolution in RESOLUTIONS,'Select512x288,720p or1080p'
    return RESOLUTIONS[resolution]

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

def graph(identifier,seed=27001,prompt=PROMPT,resolution="512x288"):
    entry(identifier);dimensions(resolution)
    return {'1':{'class_type':'NvidiaVideoEntry','inputs':dict(entry=identifier,prompt=prompt,seed=seed,resolution=resolution)},'9':{'class_type':'SaveVideo','inputs':dict(video=['1',0],filename_prefix=identifier+'-'+str(seed),format='mp4')}}

def output(root,work,identifier,seed,elapsed):
    files=list((work/'images').rglob('*'+str(seed)+'*.mp4'));assert len(files)==1
    video=files[0]
    code="import av,json,sys; c=av.open(sys.argv[1]); v=list(c.decode(video=0)); c=av.open(sys.argv[1]); a=list(c.decode(audio=0)) if c.streams.audio else []; print(json.dumps(dict(frames=len(v),width=v[0].width,height=v[0].height,audio_samples=sum(x.samples for x in a))))"
    dimensions=json.loads(subprocess.check_output([str(root/'runtimes/env-comfy-video/bin/python'),'-c',code,str(video)],text=True))
    settings=json.loads((work/'video-stage.json').read_text())
    assert (dimensions['width'],dimensions['height'],dimensions['frames'])==(settings.get('width',512),settings.get('height',288),33)
    assert bool(dimensions['audio_samples'])==(identifier=='ltx23-mesh')
    return dict(seed=seed,wall_s=elapsed,video=str(video),sha256=hashlib.sha256(video.read_bytes()).hexdigest(),**dimensions)

def workflow(identifier,resolution='512x288'):
    row=entry(identifier);width,height=dimensions(resolution)
    nodes=[dict(id=1,type='NvidiaVideoEntry',title=row['name']+f' —{width}x{height} /33frames',pos=[0,0],size=[490,340],flags={},order=0,mode=0,inputs=[],outputs=[dict(name='VIDEO',type='VIDEO',links=[1])],properties={'Node name for S&R':'NvidiaVideoEntry'},widgets_values=[identifier,PROMPT,27001,'fixed',resolution]),dict(id=9,type='SaveVideo',pos=[560,0],size=[530,400],flags={},order=1,mode=0,inputs=[dict(name='video',type='VIDEO',link=1)],outputs=[dict(name='video',type='VIDEO',links=None)],properties={'Node name for S&R':'SaveVideo'},widgets_values=[identifier+'-'+resolution,'mp4','auto','auto'],widgets_values_named={'filename_prefix':identifier+'-'+resolution,'format':'mp4','format.codec':'auto','codec':'auto'})]
    return dict(last_node_id=9,last_link_id=1,nodes=nodes,links=[[1,1,0,9,0,'VIDEO']],groups=[],config={},extra={'ds':{'scale':1,'offset':[0,0]}},version=0.4)

def install_workflows(identifier,folder):
    folder.mkdir(parents=True,exist_ok=True)
    for resolution in RESOLUTIONS:
        name=identifier+('' if resolution=='512x288' else '-'+resolution)+'.json'
        target=folder/name
        # Saved user edits are retained; new HD presets have their own names.
        if not target.exists():target.write_text((ROOT/'config/comfy-workflows'/name).read_text())

if __name__=='__main__':
    for row in json.loads((ROOT/'config/comfy-video-entries.json').read_text())['models']:
        identifier=row['id']
        for resolution in RESOLUTIONS:
            name=identifier+('' if resolution=='512x288' else '-'+resolution)
            folder=ROOT/'config/comfy-workflows'
            (folder/(name+'.api.json')).write_text(json.dumps(graph(identifier,resolution=resolution),indent=2)+'\n')
            (folder/(name+'.json')).write_text(json.dumps(workflow(identifier,resolution),indent=2)+'\n')
