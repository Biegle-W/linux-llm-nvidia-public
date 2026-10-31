"""Verify the pinned Bolt adapter and build its guarded text-only command."""
import hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def relative(root,name):
 p=Path(name)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Runtime manifest path must stay relative')
 return Path(root)/p
def verify(profile,root=ROOT):
 root=Path(root);m=json.loads((root/'config/bolt-offload-runtime.json').read_text())
 if (m.get('schema')!=1 or profile['id']!='bolt-vllm' or profile['engine']!='vLLM-offload'
     or m['context']!=profile['allocated_context'] or m['gpu_indices']!=[0,1]
     or m['model_directory']!=profile['storage']['checkpoint_directory']):raise ValueError('Bolt manifest/profile mismatch')
 for path,value in m['runtime_sha256'].items():
  if digest(relative(root,path))!=value:raise ValueError('Pinned Bolt runtime source changed: '+path)
 model=relative(root,m['model_directory'])
 for name,value in m['model_source_sha256'].items():
  if digest(relative(model,name))!=value:raise ValueError('Reviewed Bolt checkpoint metadata/source changed: '+name)
 for name,size in m['weight_sizes'].items():
  if relative(model,name).stat().st_size!=size:raise ValueError('Bolt weight size changed: '+name)
 return m

def build_launch(profile,key,root=ROOT):
 root=Path(root);m=verify(profile,root);model=relative(root,m['model_directory'])
 config=json.loads((model/'config.json').read_text());quant=config['quantization_config'];changed=0
 for group in quant['config_groups'].values():
  targets=group['targets'];updated=[x.replace('(?:up_proj|down_proj)','(?:gate_proj|up_proj|down_proj)') for x in targets];changed+=updated!=targets;group['targets']=updated
 if not changed:raise ValueError('Unreviewed Bolt quantization target mapping')
 args=[str(relative(root,m['binary'])),'serve',str(model),
       '--host','127.0.0.1','--port','10000','--trust-remote-code','--language-model-only',
       '--dtype','bfloat16','--max-model-len',str(m['context']),'--max-num-seqs','1',
       '--max-num-batched-tokens',str(m['prefill_batch_tokens']),'--tensor-parallel-size','2',
       '--pipeline-parallel-size','1','--gpu-memory-utilization','0.85','--enforce-eager',
       '--served-model-name','bolt','--offload-backend','prefetch','--offload-group-size','1',
       '--offload-num-in-group','1','--offload-prefetch-step','1','--offload-params','experts','out_proj',
       '--hf-overrides',json.dumps({'quantization_config':quant})]
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1',CUDA_DEVICE_ORDER='PCI_BUS_ID',NCCL_P2P_DISABLE='0',NCCL_P2P_LEVEL='SYS',
          VLLM_WEIGHT_OFFLOADING_DISABLE_PIN_MEMORY='1',VLLM_WEIGHT_OFFLOADING_DISABLE_UVA='1',
          OMP_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',VLLM_ALLOW_LONG_MAX_MODEL_LEN='0',
          BOLT_POSTLOAD_CACHE_TRIM='1',BOLT_PREFETCH_EARLY_SYNC='1',BOLT_CHECKPOINT_DIRECTORY=str(model),PYTHONPATH=str(root/'scripts/bolt_offload_hook'),VLLM_API_KEY=key)
 return args,env
