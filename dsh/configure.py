#!/usr/bin/env python3
"""Register the selected NVIDIA models in DSH without storing the API key in YAML."""
import json
from pathlib import Path
import sys
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from profile_catalog import load_catalog


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
    groups = {}
    for p in load_catalog()['profiles']:
        key = {'HyperQwen-vLLM': 'hyperqwen', 'SGLang': 'sglang', 'Strata': 'strata', 'Maya': 'maya'}[p['engine']]
        groups.setdefault(key, []).append(p)
    for key, profiles in groups.items():
        providers['nvidia-' + key] = {
            'displayName': 'NVIDIA ' + profiles[0]['engine'], 'api': 'openai-completions',
            'baseURL': 'http://127.0.0.1:10100/v1', 'apiKeyEnv': 'LOCAL_LLM_API_KEY',
            'timeoutMs': 7200000, 'streamIdleTimeoutMs': 7200000,
            'compat': {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens',
                       'supportsStore': False, 'supportsStrictMode': False,
                       'supportsReasoningEffort': False},
            'models': [{'id': p['id'], 'name': p['model'] + ' / ' + p['engine'],
                        'contextWindow': p['allocated_context'], 'maxTokens': 4096,
                        'input': ['text'], 'reasoningEfforts': False} for p in profiles]}
    selected = entry('agent-default-model')
    if not selected:
        selected.update(provider='nvidia-hyperqwen', model='qwen27b-hyperqwen')
    temp = path.with_suffix('.tmp')
    temp.write_text(yaml.safe_dump(entries, sort_keys=False))
    temp.chmod(0o600)
    temp.replace(path)
    print('DSH registered six profiles in four NVIDIA engine providers.')


if __name__ == '__main__':
    configure('web')
    configure('headless')
