#!/usr/bin/env python3
"""Read and validate the single selected setting for each model/quant/engine."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'config/maintained-profiles.json'


def worker_budget(profile):
    dense = profile['id'].startswith('qwen27b-')
    large = profile['id'] in ('flash-next-strata', 'glm-maya')
    default = {'high': 44 if large else 30, 'max': 48 if large else 36, 'swap': None}
    budget = profile.get('worker_memory_gib', default)
    if (set(budget) != {'high', 'max', 'swap'}
            or any(type(budget[k]) is not int for k in ('high', 'max'))
            or not (0 < budget['high'] <= budget['max'] - 2
                    and budget['max'] <= (36 if dense else 48))
            or budget['swap'] is not None):
        raise ValueError(f"Invalid bounded worker budget: {profile['id']}")
    return dict(budget)


def validate_catalog(catalog):
    if catalog.get('schema') != 1:
        raise ValueError('Unsupported maintained-profile catalog schema.')
    groups, identifiers, launches = set(), set(), set()
    for profile in catalog['profiles']:
        identifier = profile['id']
        group = tuple(profile[k] for k in ('model', 'weight_quant', 'engine'))
        launch = tuple(profile['launch'])
        if identifier in identifiers or group in groups or launch in launches:
            raise ValueError(f'Duplicate maintained profile: {identifier}')
        if profile['status'] != 'selected' or profile['allocated_context'] <= 0:
            raise ValueError(f'Unselected or invalid profile: {identifier}')
        identifiers.add(identifier)
        groups.add(group)
        launches.add(launch)
        storage = profile['storage']
        location = Path(storage['checkpoint_directory'])
        expected = {'gpu-resident': 'sata', 'ram-resident': 'sata', 'ssd-streaming': 'nvme'}
        if (storage.get('access') not in expected
                or storage.get('required_transport') != expected[storage['access']]
                or location.is_absolute() or '..' in location.parts):
            raise ValueError(f'Invalid model storage policy: {identifier}')
        worker_budget(profile)
        args = profile.get('cli_args', [])
        for flag in ('--max-model-len', '--ctx-size'):
            if flag in args and int(args[args.index(flag) + 1]) != profile['allocated_context']:
                raise ValueError(f'Context metadata disagrees with arguments: {identifier}')
        if '--cpu-offload-gb' in args and float(args[args.index('--cpu-offload-gb') + 1]) != 0:
            raise ValueError(f'Dense weight offload is not qualified: {identifier}')
        server = profile.get('server_args', {})
        if server and (server['context_length'] != profile['allocated_context']
                       or server.get('cpu_offload_gb', 0) != 0):
            raise ValueError(f'Invalid dense server setting: {identifier}')
    return catalog


def load_catalog():
    return validate_catalog(json.loads(CATALOG.read_text()))


def get_profile(identifier):
    for profile in load_catalog()['profiles']:
        if profile['id'] == identifier:
            return profile
    raise ValueError(f'No maintained profile named {identifier}')


if __name__ == '__main__':
    for profile in load_catalog()['profiles']:
        command = './scripts/start_model.sh ' + ' '.join(profile['launch'])
        print(f"{profile['id']}: {profile['allocated_context']} allocated tokens; {command}")
