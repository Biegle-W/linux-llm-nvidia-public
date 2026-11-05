"""Run the isolated dual-GPU ComfyUI under an exclusive project reservation."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import socket
import shutil
import subprocess
import struct
import sys
import time
import threading
import urllib.request
import uuid
from cli_short_models import inactive, property_of
from gpu_transport_health import require_host_staged
from pair_p2p_health import require_verified_pair

ROOT = Path(__file__).resolve().parents[1]
UNIT = 'llm-comfy-images.service'
CAPTION = ('A detailed editorial photograph of a small red fox standing in fresh white snow beside a dark green pine tree. '
           'The fox faces the camera, with two alert triangular ears, amber eyes, a black nose and a fluffy orange tail curled to its right. '
           'Warm sunrise light enters from the left, illuminating individual hairs and tiny snow crystals. '
           'A softly blurred forest fills the background. Natural colors, realistic anatomy, no text, square composition.')


def ended_unit(query=property_of):
    return (not query(UNIT,'InvocationID') and query(UNIT,'ActiveState')=='inactive'
            and query(UNIT,'MainPID')=='0' and not query(UNIT,'ControlGroup'))


def graph(model, seed, size=1024):
    qwen = model['id'].startswith('qwen')
    files = {x['file'].split('/')[0]:Path(x['file']).name for x in model['files']}
    def node(kind, **inputs):return dict(class_type=kind,inputs=inputs)
    g = {'1':node('NvidiaResidentDenoiser',name=files['diffusion_models']),
         '2':node('NvidiaResidentEncoder',name=files['text_encoders'],type='qwen_image' if qwen else 'flux3'),
         '3':node('NvidiaResidentVAE',name=files['vae']),
         '8':node('VAEDecode',samples=['7',0],vae=['3',0]),
         '9':node('SaveImage',images=['8',0],filename_prefix=model['id']+'-'+str(seed))}
    if qwen:
        g.update({'4':node('TextEncodeQwenImage21',clip=['2',0],prompt=CAPTION,negative_prompt='',resolution=size),
                  '10':node('RandomNoise',noise_seed=seed),'11':node('KSamplerSelect',sampler_name='euler'),
                  '12':node('ManualSigmas',sigmas='1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0'),
                  '13':node('CFGGuider',model=['1',0],positive=['4',0],negative=['4',1],cfg=1.0),
                  '7':node('SamplerCustomAdvanced',noise=['10',0],guider=['13',0],sampler=['11',0],sigmas=['12',0],latent_image=['4',2])})
    else:
        g.update({'4':node('CLIPTextEncode',clip=['2',0],text=CAPTION),
                  '5':node('CLIPTextEncode',clip=['2',0],text=''),
                  '6':node('EmptyFlux2LatentImage',width=size,height=size,batch_size=1),
                  '7':node('KSampler',model=['1',0],positive=['4',0],negative=['5',0],latent_image=['6',0],
                           seed=seed,steps=16,cfg=1.0,sampler_name='er_sde',scheduler='simple',denoise=1.0)})
    return g


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',choices=['qwen-image-2.1-turbo','flux3-klein','wan22-5b','wan22-5b-raylight','ltx23-mesh'],required=True)
    parser.add_argument('--video-entry',action='store_true',help='Use the selected interactive video workflow')
    parser.add_argument('--video-resolution',choices=['720p','1080p'],help='Video entry preset or isolated render size; retains33frames and all guards')
    parser.add_argument('--video-sync-ulysses',action='store_true',help='Explicit synchronized Raylight benchmark retry')
    parser.add_argument('--video-seed',type=int,help='Single-request guarded video verification seed')
    parser.add_argument('--video-stage',choices=['prepare','baseline','raylight','mesh-prepare','mesh'])
    parser.add_argument('--size',type=int,choices=[1024,2048,4096],default=1024,help='Square image width/height in pixels')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--serve',action='store_true')
    mode.add_argument('--check-ui',action='store_true')
    parser.add_argument('--foreground-backend',action='store_true',help='Show backend logs in this same visible foreground terminal')
    args=parser.parse_args()
    video_dimensions={'720p':(1280,720),'1080p':(1920,1080)}.get(args.video_resolution,(512,288))
    if args.video_resolution or args.video_seed is not None:
        assert args.video_entry or (args.video_stage in ('baseline','raylight','mesh') and not (args.serve or args.check_ui)),'Select video entry mode or an isolated video render stage'
        assert args.video_seed is None or (not (args.serve or args.check_ui) and 0<=args.video_seed<2**64),'Seed override requires a bounded generation test'
    if args.video_sync_ulysses:assert not args.video_entry and args.video_stage=='raylight' and args.video_resolution,'Synchronized retry requires an isolated Raylight resolution benchmark'
    entry=None
    if args.video_entry:
        from comfy_video_entries import entry as get_entry
        entry=get_entry(args.model)
        assert args.video_stage is None,'Entry mode owns encoding and rendering stages'
        args.video_stage='entry'
    elif args.model in ('wan22-5b-raylight','ltx23-mesh'):
        expected=('mesh-prepare','mesh') if args.model=='ltx23-mesh' else ('prepare','baseline','raylight')
        assert args.video_stage in expected,'Select a matching experimental video stage'
        assert not args.serve,'Video candidates have no production serving qualification'
        from comfy_video_trial import graph as validate_video_graph
        validate_video_graph(args.video_stage,27001,*video_dimensions,sync_ulysses=args.video_sync_ulysses)
    else:assert args.video_stage is None and args.model!='wan22-5b','Select video entry mode for this model'
    def interrupted(*_):raise KeyboardInterrupt('Owned ComfyUI coordinator interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGINT,interrupted)
    signal.signal(signal.SIGHUP,interrupted)
    assert sys.stdin.isatty() and sys.stdout.isatty(),'Use visible_terminal.py foreground'
    os.umask(0o077)
    config=json.loads((ROOT/'config/comfy-runtime.json').read_text())
    if args.video_stage:
        trial=json.loads((ROOT/'config/comfy-video-trial.json').read_text())
        models=trial['models'] if entry is None else [dict(next(row for row in trial['models'] if row['id']==entry['trial_id']),id=args.model)]
        config=dict(config,models=models,checkpoint_directory=trial['checkpoint_directory'])
    model=next(x for x in config['models'] if x['id']==args.model)
    base=ROOT/'data/comfy-video-dual-20261104/stages' if args.video_stage else ROOT/'data/comfy-qualification-20261105'
    if args.video_resolution:base=ROOT/'data/comfy-video-resolutions-20261105/stages'
    work=base/time.strftime('%H%M%S-'+args.model+'-'+(args.video_stage or str(args.size))+('-'+args.video_resolution if args.video_resolution else '')+('-seed'+str(args.video_seed) if args.video_seed is not None else '')+('-sync' if args.video_sync_ulysses else ''))
    work.mkdir(parents=True,exist_ok=False)
    (work/'user').mkdir()
    (work/'images').mkdir()
    if args.video_stage:
        (work/'video-stage.json').write_text(json.dumps(dict(stage=args.video_stage,width=video_dimensions[0],height=video_dimensions[1],sync_ulysses=args.video_sync_ulysses)))
    if args.serve or (args.check_ui and args.video_entry):(work/'serve').touch()
    if args.serve or args.video_entry:
        folder=ROOT/'data/comfy-user'/args.model/'default/workflows'
        folder.mkdir(parents=True,exist_ok=True)
        if entry:
            from comfy_video_entries import install_workflows
            install_workflows(args.model,folder)
        else:
            source=ROOT/'config/comfy-workflows'/(args.model+'.json')
            if source.exists() and not (folder/source.name).exists():shutil.copy2(source,folder/source.name)
    (work/'extra-model-paths.yaml').write_text('nvidia_images:\n  base_path: '+str(ROOT/config['checkpoint_directory'])+'\n  diffusion_models: diffusion_models\n  text_encoders: text_encoders\n  vae: vae\n')
    if args.video_stage:
        (work/'extra-model-paths.yaml').write_text('nvidia_video:\n  base_path: '+str(ROOT/config['checkpoint_directory'])+'\n  diffusion_models: split_files/diffusion_models\n  text_encoders: .\n  vae: split_files/vae\n')
    state=dict(phase='preflight',model=args.model,width=args.size,height=args.size,started=time.time(),pid=os.getpid(),work=str(work))
    if args.video_stage:state.update(width=video_dimensions[0],height=video_dimensions[1],frames=33,fps=24 if args.model=='ltx23-mesh' else 16,stage=args.video_stage)
    def save():
        temp=work/'state.tmp';temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(work/'state.json')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path,body=None,port=8188,key=None):
        headers={'Content-Type':'application/json'}
        if key:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        with opener.open(req,timeout=10) as response:return json.load(response)
    owned=lock=None
    tail_stop=threading.Event()
    tail_thread=None
    save()
    try:
        require_verified_pair();require_host_staged()
        assert 'VERIFIED' in subprocess.check_output(['gpu-unlock-health','status','--brief'],text=True)
        assert inactive() and not (ROOT/'data/GPU-LOCK').exists(),'Independent GPU owner preserved'
        assert property_of(UNIT,'ActiveState') not in ('active','activating')
        key=(ROOT/'data/local-api-key').read_text().strip()
        health=request('/health',port=10100,key=key)
        assert not any(health.get(k) for k in ('busy','inflight','queued','loading_model','idle_unloading_model'))
        from storage_policy import verify_storage
        for folder in (tuple({str(Path(row['file']).parent) for row in model['files']}) if args.video_stage else ('diffusion_models','text_encoders','vae')):
            verify_storage(dict(id=args.model,storage=dict(checkpoint_directory=config['checkpoint_directory']+'/'+folder,required_transport='sata')))
        print('Verifying publisher hashes and SATA placement; guards='+json.dumps(config['guard_policy']),flush=True)
        for row in model['files']:
            path=ROOT/config['checkpoint_directory']/row['file']
            assert path.stat().st_size==row['bytes']
            with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            probe.bind(('127.0.0.1',8188))
        if args.video_stage=='mesh':
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                probe.bind(('127.0.0.1',7777))
        lock=dict(owner='comfy-images',pid=os.getpid(),unit=UNIT,nonce=uuid.uuid4().hex,started=time.time())
        fd=os.open(ROOT/'data/GPU-LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as stream:stream.write(json.dumps(lock)+'\n')
        assert inactive(),'New independent GPU owner preserved'
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip()
        assert not apps,'Independent CUDA process preserved'
        free=[int(x) for x in subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()]
        assert len(free)==2 and free[0]>=11520 and free[1]>=9472,'Both main GPUs must be idle before ComfyUI admission'
        if args.foreground_backend:
            print('Backend logs share this visible foreground terminal.',flush=True)
            def tail():
                position=0
                while not tail_stop.wait(0.5):
                    path=work/'engine.log'
                    if path.exists():
                        with path.open(errors='replace') as stream:
                            stream.seek(position);text=stream.read();position=stream.tell()
                        if text:print(text,end='',flush=True)
            tail_thread=threading.Thread(target=tail,daemon=True);tail_thread.start()
        else:
            from visible_terminal import open_monitor
            open_monitor('ComfyUI dual-GPU backend',UNIT,[work/'engine.log'])
        subprocess.run(['systemd-run','--user','--collect','--unit='+UNIT,'--property=MemoryHigh=32G',
                        '--property=MemoryMax=36G','--property=MemorySwapMax=infinity','--property=OOMPolicy=kill',
                        '--property=KillMode=control-group','--property=TimeoutStopSec=45','--property=NoNewPrivileges=yes',
                        '--property=UMask=0077','--property=StandardOutput=append:'+str(work/'engine.log'),
                        '--property=StandardError=append:'+str(work/'engine.log'),'/usr/bin/python3',
                        str(ROOT/'scripts/comfy_worker.py'),str(work)],check=True)
        owned=property_of(UNIT,'InvocationID');assert owned
        state.update(phase='starting',invocation=owned);save()
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            assert property_of(UNIT,'InvocationID')==owned and property_of(UNIT,'ActiveState')=='active','Owned backend stopped'
            try:request('/system_stats');break
            except OSError:time.sleep(1)
        else:raise TimeoutError('ComfyUI did not become ready')
        if args.video_stage=='mesh':
            while time.monotonic()<deadline:
                assert property_of(UNIT,'InvocationID')==owned and property_of(UNIT,'ActiveState')=='active','Owned Mesh backend stopped'
                try:
                    with socket.create_connection(('127.0.0.1',7777),timeout=1):break
                except OSError:time.sleep(1)
            else:raise TimeoutError('Mesh back-half server did not become ready')
        state.update(phase='ready');save()
        print('ComfyUI ready at http://127.0.0.1:8188; exclusive GPUs reserved.',flush=True)
        if entry:
            info=request('/object_info/NvidiaVideoEntry')['NvidiaVideoEntry']['input']['required']
            assert info['entry'][0]==[args.model]
            assert info['resolution'][0]==['512x288','720p','1080p']
            assert info['resolution'][1]['default']==(args.video_resolution or '512x288')
            state['frontend_resolution_choices']=info['resolution'][0];save()
            print('Open Workflows preset: '+args.model+('-'+args.video_resolution if args.video_resolution else '')+'; resolution can also be changed in the video node.',flush=True)
        if args.check_ui:
            with opener.open('http://127.0.0.1:8188/',timeout=10) as response:
                html=response.read().decode()
                assert response.status==200 and 'ComfyUI' in html
            info=request('/object_info')
            if args.video_stage:
                from comfy_video_entries import graph as entry_graph
                from comfy_video_trial import graph as video_graph
                candidate=entry_graph(args.model,resolution=args.video_resolution or '512x288') if entry else video_graph(args.video_stage,27001)
                assert all(node['class_type'] in info for node in candidate.values())
                if entry:
                    assert info['NvidiaVideoEntry']['input']['required']['entry'][0]==[args.model]
                    installed=ROOT/'data/comfy-user'/args.model/'default/workflows'/(args.model+'.json')
                    assert installed.is_file(),'Selected workflow missing from persistent ComfyUI library'
            else:
                for candidate in config['models']:
                    assert all(node['class_type'] in info for node in graph(candidate,27001).values())
            state['frontend_http_and_workflow_nodes_passed']=True
        elif args.serve:
            while property_of(UNIT,'InvocationID')==owned and property_of(UNIT,'ActiveState')=='active':time.sleep(2)
        else:
            state['runs']=[]
            for seed in ((args.video_seed,) if args.video_seed is not None else (27001,) if args.video_stage in ('prepare','mesh-prepare','mesh') else (27001,27002)):
                if args.video_entry:
                    from comfy_video_entries import graph as entry_graph
                    prompt=entry_graph(args.model,seed,resolution=args.video_resolution or '512x288')
                elif args.video_stage:
                    from comfy_video_trial import graph as video_graph
                    prompt=video_graph(args.video_stage,seed,*video_dimensions,sync_ulysses=args.video_sync_ulysses)
                else:prompt=graph(model,seed,args.size)
                (work/f'workflow-{seed}.json').write_text(json.dumps(prompt,indent=2)+'\n')
                state.update(phase='generating',seed=seed);save()
                started=time.monotonic();answer=request('/prompt',dict(prompt=prompt,client_id='nvidia-local-qualified'))
                ident=answer['prompt_id'];deadline=time.monotonic()+1200
                while time.monotonic()<deadline:
                    assert property_of(UNIT,'InvocationID')==owned and property_of(UNIT,'ActiveState')=='active','Owned backend stopped; inspect guard/engine logs'
                    history=request('/history/'+ident)
                    if ident in history:break
                    time.sleep(1)
                else:raise TimeoutError('Image generation exceeded1200seconds')
                result=history[ident];(work/f'history-{seed}.json').write_text(json.dumps(result,indent=2)+'\n')
                assert result['status']['status_str']=='success',str(result['status'])[:1000]
                if args.video_stage:
                    if args.video_entry:
                        from comfy_video_entries import output
                        stage_or_id=args.model
                    else:
                        from comfy_video_trial import output
                        stage_or_id=args.video_stage
                    state['runs'].append(output(ROOT,work,stage_or_id,seed,time.monotonic()-started))
                    save();print('Video stage PASS: '+json.dumps(state['runs'][-1]),flush=True)
                    continue
                images=result['outputs']['9']['images'];assert len(images)==1
                image=work/'images'/images[0]['subfolder']/images[0]['filename']
                image_data=image.read_bytes()
                assert image_data[:8]==b'\x89PNG\r\n\x1a\n'
                assert struct.unpack('>II',image_data[16:24])==(args.size,args.size),'Output dimensions differ from requested benchmark size'
                state['runs'].append(dict(seed=seed,wall_s=time.monotonic()-started,image=str(image),image_sha256=hashlib.sha256(image_data).hexdigest(),width=args.size,height=args.size))
                save();print('Image PASS: '+json.dumps(state['runs'][-1]),flush=True)
            if args.video_stage:
                from comfy_video_trial import audit
                state['forward_audit']=audit(work)
            else:
                placement=[json.loads(x) for x in (work/'placement.jsonl').read_text().splitlines()]
                assert {'cuda:0','cuda:1'}<={x['expected'] for x in placement}
            assert not (work/'guard-stop.json').exists()
        state['phase']='pass';save()
    except BaseException as error:
        state.update(phase='failed',error=type(error).__name__+': '+str(error));save();raise
    finally:
        released=False
        if owned and property_of(UNIT,'InvocationID')==owned and str(ROOT/'scripts/comfy_worker.py') in property_of(UNIT,'ExecStart'):
            subprocess.run(['systemctl','--user','stop',UNIT],check=True)
            released=property_of(UNIT,'ActiveState') in ('inactive','failed')
        elif owned and ended_unit():
            released=True
        elif not owned:released=True
        if lock and released and json.loads((ROOT/'data/GPU-LOCK').read_text())==lock:
            (ROOT/'data/GPU-LOCK').unlink();state['reservation_released']=True
        state.update(worker_inactive=released,finished=time.time());save()
        tail_stop.set()
        if tail_thread:tail_thread.join(timeout=2)
        print('Final state: '+str(work/'state.json'),flush=True)

if __name__=='__main__':main()
