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
MODEL_REPLACEMENTS={'flash-next-iq1s-llamacpp':'flash-next-iq1m-strata'}
RETIRED={'super-vllm','super-strata-trial'}|set(MODEL_REPLACEMENTS)

def exposed_id(identifier):return PLAIN if identifier==SEARCH else identifier

def router_providers(providers,profiles):
    result=copy.deepcopy(providers);managed={p['id'] for p in profiles}|{SEARCH}
    def local(key,p):return key in LEGACY_ROUTER_IDS|{ROUTER_ID} and p.get('baseURL',ROUTER_URL).rstrip('/')==ROUTER_URL
    keys=[k for k,p in result.items() if local(k,p)]
    preferred=ROUTER_ID if ROUTER_ID in keys else 'nvidia-strata' if 'nvidia-strata' in keys else next(iter(keys),None)
    base=copy.deepcopy(result[preferred]) if preferred else {}
    models={}
    def add_model(model):
        if model.get('id') in RETIRED:return
        m=copy.deepcopy(model);original=m['id'];m['id']=exposed_id(original)
        if original==SEARCH:models[PLAIN]={**models.get(PLAIN,{}),**m}
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
        if identifier=='bolt-vllm':m['name']=p.get('display_name') or p['model']+' / '+p['engine']
        m.setdefault('name',p.get('display_name') or p['model']+' / '+p['engine'])
        if identifier==PLAIN and 'web search' in m['name'].lower():m['name']=p.get('display_name') or p['model']+' / '+p['engine']
        m.update(contextWindow=p['allocated_context'],maxTokens=4096,reasoningEfforts=False)
        m.setdefault('input',['text'])
    disabled={p['id'] for p in profiles if p.get('availability',{}).get('enabled',True) is False}
    models={k:v for k,v in models.items() if k not in disabled}
    base.update(displayName='NVIDIA server',api='openai-completions',baseURL=ROUTER_URL,defaultMaxTokens=4096,timeoutMs=7200000,streamIdleTimeoutMs=7200000,models=list(models.values()))
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
        if isinstance(pair[0],str) and pair[0] in LEGACY_ROUTER_IDS|{ROUTER_ID} and isinstance(pair[1],str) and pair[1] in RETIRED:
            result.update(provider=ROUTER_ID,model=MODEL_REPLACEMENTS.get(pair[1],PLAIN))
        elif routes and all(isinstance(x,str) for x in pair) and pair in routes:
            result.update(provider=ROUTER_ID,model=routes[pair])
        elif isinstance(pair[0],str) and pair[0] in LEGACY_ROUTER_IDS|{ROUTER_ID} and pair[1]==SEARCH:
            result.update(provider=ROUTER_ID,model=PLAIN)
        return result
    if isinstance(value,list):return [migrate_selection(v,field,routes) for v in value]
    if field=='provider' and value in LEGACY_ROUTER_IDS:return ROUTER_ID
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
    if selected is None:entries.append({'id':'agent-default-model','config':{'provider':ROUTER_ID,'model':PLAIN}})
    elif selected.get('config',{}).get('model') in {p['id'] for p in profiles if p.get('availability',{}).get('enabled',True) is False}:selected['config']={'provider':ROUTER_ID,'model':PLAIN}
    # Auxiliary title inference can switch the sole GPU worker away from an agent.
    title=next((x for x in entries if x.get('id')=='session-title-llm'),None)
    if title is None:entries.append({'id':'session-title-llm','disabled':True,'config':{}})
    else:title['disabled']=True
    temp=path.with_suffix('.tmp');temp.write_text(yaml.safe_dump(entries,sort_keys=False));temp.chmod(0o600);temp.replace(path)
    print(f'DSH registered {sum(p.get("availability",{}).get("enabled",True) for p in profiles)} enabled models under NVIDIA Server Router; unrelated routes preserved.')

if __name__=='__main__':configure('web');configure('headless')
