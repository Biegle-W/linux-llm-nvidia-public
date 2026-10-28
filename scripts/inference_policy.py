"""One idle/lifecycle policy for all maintained models and engine launch paths."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_SOURCES = {'Strata': 'runtimes/strata-terminal/terminal/0.1.51/serve/server.py',
                  'Maya': 'runtimes/project-maya/serve/server.py'}


def load_policy(root=ROOT):
    policy = json.loads((root / 'config/inference-policy.json').read_text())
    if (policy.get('schema') != 1 or type(policy.get('idle_timeout_s')) is not int
            or not 0 < policy['idle_timeout_s'] <= 86400
            or policy.get('lifecycle_telemetry') is not True
            or policy.get('visible_terminals_required') is not True):
        raise ValueError('Invalid required inference lifecycle policy')
    return policy


def apply_native_idle(config, profile, root=ROOT):
    policy = load_policy(root)
    source = (root / NATIVE_SOURCES[profile['engine']]).read_text()
    for marker in ['# Managed NVIDIA idle reservation', 'idle_activity_path', 'idle_lock_path']:
        if marker not in source:
            raise RuntimeError('Required native idle adapter missing for ' + profile['engine'])
    return dict(config, idle_unload_s=policy['idle_timeout_s'],
                idle_lock_path=str(root / 'data/GPU-LOCK'),
                idle_activity_path=str(root / 'data/router/activity' / (profile['id'] + '.txt')))
