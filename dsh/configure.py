#!/usr/bin/env python3
"""Register maintained NVIDIA models while preserving custom DSH routes and aliases."""
import json
from pathlib import Path
import sys
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from profile_catalog import load_catalog


def hyperqwen_search_only(providers):
    """Expose one search alias while retaining the backend and provider settings."""
    plain, search = 'qwen27b-hyperqwen', 'qwen27b-hyperqwen-search'
    target = next((key for key, provider in providers.items()
                   if any(m.get('id') == search for m in provider.get('models', []))), None)
    if target is None:
        target = next((key for key, provider in providers.items()
                       if any(m.get('id') == plain for m in provider.get('models', []))), None)
        if target is not None:
            model = next(m for m in providers[target]['models'] if m.get('id') == plain)
            model['id'] = search
            model['name'] = 'Qwen3.8-27B / HyperQwen-vLLM + Web Search (free)'
    kept = False
    for key, provider in providers.items():
        if 'models' not in provider:
            continue
        models = []
        for model in provider.get('models', []):
            if model.get('id') == plain:
                continue
            if model.get('id') == search:
                if key != target or kept:
                    continue
                kept = True
            models.append(model)
        provider['models'] = models
    return target


def configure(profile='web'):
    path = ROOT / 'data/dsh/profiles' / profile / 'cordis.patch.yml'
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = yaml.safe_load(path.read_text()) if path.exists() else []
    entries = entries or []
    if not isinstance(entries, list):
        raise ValueError('Expected a DSH profile patch list.')
    def entry(name):
        existing = next((x for x in entries if isinstance(x, dict) and x.get('id') == name), None)
        if existing is None:
            existing = {'id': name, 'config': {}}
            entries.append(existing)
        return existing.setdefault('config', {})
    providers = entry('llm-pi-ai').setdefault('providers', {})
    hyperqwen_search_only(providers)
    profiles = load_catalog()['profiles']
    engine_keys = {'HyperQwen-vLLM': 'hyperqwen', 'SGLang': 'sglang',
                   'Strata': 'strata', 'Maya': 'maya', 'vLLM-offload': 'vllm-offload', 'vLLM-offload': 'vllm-offload'}
    for selected in profiles:
        exposed_id = 'qwen27b-hyperqwen-search' if selected['id'] == 'qwen27b-hyperqwen' else selected['id']
        matches = [model for provider in providers.values() for model in provider.get('models', [])
                   if model.get('id') == exposed_id]
        if not matches:
            key = 'nvidia-' + engine_keys[selected['engine']]
            provider = providers.setdefault(key, {
                'displayName': 'NVIDIA ' + selected['engine'], 'api': 'openai-completions',
                'baseURL': 'http://127.0.0.1:10100/v1', 'apiKeyEnv': 'LOCAL_LLM_API_KEY',
                'timeoutMs': 7200000, 'streamIdleTimeoutMs': 7200000,
                'compat': {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens',
                           'supportsStore': False, 'supportsStrictMode': False,
                           'supportsReasoningEffort': False}, 'models': []})
            model = {'id': exposed_id, 'name': selected['model'] + ' / ' + selected['engine'] + (' + Web Search (free)' if exposed_id.endswith('-search') else ''),
                     'input': ['text'], 'reasoningEfforts': False}
            provider.setdefault('models', []).append(model)
            matches = [model]
        for model in matches:
            model['contextWindow'] = selected['allocated_context']
            if selected['engine'] == 'vLLM-offload':
                model['maxTokens'] = 4096
            else:
                model.setdefault('maxTokens', 4096)
    target = hyperqwen_search_only(providers)
    selected = entry('agent-default-model')
    if selected.get('model') == 'qwen27b-hyperqwen':
        selected.update(provider=target, model='qwen27b-hyperqwen-search')
    if not selected:
        selected.update(provider=target or 'nvidia-hyperqwen', model='qwen27b-hyperqwen-search')
    temp = path.with_suffix('.tmp')
    temp.write_text(yaml.safe_dump(entries, sort_keys=False))
    temp.chmod(0o600)
    temp.replace(path)
    print(f'DSH registered {len(profiles)} maintained profiles; custom routes and aliases preserved.')


if __name__ == '__main__':
    configure('web')
    configure('headless')
