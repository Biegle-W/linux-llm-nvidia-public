"""Keep selected expert layers resident independently on the unequal GPU pair."""
import os,json
from pathlib import Path

def install(module):
 original=module.PrefetchOffloader.wrap_modules
 def placed(instance,modules_generator,prefix=''):
  setting=os.environ.get('SUPER_RESIDENT_EXPERT_LAYERS')
  if not setting:return original(instance,modules_generator,prefix)
  import torch.distributed as dist
  if dist.get_world_size()!=2 or instance.group_size!=1 or instance.num_in_group!=1:
   raise ValueError('Asymmetric placement requires the qualified EP2/all-layer offload layout')
  rank=dist.get_rank();counts=[int(x) for x in setting.split(',')]
  if len(counts)!=2 or rank not in (0,1):raise ValueError('Expected main GPU pair')
  blocks=json.loads((Path(os.environ['SUPER_CHECKPOINT_DIRECTORY'])/'config.json').read_text())['llm_config']['layers_block_type'];moe=[i for i,kind in enumerate(blocks) if kind=='moe'];n=counts[rank]
  if not 0<=n<=len(moe):raise ValueError('Invalid resident expert layer count')
  retained={moe[round(j*(len(moe)-1)/max(1,n-1))] for j in range(n)}
  if len(retained)!=n:raise ValueError('Resident placement collided')
  mamba=[i for i,kind in enumerate(blocks) if kind=='mamba']
  def select_counts(env_name):
   values=[int(x) for x in os.environ.get(env_name,'0,0').split(',')]
   if len(values)!=2 or any(not 0<=x<=len(mamba) for x in values):raise ValueError('Invalid projection placement')
   n=values[rank]
   result={mamba[round(j*(len(mamba)-1)/max(1,n-1))] for j in range(n)}
   if len(result)!=n:raise ValueError('Projection placement collided')
   return result
  input_cpu=select_counts('SUPER_INPUT_OFFLOAD_COUNTS');output_gpu=select_counts('SUPER_OUTPUT_RESIDENT_COUNTS')
  saved=instance.offload_params
  if set(saved)!={'experts','out_proj'}:raise ValueError('Unexpected offload recipe')
  def choices():
   for index,layer in enumerate(modules_generator):
    targets=set(saved)
    if index in retained:targets.discard('experts')
    if index in input_cpu:targets.add('in_proj')
    if index in output_gpu:targets.discard('out_proj')
    instance.offload_params=targets
    yield layer
  print('SUPER_RESIDENT_EXPERT_LAYERS','rank',rank,'indices',sorted(retained),'cpu_input_projections',sorted(input_cpu),'gpu_output_projections',sorted(output_gpu),flush=True)
  try:return original(instance,choices(),prefix)
  finally:instance.offload_params=saved
 module.PrefetchOffloader.wrap_modules=placed
