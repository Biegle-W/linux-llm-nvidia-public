"""Verify the independently pinned Super runtime and build its guarded text command."""
import json,os,uuid,subprocess
from pathlib import Path
from bolt_runtime import digest,relative
ROOT=Path(__file__).resolve().parents[1]
def verify(profile,root=ROOT):
 root=Path(root);m=json.loads((root/'config/super-offload-runtime.json').read_text())
 if (m.get('schema')!=1 or profile['id']!='super-vllm' or profile['engine']!='vLLM-offload' or m['profile']!=profile['id'] or m['context']!=profile['allocated_context'] or m['gpu_indices']!=[0,1] or m['model_directory']!=profile['storage']['checkpoint_directory']):raise ValueError('Super manifest/profile mismatch')
 if not 0<m['file_backing_mib_per_rank']<=2048:raise ValueError('Super file backing exceeds qualified cap')
 for path,value in m['runtime_sha256'].items():
  if digest(relative(root,path))!=value:raise ValueError('Pinned Super runtime source changed: '+path)
 backing=relative(root,m['processed_backing_directory'])
 if profile['storage'].get('processed_backing_directory')!=m['processed_backing_directory'] or profile['storage'].get('processed_backing_transport')!='nvme':raise ValueError('Super processed backing policy mismatch')
 backing.mkdir(exist_ok=True,mode=0o700)
 device=subprocess.check_output(['findmnt','-n','-o','SOURCE','--target',str(backing)],text=True).strip().split('[',1)[0]
 inventory=subprocess.check_output(['lsblk','--inverse','--noheadings','--raw','--output','TYPE,TRAN','--',device],text=True)
 if {parts[1] for line in inventory.splitlines() if len(parts:=line.split())==2 and parts[0]=='disk'}!={'nvme'}:raise ValueError('Super processed backing requires NVMe')
 model=relative(root,m['model_directory'])
 for name,value in m['model_source_sha256'].items():
  if digest(relative(model,name))!=value:raise ValueError('Reviewed Super checkpoint source changed: '+name)
 for name,size in m['weight_sizes'].items():
  if relative(model,name).stat().st_size!=size:raise ValueError('Super weight size changed: '+name)
 return m

def build_launch(profile,key,root=ROOT):
 root=Path(root);m=verify(profile,root);model=relative(root,m['model_directory']);run=os.environ.get('INVOCATION_ID') or uuid.uuid4().hex
 if len(run)!=32 or any(x not in '0123456789abcdef' for x in run):raise ValueError('Invalid backing ownership token')
 backing=relative(root,m['processed_backing_directory'])/('router-'+run)
 if backing.exists():raise ValueError('Super backing ownership path already exists')
 args=[str(relative(root,m['binary'])),'-m','vllm.entrypoints.cli.main','serve',str(model),'--host','127.0.0.1','--port','10000','--trust-remote-code','--language-model-only','--dtype','bfloat16','--max-model-len',str(m['context']),'--max-num-seqs','1','--max-num-batched-tokens',str(m['prefill_batch_tokens']),'--tensor-parallel-size','2','--pipeline-parallel-size','1','--enable-expert-parallel','--gpu-memory-utilization','0.85','--kv-cache-memory-bytes',str(m['kv_cache_mib_per_gpu']*2**20),'--enforce-eager','--served-model-name','super','--default-chat-template-kwargs',json.dumps({'enable_thinking':False}),'--offload-backend','prefetch','--offload-group-size','1','--offload-num-in-group','1','--offload-prefetch-step','1','--offload-params','experts','out_proj','--enable-auto-tool-choice','--tool-call-parser','qwen3_coder','--no-enable-prefix-caching','--mamba-cache-mode','none']
 env=dict(os.environ,VLLM_USE_FLASHINFER_SAMPLER='0',CUDA_VISIBLE_DEVICES='0,1',CUDA_DEVICE_ORDER='PCI_BUS_ID',NCCL_P2P_DISABLE='0',NCCL_P2P_LEVEL='SYS',VLLM_WEIGHT_OFFLOADING_DISABLE_PIN_MEMORY='1',VLLM_WEIGHT_OFFLOADING_DISABLE_UVA='1',OMP_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',VLLM_ALLOW_LONG_MAX_MODEL_LEN='0',SUPER_POSTLOAD_CACHE_TRIM='1',SUPER_PREFETCH_EARLY_SYNC='1',SUPER_CHECKPOINT_DIRECTORY=str(model),PYTHONPATH=str(root/'scripts/super_offload_hook'),PYTHONUNBUFFERED='1',VLLM_API_KEY=key,SUPER_RESIDENT_EXPERT_LAYERS=m['resident_expert_layers'],SUPER_INPUT_OFFLOAD_COUNTS=m['cpu_input_projection_counts'],SUPER_OUTPUT_RESIDENT_COUNTS=m['gpu_output_projection_counts'],SUPER_FILE_BACKING_DIRECTORY=str(backing),SUPER_FILE_BACKING_MIB_PER_RANK=str(m['file_backing_mib_per_rank']))
 return args,env
