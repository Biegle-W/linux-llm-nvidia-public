"""Build bounded native Wan baseline/Raylight trials with GPU-prepared conditioning."""
import hashlib
import json
from pathlib import Path
import subprocess

def graph(stage, seed):
    def node(class_type,**inputs):return dict(class_type=class_type,inputs=inputs)
    if stage=='mesh-prepare':
        return {'9':node('NvidiaPrepareLTXPrompt',prompt='A red fox standing in snow slowly turns its head toward the camera and blinks. Gentle snowflakes drift through the air. Static camera, natural sunrise light, realistic smooth motion. Quiet winter ambience.')}
    if stage=='mesh':
        return {
          '1':node('NvidiaMeshDenoiser'),
          '11':node('MeshSplitLTX',model=['1',0],n_blocks_remote=20,remote_host='127.0.0.1',remote_port=7777,codec_mode='raw',forward_client_loras=False),
          '2':node('NvidiaPreparedLTXConditioning'),
          '12':node('LTXVConditioning',positive=['2',0],negative=['2',1],frame_rate=24.0),
          '3':node('NvidiaMeshVAE',kind='video'),'13':node('NvidiaMeshVAE',kind='audio'),
          '4':node('EmptyLTXVLatentVideo',width=512,height=288,length=33,batch_size=1),
          '14':node('LTXVEmptyLatentAudio',frames_number=33,frame_rate=24.0,batch_size=1,audio_vae=['13',0]),
          '15':node('LTXVConcatAVLatent',video_latent=['4',0],audio_latent=['14',0]),
          '16':node('RandomNoise',noise_seed=seed),
          '17':node('ManualSigmas',sigmas='1.0,0.99375,0.9875,0.98125,0.975,0.909375,0.725,0.421875,0.0'),
          '18':node('KSamplerSelect',sampler_name='euler'),
          '19':node('CFGGuider',model=['11',0],positive=['12',0],negative=['12',1],cfg=1.0),
          '7':node('SamplerCustomAdvanced',noise=['16',0],guider=['19',0],sampler=['18',0],sigmas=['17',0],latent_image=['15',0]),
          '22':node('NvidiaReleaseMeshServer',samples=['7',0]),
          '20':node('LTXVSeparateAVLatent',av_latent=['22',0]),
          '8':node('VAEDecodeTiled',samples=['20',0],vae=['3',0],tile_size=128,overlap=32,temporal_size=16,temporal_overlap=4),
          '21':node('LTXVAudioVAEDecode',samples=['20',1],audio_vae=['13',0]),
          '10':node('CreateVideo',images=['8',0],fps=24.0,audio=['21',0]),
          '9':node('SaveVideo',video=['10',0],filename_prefix='ltx-mesh-'+str(seed),format='mp4')}
    if stage=='prepare':
        return {'9':node('NvidiaPrepareWanPrompt',prompt='A red fox standing in snow slowly turns its head toward the camera and blinks. Gentle snowflakes drift through the air. Static camera, natural sunrise light, realistic smooth motion.')}
    g={'2':node('NvidiaPreparedWanConditioning'),'3':node('NvidiaVideoVAE'),
       '4':node('Wan22ImageToVideoLatent',vae=['3',0],width=512,height=288,length=33,batch_size=1),
       '8':node('VAEDecode',samples=['7',0],vae=['3',0]),
       '10':node('CreateVideo',images=['8',0],fps=16.0),
       '9':node('SaveVideo',video=['10',0],filename_prefix='wan-'+stage+'-'+str(seed),format='mp4')}
    if stage=='baseline':
        g.update({'1':node('NvidiaVideoDenoiser'),'5':node('ModelSamplingSD3',model=['1',0],shift=8.0),
                  '7':node('KSampler',model=['5',0],positive=['2',0],negative=['2',1],latent_image=['4',0],seed=seed,
                           steps=20,cfg=5.0,sampler_name='euler',scheduler='simple',denoise=1.0)})
    else:
        g.update({'11':node('RayInitializer',ray_cluster_address='local',ray_cluster_namespace='nvidia-guarded-video',
                           GPU=2,ulysses_degree=2,ring_degree=1,cfg_degree=1,dp_degree=1,sync_ulysses=False,
                           clear_vram_after_sampling=False,FSDP=True,FSDP_CPU_OFFLOAD=False,XFuser_attention='TORCH_FLASH',skip_comm_test=False,use_mmap=True),
                  '1':node('RayUNETLoader',unet_name='wan2.2_ti2v_5B_fp16.safetensors',weight_dtype='default',ray_actors_init=['11',0]),
                  '5':node('RayModelSamplingSD3',ray_actors=['1',0],shift=8.0),
                  '7':node('XFuserKSamplerAdvanced',ray_actors=['5',0],add_noise='enable',noise_seed=seed,steps=20,cfg=5.0,
                           sampler_name='euler',scheduler='simple',positive=['2',0],negative=['2',1],latent_image=['4',0],
                           start_at_step=0,end_at_step=10000,return_with_leftover_noise='disable',denoise=1.0)})
    return g

def output(root,work,stage,seed,elapsed):
    if stage in ('prepare','mesh-prepare'):
        proof=json.loads((work/'prompt-proof.json').read_text())
        assert proof['parameter_devices']==(['cuda:0','cuda:1'] if stage=='mesh-prepare' else ['cuda:0']) and proof['CPU_weight_offload'] is False
        return dict(seed=seed,wall_s=elapsed,prompt_proof=proof)
    files=list((work/'images').rglob('*'+str(seed)+'*.mp4'))
    assert len(files)==1,'Exactly one video output required'
    image=files[0]
    code="import av,json,sys; c=av.open(sys.argv[1]); frames=list(c.decode(video=0)); print(json.dumps(dict(frames=len(frames),width=frames[0].width,height=frames[0].height)))"
    value=json.loads(subprocess.check_output([str(root/'runtimes/env-comfy-video/bin/python'),'-c',code,str(image)],text=True))
    assert value==dict(frames=33,width=512,height=288),'Decoded video shape mismatch'
    if stage=='mesh':
        assert (work/'mesh-server-stopped').exists(),'Mesh denoiser must release GPU1 before decoding'
        audio_code="import av,json,sys; c=av.open(sys.argv[1]); f=list(c.decode(audio=0)); print(json.dumps(dict(audio_samples=sum(x.samples for x in f),audio_sample_rate=f[0].sample_rate)))"
        audio=json.loads(subprocess.check_output([str(root/'runtimes/env-comfy-video/bin/python'),'-c',audio_code,str(image)],text=True))
        assert audio['audio_samples']>0
        value.update(audio)
    return dict(seed=seed,wall_s=elapsed,video=str(image),video_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),**value)

def audit(work):
    paths=list(work.rglob('forward-audits/*.jsonl'))
    rows=[json.loads(line) for path in paths for line in path.read_text().splitlines()]
    assert rows and not any(row.get('violation') for row in rows),'GPU-forward residency audit failed/missing'
    assert all(all(device.startswith('cuda:') for device in row['devices']) for row in rows)
    uuids=sorted({uuid for row in rows for uuid in row.get('cuda_device_uuids',[])})
    if (work/'video-stage.json').exists() and json.loads((work/'video-stage.json').read_text())['stage'] in ('baseline','raylight','mesh','mesh-prepare','entry'):
        assert len(uuids)==2,'Both physical GPUs must have audited neural forwards'
    return dict(physical_gpu_count=len(uuids),audited_modules=len(rows),processes=len(paths),physical_GPU_assignments=sorted({row['CUDA_VISIBLE_DEVICES'] or '' for row in rows}))
