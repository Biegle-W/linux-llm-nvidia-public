"""gBench Golden Set chat-template and tool-call check for one router profile.

Run after the short DSH check on each engine update:
  python3 scripts/gbench_template_check.py --model PROFILE
One-time setup (venv and pinned tokenizer files):
  python3 scripts/gbench_template_check.py --setup
The model is selected and warmed first (gBench allows only 30 s per request, so a
cold load would fail), then the six cases run under the time limit in
config/gbench-template-check.json, then the router unloads. Results stay in
data/gbench-template/ (never committed).
"""
import argparse, json, os, shutil, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

R = Path(__file__).resolve().parents[1]
CONFIG = R / 'config/gbench-template-check.json'
ROUTER = 'http://127.0.0.1:10100'
sys.path.insert(0, str(R / 'scripts'))


def load_config():
    return json.loads(CONFIG.read_text())


def tokenizer_dir(cfg, model):
    spec = cfg['tokenizers'][model]
    return R / cfg['tokenizer_root'] / spec['repo'].replace('/', '__') / spec['revision'][:12]


def profile_model(profile_id):
    from profile_catalog import get_profile
    return get_profile(profile_id)['model']


def setup(cfg):
    venv = R / cfg['venv']
    if not (venv / 'bin/gbench').exists():
        uv = shutil.which('uv')
        if uv:
            subprocess.run([uv, 'venv', '-q', '-p', '3.12', str(venv)], check=True)
            subprocess.run([uv, 'pip', 'install', '-q', '-p', str(venv / 'bin/python'), f"gbench=={cfg['gbench_version']}", 'transformers'], check=True)
        else:
            subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
            subprocess.run([str(venv / 'bin/pip'), 'install', '-q', f"gbench=={cfg['gbench_version']}", 'transformers'], check=True)
    fetch = (
        'import json,sys\n'
        'from huggingface_hub import hf_hub_download, list_repo_files\n'
        'repo, rev, dest, wanted = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])\n'
        'have = set(list_repo_files(repo, revision=rev))\n'
        'got = [f for f in wanted if f in have]\n'
        'for f in got: hf_hub_download(repo, f, revision=rev, local_dir=dest)\n'
        'print(repo, rev[:12], got)\n'
    )
    for model, spec in cfg['tokenizers'].items():
        dest = tokenizer_dir(cfg, model)
        if (dest / '.complete').exists():
            print(model, 'tokenizer present'); continue
        dest.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(venv / 'bin/python'), '-c', fetch, spec['repo'], spec['revision'], str(dest), json.dumps(cfg['tokenizer_files'])], check=True)
        (dest / '.complete').write_text(spec['revision'] + '\n')


def verdict(cfg, summary, exit_code, wall_s):
    """PASS only if gbench exited 0 inside the limit and every configured case passed exactly once."""
    if exit_code != 0 or wall_s > cfg['time_limits_s']['gbench_run'] or summary.get('status') != 'passed' or summary.get('error_cases'):
        return 'FAIL'
    ids = [x.get('task_id') for x in summary.get('task_results', [])]
    ok = all(x.get('status') == 'passed' for x in summary.get('task_results', []))
    return 'PASS' if ok and sorted(ids) == sorted(cfg['tasks']) else 'FAIL'


class CheckError(Exception):
    pass


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--model'); g.add_argument('--setup', action='store_true')
    p.add_argument('--keep-loaded', action='store_true')
    a = p.parse_args(); os.umask(0o077); cfg = load_config()
    if a.setup:
        setup(cfg); return 0
    model = profile_model(a.model)
    tok = tokenizer_dir(cfg, model); gb = R / cfg['venv'] / 'bin/gbench'
    if not ((tok / '.complete').exists() and gb.exists()):
        raise SystemExit('Run --setup first')
    limits = cfg['time_limits_s']
    out = R / 'data/gbench-template' / f"{time.strftime('%Y%m%d-%H%M%S')}-{a.model}"
    out.mkdir(parents=True)
    state = {'model': a.model, 'tokenizer': str(tok.relative_to(R)), 'gbench_version': cfg['gbench_version'], 'tasks': cfg['tasks'], 'limits_s': limits}
    save = lambda: (out / 'state.json').write_text(json.dumps(state, indent=2) + '\n')
    key = (R / 'data/local-api-key').read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise SystemExit('Router key file is malformed')
    scrub = lambda text: text.replace(key, '<router-key>')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def req(path, body=None, timeout=60):
        q = urllib.request.Request(ROUTER + path, data=None if body is None else json.dumps(body).encode(),
                                   headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        with opener.open(q, timeout=timeout) as f:
            return json.load(f)

    selected = False
    try:
        unlock = subprocess.run(['gpu-unlock-health', 'status', '--brief'], capture_output=True, text=True)
        if unlock.returncode != 0 or unlock.stdout.strip() != 'GPU unlock: VERIFIED':
            raise CheckError('GPU unlock not verified: ' + unlock.stdout.strip()[:200])
        if (R / 'data/GPU-LOCK').exists():
            raise CheckError('data/GPU-LOCK exists')
        health = req('/health')
        if any(health.get(x) for x in ('busy', 'inflight', 'queued', 'loading_model', 'idle_unloading_model')):
            raise CheckError('Router is not idle')
        t = time.monotonic()
        try:
            req('/router/select', {'model': a.model}, timeout=limits['warmup'])
        except urllib.error.HTTPError as e:
            if e.code == 409:
                raise CheckError('Router refused the selection (409)')
            selected = True; raise
        except Exception:
            selected = True; raise
        selected = True
        req('/v1/chat/completions', {'model': a.model, 'messages': [{'role': 'user', 'content': 'Reply with OK.'}], 'max_tokens': 16}, timeout=limits['warmup'])
        state['warmup_s'] = round(time.monotonic() - t, 1); save()
        env = dict(os.environ, VLLM_API_KEY=key, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        cmd = [str(gb), '--golden-only', '--remote-endpoint', ROUTER + '/v1', '--models', a.model, '--served-model-id', a.model,
               '--tokenizer', str(tok), '--golden-tasks', *cfg['tasks'], '--results-dir', str(out / 'gbench')]
        t = time.monotonic()
        try:
            run = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=limits['gbench_run'])
            state['gbench_exit'] = run.returncode
            (out / 'gbench.log').write_text(scrub(run.stdout[-20000:] + run.stderr[-20000:]))
        except subprocess.TimeoutExpired:
            state['gbench_exit'] = 'timeout'
        wall = time.monotonic() - t; state['gbench_wall_s'] = round(wall, 1)
        summaries = sorted((out / 'gbench').glob('*/summary.json'))
        m = json.loads(summaries[-1].read_text())['models'][0] if summaries else {}
        state['cases'] = [[x.get('task_id'), x.get('status')] for x in m.get('task_results', [])]
        state['harness_errors'] = json.loads(scrub(json.dumps(m.get('harness_errors'))))
        state['verdict'] = verdict(cfg, m, state['gbench_exit'], wall)
    except Exception as e:
        state['verdict'] = 'FAIL'
        state['error'] = type(e).__name__ + (f' HTTP {e.code}' if isinstance(e, urllib.error.HTTPError) else '') + ': ' + scrub(str(e))[:300]
    finally:
        if selected and not a.keep_loaded:
            deadline = time.monotonic() + 180
            while True:
                try:
                    req('/router/unload', {}); state['unloaded'] = True; break
                except urllib.error.HTTPError as e:
                    if e.code != 409 or time.monotonic() > deadline:
                        state['unload_error'] = f'HTTP {e.code}'; break
                    time.sleep(3)
                except Exception as e:
                    state['unload_error'] = type(e).__name__; break
            if 'unload_error' in state:
                state['verdict'] = 'FAIL'
        save()
    print(json.dumps({k: state.get(k) for k in ('model', 'verdict', 'warmup_s', 'gbench_wall_s', 'cases', 'error', 'unloaded', 'unload_error')}))
    print('details:', out.relative_to(R))
    return 0 if state['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
