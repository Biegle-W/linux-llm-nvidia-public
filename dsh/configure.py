#!/usr/bin/env python3
"""Register local models under one NVIDIA router provider; retain unrelated routes."""
import copy,json,sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from profile_catalog import load_catalog
ROUTER_ID='nvidia-strata'
ROUTER_URL='http://127.0.0.1:10100/v1'
LEGACY_ROUTER_IDS={'nvidia-hyperqwen','nvidia-sglang','nvidia-router','nvidia-maya','nvidia-vllm-offload'}
PLAIN='qwen27b-hyperqwen'
SEARCH=PLAIN+'-search'

def exposed_id(identifier):return SEARCH if identifier==PLAIN else identifier

def hyperqwen_search_only(providers):
    target=next((k for k,p in providers.items() if any(m.get('id')==SEARCH for m in p.get('models',[]))),None)
    if target is None:
        target=next((k for k,p in providers.items() if any(m.get('id')==PLAIN for m in p.get('models',[]))),None)
        if target is not None:
            m=next(m for m in providers[target]['models'] if m.get('id')==PLAIN);m.update(id=SEARCH,name='Qwen3.8-27B / HyperQwen-vLLM + Web Search (free)')
    kept=False
    for key,p in providers.items():
        if 'models' not in p:continue
        models=[]
        for m in p['models']:
            if m.get('id')==PLAIN:continue
            if m.get('id')==SEARCH:
                if key!=target or kept:continue
                kept=True
            models.append(m)
        p['models']=models
    return target

def router_providers(providers,profiles):
    result=copy.deepcopy(providers);managed={p['id'] for p in profiles}|{SEARCH}
    def local(key,p):return key in LEGACY_ROUTER_IDS|{ROUTER_ID} and p.get('baseURL',ROUTER_URL).rstrip('/')==ROUTER_URL
    keys=[k for k,p in result.items() if local(k,p)]
    preferred=ROUTER_ID if ROUTER_ID in keys else 'nvidia-strata' if 'nvidia-strata' in keys else next(iter(keys),None)
    base=copy.deepcopy(result[preferred]) if preferred else {}
    models={}
    def add_model(model):
        m=copy.deepcopy(model);original=m['id'];m['id']=exposed_id(original)
        if original==SEARCH:models[SEARCH]={**models.get(SEARCH,{}),**m}
        else:models.setdefault(m['id'],m)
    for key in ([preferred] if preferred else [])+[k for k in keys if k!=preferred]:
        for model in result[key].get('models',[]):
            add_model(model)
    for key,p in list(result.items()):
        if key in keys:del result[key];continue
        if p.get('baseURL','').rstrip('/')!=ROUTER_URL:continue
        remaining=[]
        for model in p.get('models',[]):
            if model.get('id') in managed:
                add_model(model)
            else:remaining.append(model)
        if 'models' in p:p['models']=remaining
    for p in profiles:
        identifier=exposed_id(p['id']);m=models.setdefault(identifier,{'id':identifier})
        m.setdefault('name',p.get('display_name') or p['model']+' / '+p['engine']+(' + Web Search (free)' if identifier==SEARCH else ''))
        if identifier==SEARCH and 'search' not in m['name'].lower():m['name']+=' + Web Search (free)'
        m.update(contextWindow=p['allocated_context'],maxTokens=4096,reasoningEfforts=False)
        m.setdefault('input',['text'])
    base.update(displayName='NVIDIA Server Router',api='openai-completions',baseURL=ROUTER_URL,defaultMaxTokens=4096,timeoutMs=7200000,streamIdleTimeoutMs=7200000,models=list(models.values()))
    base.setdefault('apiKeyEnv','LOCAL_LLM_API_KEY')
    base['compat']={**base.get('compat',{}),'supportsDeveloperRole':False,'maxTokensField':'max_tokens','supportsStore':False,'supportsStrictMode':False,'supportsReasoningEffort':False}
    result[ROUTER_ID]=base
    return result

def selection_routes(providers,profiles):
    managed={p['id'] for p in profiles}|{SEARCH}
    return {(key,m['id']):exposed_id(m['id']) for key,p in providers.items()
            if p.get('baseURL',ROUTER_URL if key in LEGACY_ROUTER_IDS|{ROUTER_ID} else '').rstrip('/')==ROUTER_URL
            for m in p.get('models',[]) if m.get('id') in managed}

def migrate_selection(value,field='',routes=None):
    if isinstance(value,dict):
        result={k:migrate_selection(v,k,routes) for k,v in value.items()}
        pair=(value.get('provider'),value.get('model'))
        if routes and all(isinstance(x,str) for x in pair) and pair in routes:
            result.update(provider=ROUTER_ID,model=routes[pair])
        return result
    if isinstance(value,list):return [migrate_selection(v,field,routes) for v in value]
    if field=='provider' and value in LEGACY_ROUTER_IDS:return ROUTER_ID
    if field in ('model','models') and value==PLAIN:return SEARCH
    return value

def configure(profile='web'):
    path=ROOT/'data/dsh/profiles'/profile/'cordis.patch.yml';path.parent.mkdir(parents=True,exist_ok=True)
    entries=yaml.safe_load(path.read_text()) if path.exists() else [];entries=entries or []
    if not isinstance(entries,list):raise ValueError('Expected a DSH profile patch list')
    llm=next((x for x in entries if x.get('id')=='llm-pi-ai'),None)
    if llm is None:llm={'id':'llm-pi-ai','config':{}};entries.append(llm)
    profiles=load_catalog()['profiles'];config=llm.setdefault('config',{});routes=selection_routes(config.get('providers',{}),profiles);config['providers']=router_providers(config.get('providers',{}),profiles)
    for e in entries:
        if e.get('id')!='llm-pi-ai':e['config']=migrate_selection(e.get('config',{}),routes=routes)
    selected=next((x for x in entries if x.get('id')=='agent-default-model'),None)
    if selected is None:entries.append({'id':'agent-default-model','config':{'provider':ROUTER_ID,'model':SEARCH}})
    temp=path.with_suffix('.tmp');temp.write_text(yaml.safe_dump(entries,sort_keys=False));temp.chmod(0o600);temp.replace(path)
    print(f'DSH registered {len(profiles)} maintained models under NVIDIA Server Router; unrelated routes preserved.')

if __name__=='__main__':configure('web');configure('headless')
