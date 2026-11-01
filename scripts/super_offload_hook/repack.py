"""Preserve Marlin's per-expert repack while staging one expert transpose at a time."""
import ast
from pathlib import Path

def repack_view(b_q_weight,size_k,size_n,num_bits,is_a_8bit=False):
 import torch
 canonical=b_q_weight.transpose(1,2)
 if num_bits!=4 or (size_k,size_n) not in [(1024,2688),(2688,1024)] or not canonical.is_contiguous():
  raise ValueError('Unreviewed Super expert packing layout')
 output=canonical.view(b_q_weight.shape[0],size_k//16,size_n*(num_bits//2))
 for e in range(b_q_weight.shape[0]):
  output[e]=torch.ops._C.gptq_marlin_repack(b_q_weight[e].contiguous(),size_k,size_n,num_bits,is_a_8bit)
 return output

def install(module):
 source=Path(module.__file__).read_text();parsed=ast.parse(source);functions=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='_process_weights_marlin']
 if len(functions)!=1:raise RuntimeError('Expected one reviewed Marlin converter')
 tree=ast.Module(body=functions,type_ignores=[]);count=0;calls=0
 class Patch(ast.NodeTransformer):
  def visit_Assign(self,node):
   nonlocal count
   if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['w13_qweight','w2_qweight']:
    v=node.value
    if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='contiguous' and isinstance(v.func.value,ast.Call) and isinstance(v.func.value.func,ast.Attribute) and v.func.value.func.attr=='transpose':
     node.value=v.func.value;count+=1
   return self.generic_visit(node)
  def visit_Call(self,node):
   nonlocal calls
   if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='ops' and node.func.attr=='gptq_marlin_moe_repack':
    node.func=ast.Name(id='_super_repack_view',ctx=ast.Load());calls+=1
   return self.generic_visit(node)
 tree=Patch().visit(tree)
 if count!=2 or calls!=2:raise RuntimeError('Unreviewed Marlin repack source; refusing patch')
 module.__dict__['_super_repack_view']=repack_view
 exec(compile(ast.fix_missing_locations(tree),module.__file__,'exec'),module.__dict__)
 print('SUPER_EXPERT_REPACK_VIEW','removed_full_transposes',count,'kernel_calls_redirected',calls,flush=True)
