#!/usr/bin/env python3
"""Benchmark all kept profiles at their installed contexts; preserve dated raw evidence."""
import argparse
import json
import os
from pathlib import Path
import random
import re
import signal
import statistics
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
from profile_catalog import load_catalog

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
VOCAB = 'river stone market lantern copper winter garden signal harbor needle orbit velvet canyon ember ledger quartz meadow anchor violet thunder'.split()


def metric_rows(text, metric, stage=None):
    rows = []
    for line in text.splitlines():
        if line.startswith('#') or not line:
            continue
        name = line.split('{', 1)[0].split()[0]
        if name != metric:
            continue
        labels = dict(re.findall(r'(\w+)="([^"\n]*)"', line))
        if stage and labels.get('stage') != stage:
            continue
        rows.append((labels, float(line.split()[-1])))
    return rows


def metric_delta(before, after, metric, stage=None):
    old = {tuple(sorted(labels.items())): value for labels, value in metric_rows(before, metric, stage)}
    rows = [(labels, value - old.get(tuple(sorted(labels.items())), 0))
            for labels, value in metric_rows(after, metric, stage)]
    rows = [(labels, value) for labels, value in rows if value > 0]
    # Pipeline replicas may publish separate samples; take the last stage, never add duplicate wall times.
    for rank in ['pp_rank', 'pipeline_parallel_rank']:
        values = [int(labels[rank]) for labels, _ in rows if rank in labels]
        if values:
            rows = [(labels, value) for labels, value in rows if int(labels.get(rank, -1)) == max(values)]
    # Tensor ranks execute the same request in parallel. Keep its sampling rank,
    # rather than summing duplicate request counts and overlapping durations.
    for rank in ['tp_rank', 'tensor_parallel_rank']:
        values = [int(labels[rank]) for labels, _ in rows if rank in labels]
        if values:
            selected = min(values)
            rows = [(labels, value) for labels, value in rows
                    if int(labels.get(rank, -1)) == selected]
    return sum(value for _, value in rows), rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/benchmarks' / time.strftime('%Y%m%d-%H%M%S-current'))
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.umask(0o077)
    key = (ROOT / 'data/local-api-key').read_text().strip()
    headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
    catalog = load_catalog()
    (out / 'catalog.json').write_text(json.dumps(catalog, indent=2))
    (ROOT / 'data/benchmark-latest-path').write_text(str(out))
    lock = ROOT / 'data/GPU-LOCK'
    token = {'owner': 'current-profile-benchmark', 'pid': os.getpid(), 'output': str(out)}
    stop = threading.Event()
    rows = []
    active = [None]

    def event(stage, **values):
        row = {'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'stage': stage, **values}
        (out / 'state.json').write_text(json.dumps(row, indent=2))
        with (out / 'events.jsonl').open('a') as f:
            f.write(json.dumps(row) + '\n')
        print(json.dumps(row), flush=True)

    def http(port, path, body=None, timeout=1800):
        return OPENER.open(urllib.request.Request(f'http://127.0.0.1:{port}' + path,
                   headers=headers, data=None if body is None else json.dumps(body).encode()), timeout=timeout)

    def metrics():
        with http(10000, '/metrics', timeout=5) as f:
            return f.read().decode()

    def select(name):
        start = time.monotonic()
        with http(10100, '/router/select', {'model': name}) as f:
            result = json.load(f)
        assert result['status'] == 'ready' and result['model'] == name
        return time.monotonic() - start

    def reserve():
        with lock.open('x') as f:
            f.write(json.dumps(token))
        lock.chmod(0o600)

    def release():
        if lock.exists() and json.loads(lock.read_text()) == token:
            lock.unlink()

    def messages(rep, warm=False):
        rng = random.Random(261026 + rep)
        words = ' '.join(rng.choice(VOCAB) for _ in range(512 if warm else 2000))
        nonce = f'FRESH-{out.name}-{rep}-' + ('WARM' if warm else 'MEASURED')
        return [{'role': 'system', 'content': nonce + '. You are a helpful assistant. Follow the request directly without internal reasoning.'},
                {'role': 'user', 'content': 'Reference notes:\n' + words + '\n\nWrite a detailed practical guide explaining how to organize a community garden. Include planning, soil, water, tools, volunteer coordination, seasonal maintenance and record keeping. Use at least 1000 words in continuous prose. Start the guide immediately and continue in detail.'}]

    fixtures = {**{f'measured-{rep}': messages(rep) for rep in range(3)}, 'warmup': messages(0, True)}
    (out / 'prompts.json').write_text(json.dumps(fixtures, indent=2))
    protocol = {'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'repetitions': 3, 'output_tokens': 128,
                'reference_words': 2000, 'warmup': {'reference_words': 512, 'output_tokens': 64},
                'temperature': 0, 'top_p': 1, 'seed': 261026, 'thinking': False, 'concurrency': 1,
                'context': 'Each kept profile retains its installed allocation.',
                'ttft': 'HTTP request to first nonempty content SSE delta, worker loopback API; load/warmup excluded.',
                'decode': '(completion_tokens - 1)/(last-content timestamp - first-content timestamp), same formula across engines.',
                'prefill': 'Native prompt timings for Strata/Maya; per-request native prefill-phase metric deltas for dense engines.',
                'cache': 'Unique early system tags; prefix reuse off in dense profiles; native cached counts checked; OS page cache not flushed.',
                'reservation': 'Router and DSH stay running. GPU reservation blocks other router generation/switching during measurements.',
                'safety': 'Existing worker cgroups, model guards and selected RAM budgets remain; monitor aborts below 8 GiB host available or at 82 C.'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2))

    def monitor():
        with (out / 'telemetry.jsonl').open('a') as f:
            while not stop.is_set():
                memory = {k: int(v.split()[0]) for k, v in (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
                          if k in ['MemAvailable', 'SwapFree', 'SwapTotal']}
                try:
                    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=index,temperature.gpu,memory.used,memory.free,power.draw',
                                                   '--format=csv,noheader,nounits'], text=True, timeout=5).strip()
                except Exception:
                    gpu = ''
                f.write(json.dumps({'time': time.time(), 'profile': active[0], 'memory_kib': memory, 'gpu_csv': gpu}) + '\n'); f.flush()
                if memory['MemAvailable'] < 8 * 1024 ** 2 or (gpu and any(float(line.split(',')[1]) >= 82 for line in gpu.splitlines())):
                    (out / 'SAFETY-STOP').write_text('Host RAM or GPU temperature guard reached.')
                stop.wait(5)

    def measure(profile, rep, warm=False):
        if (out / 'SAFETY-STOP').exists():
            raise RuntimeError('Benchmark resource guard reached; preserve results and inspect telemetry.')
        name = profile['id']; label = name + ('-warmup' if warm else f'-rep{rep}')
        dense = name.startswith('qwen27b-')
        before = metrics() if dense else ''
        (out / (label + '-metrics-before.txt')).write_text(before)
        with http(10000, '/v1/models', timeout=5) as f:
            model = json.load(f)['data'][0]['id']
        body = {'model': model, 'messages': fixtures['warmup' if warm else f'measured-{rep}'],
                'stream': True, 'stream_options': {'include_usage': True}, 'max_tokens': 64 if warm else 128,
                'temperature': 0, 'top_p': 1, 'seed': 261026, 'cache_prompt': False,
                'chat_template_kwargs': {'enable_thinking': False}}
        start = time.perf_counter(); first = last = None; text = ''; reasoning = ''; raw = []; usage = {}; native = {}; done = False; finish = None
        event('request-start', profile=name, case='warmup' if warm else 'measured', rep=rep)
        try:
            with http(10000, '/v1/chat/completions', body, timeout=1800) as response:
                for binary in response:
                    line = binary.decode(errors='replace').strip()
                    if not line.startswith('data:'):
                        continue
                    payload = line[5:].strip()
                    if payload == '[DONE]':
                        done = True; break
                    data = json.loads(payload); raw.append(data)
                    if data.get('error'):
                        raise RuntimeError(str(data['error']))
                    usage = data.get('usage') or usage; native = data.get('timings') or native
                    for choice in data.get('choices', []):
                        delta = choice.get('delta') or {}; content = delta.get('content') or ''; reason = delta.get('reasoning_content') or ''
                        if content:
                            now = time.perf_counter() - start
                            if first is None:
                                first = now
                            last = now
                        text += content; reasoning += reason
                        finish = choice.get('finish_reason') or finish
                    if (out / 'SAFETY-STOP').exists():
                        raise RuntimeError('Benchmark resource guard reached during inference.')
        except Exception as e:
            (out / (label + '-error.json')).write_text(json.dumps({'request': body, 'events': raw, 'error': str(e).replace(key, '[redacted]')}, indent=2))
            raise
        wall = time.perf_counter() - start
        n = usage.get('completion_tokens'); prompt = usage.get('prompt_tokens')
        row = {'profile': name, 'case': 'warmup' if warm else 'measured', 'rep': rep,
               'context': profile['allocated_context'], 'prompt_tokens': prompt, 'output_tokens': n,
               'ttft_s': first, 'last_content_s': last, 'wall_s': wall, 'usage': usage,
               'native_timings': native, 'client_decode_tps': (n - 1) / (last - first) if n and first is not None and last > first else None,
               'native_decode_tps': native.get('predicted_per_second'), 'prefill_tps': native.get('prompt_per_second'),
               'prefill_method': 'native prompt_n / native prompt time' if native else None,
               'cached_tokens': native.get('cache_n', (usage.get('prompt_tokens_details') or {}).get('cached_tokens', 0)),
               'finish_reason': finish, 'done': done, 'answer': text, 'reasoning': reasoning}
        # Preserve every completed response before interpreting optional engine counters.
        (out / (label + '-raw-response.json')).write_text(json.dumps({'request': body, 'events': raw, 'partial_result': row}, indent=2))
        if dense:
            metric = 'vllm:request_prefill_time_seconds' if name.endswith('hyperqwen') else 'sglang:per_stage_req_latency_seconds'
            stage = None if name.endswith('hyperqwen') else 'prefill_forward'
            for _ in range(50):
                after = metrics()
                count, count_rows = metric_delta(before, after, metric + '_count', stage)
                duration, duration_rows = metric_delta(before, after, metric + '_sum', stage)
                if count >= 1 and duration > 0:
                    break
                time.sleep(.2)
            (out / (label + '-metrics-after.txt')).write_text(after)
            row.update(prefill_metric_count=count, prefill_metric_count_rows=count_rows,
                       prefill_metric_duration_rows=duration_rows, prefill_s=duration,
                       prefill_tps=prompt / duration if duration > 0 else None,
                       prefill_method=metric + ('{stage="prefill_forward"}' if stage else '') + ' per-request delta')
            valid_count = count == 1
            if not valid_count or duration <= 0 or duration > first * 1.05 + .05:
                raise RuntimeError(f'Invalid native prefill interval/count {duration}/{count}; inspect {label} metric snapshots.')
        cap = 64 if warm else 128
        row['valid'] = bool(done and text.strip() and not reasoning and n == cap and row['client_decode_tps'] and row['prefill_tps']
                            and row['cached_tokens'] <= max(32, prompt * .03))
        (out / (label + '-response.json')).write_text(json.dumps({'request': body, 'events': raw, 'result': row}, indent=2))
        rows.append(row)
        with (out / 'requests.jsonl').open('a') as f:
            f.write(json.dumps(row) + '\n')
        event('request-finished', profile=name, rep=rep, case=row['case'], valid=row['valid'], prompt_tokens=prompt,
              output_tokens=n, ttft_s=round(first, 4) if first else first, prefill_tps=row['prefill_tps'],
              decode_tps=round(row['client_decode_tps'], 3) if row['client_decode_tps'] else None)
        if not row['valid']:
            raise RuntimeError('Invalid measured response: ' + label)

    thread = threading.Thread(target=monitor, daemon=True); thread.start()
    error = None
    def interrupted(*_):
        raise KeyboardInterrupt('Benchmark interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        # SGLang first verifies native metric availability before the slow streamed models.
        order = sorted(catalog['profiles'], key=lambda p: ['qwen27b-sglang', 'qwen27b-hyperqwen', 'flash-next-strata', 'glm-maya', 'deepseek-strata', 'deepseek-maya'].index(p['id']))
        for profile in order:
            active[0] = profile['id']; event('loading', profile=profile['id'])
            elapsed = select(profile['id']); reserve(); event('ready', profile=profile['id'], load_s=elapsed)
            unit = 'llm-test-qwen27b.service' if profile['id'].startswith('qwen27b-') else 'llm-router-worker.service'
            record = subprocess.check_output(['systemctl', '--user', 'show', unit, '-p', 'ExecStart', '-p', 'MemoryHigh', '-p', 'MemoryMax', '-p', 'MemorySwapMax'], text=True)
            (out / (profile['id'] + '-unit.txt')).write_text(record)
            if not profile['id'].startswith('qwen27b-'):
                cfg = json.loads((ROOT / 'data/router' / (profile['id'] + '-runtime.json')).read_text()); cfg.pop('api_key', None)
                (out / (profile['id'] + '-config-redacted.json')).write_text(json.dumps(cfg, indent=2))
            if profile['id'] == 'qwen27b-sglang':
                # HTTP model listing can become ready before SGLang's own small
                # non-streaming startup generation finishes. Do not mix its
                # prefill counters into the measured request.
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    samples = metric_rows(metrics(), 'sglang:num_requests_total')
                    if sum(v for labels, v in samples if labels.get('is_streaming') == 'false') >= 1:
                        break
                    time.sleep(.2)
                else:
                    raise RuntimeError('SGLang internal startup warm-up did not settle.')
            measure(profile, 0, True)
            for rep in range(3):
                measure(profile, rep)
            event('profile-complete', profile=profile['id']); release()
    except BaseException as e:
        error = (str(e) or type(e).__name__).replace(key, '[redacted]'); event('failed', error=error)
    finally:
        release(); event('restoring-default')
        try:
            select('qwen27b-hyperqwen'); event('default-restored')
        except Exception as e:
            error = error or 'Default restoration failed: ' + str(e).replace(key, '[redacted]')
            event('restore-failed', error=str(e).replace(key, '[redacted]'))
        stop.set(); thread.join(timeout=8)
        summary = []
        for profile in catalog['profiles']:
            selected = [r for r in rows if r['profile'] == profile['id'] and r['case'] == 'measured' and r['valid']]
            if not selected:
                continue
            item = {'profile': profile['id'], 'model': profile['model'], 'engine': profile['engine'], 'quant': profile['weight_quant'],
                    'context': profile['allocated_context'], 'tested_retrieval_input': profile.get('tested_retrieval_input'), 'repetitions': len(selected)}
            for field in ['ttft_s', 'prefill_tps', 'client_decode_tps', 'native_decode_tps', 'prompt_tokens', 'output_tokens', 'wall_s']:
                values = [r[field] for r in selected if r.get(field) is not None]
                if values:
                    item[field] = statistics.median(values)
                    item[field + '_range'] = [min(values), max(values)]
            item['prefill_method'] = selected[0]['prefill_method']; summary.append(item)
        (out / 'summary.json').write_text(json.dumps(summary, indent=2))
        event('complete' if not error else 'incomplete', completed_profiles=len(summary), error=error)
    if error:
        raise SystemExit(error)


if __name__ == '__main__':
    main()
