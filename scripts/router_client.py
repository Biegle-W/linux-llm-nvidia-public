#!/usr/bin/env python3
"""Select a model through the authenticated router; used by desktop entries."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]


def call(path, body=None):
    key = (ROOT / 'data/local-api-key').read_text().strip()
    req = urllib.request.Request('http://127.0.0.1:10100' + path,
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
            data=None if body is None else json.dumps(body).encode())
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=3600) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.load(error)['error']['message']
        except (ValueError, KeyError, TypeError):
            detail = 'Router returned HTTP ' + str(error.code)
        raise SystemExit(str(detail).replace(key, '[redacted]')) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=['hyperqwen', 'vllm', 'sglang', 'strata', 'maya'])
    parser.add_argument('--model')
    parser.add_argument('--desktop', action='store_true')
    parser.add_argument('--web', action='store_true')
    args = parser.parse_args()
    engines = {'hyperqwen': 'HyperQwen-vLLM', 'vllm': 'HyperQwen-vLLM', 'sglang': 'SGLang',
               'strata': 'Strata', 'maya': 'Maya'}
    models = call('/v1/models')['data']
    choices = [m for m in models if not args.engine or m['engine'] == engines[args.engine]]
    model = args.model
    if not model:
        for i, m in enumerate(choices, 1):
            print(f"{i}. {m['name']} / {m['quant']} / {m['context_window']:,} tokens")
        if len(choices) == 1:
            model = choices[0]['id']
        elif sys.stdin.isatty():
            try:
                index = int(input('Select model [1]: ').strip() or '1') - 1
                if index < 0:
                    raise ValueError
                model = choices[index]['id']
            except (ValueError, IndexError):
                sys.exit('Invalid selection.')
        else:
            sys.exit('Choose --model from the catalog.')
    if model not in {m['id'] for m in choices}:
        sys.exit('That model is not in the selected engine catalog.')
    print('Waiting for active replies to finish, then loading:', model, flush=True)
    result = call('/router/select', {'model': model})
    print(f"Ready: {result['model']} / {result['context_window']:,} tokens")
    if args.web:
        if args.engine not in ('strata', 'maya'):
            sys.exit('Native web apps are available for Strata and Maya.')
        print('Native web app: http://127.0.0.1:10000/ (open when convenient; startup does not activate a browser)')
    print('OpenAI API: http://127.0.0.1:10100/v1')
    print('The model remains available after this terminal closes. Select the same ID in DSH.')
    # The dedicated backend console remains visible. A finished selection
    # launcher must not look like another running inference engine.


if __name__ == '__main__':
    main()
