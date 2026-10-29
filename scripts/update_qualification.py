"""Paired fixed fixtures and lifecycle gates through normal guarded workers."""
import base64
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import struct
import subprocess
import sys
import threading
import time
import urllib.request
import zlib
from update_transaction import write_json

VOCAB = 'river stone market lantern copper winter garden signal harbor needle orbit velvet canyon ember ledger quartz meadow anchor violet thunder'.split()


def check_memory_events(text):
    """A soft high-watermark throttle is evidence, not a hard allocation failure."""
    values=dict(line.split() for line in text.splitlines())
    required=('high','max','oom','oom_kill')
    if any(k not in values for k in required): raise RuntimeError('Missing memory-event telemetry')
    counts={k:int(values[k]) for k in required}
    if any(v<0 for v in counts.values()): raise RuntimeError('Invalid memory-event telemetry')
    if any(counts[k] for k in ('max','oom','oom_kill')): raise RuntimeError('Worker hard-memory-limit/oom event')
    return counts


class Qualification:
    def __init__(self, root, profile, output, manager, owner):
        self.root, self.p, self.out = Path(root), profile, Path(output)
        self.out.mkdir(parents=True, exist_ok=False)
        self.manager, self.owner = manager, owner
        self.key = (self.root / 'data/local-api-key').read_text().strip()
        self.headers = {'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'}
        self.op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.stop = threading.Event(); self.errors = []; self.samples = 0; self.invocations = set()
        sys.path.insert(0, str(self.root / 'scripts'))
        from profile_catalog import host_ram_reserve_gib
        self.floor = host_ram_reserve_gib(profile)
        self.fixtures = []
        for i in range(4):
            rng = random.Random(261026 + i)
            words = ' '.join(rng.choice(VOCAB) for _ in range(512 if i == 0 else 2000))
            self.fixtures.append([{'role': 'system', 'content': f'FIXED-NVIDIA-NIGHTLY-{i}. Follow the request directly without reasoning.'},
                {'role': 'user', 'content': words + '\nWrite a complete community-garden handbook with 40 chapters of 400 words each. Begin Chapter 1 immediately. Write detailed paragraphs until the response limit.'}])

    def http(self, path, body=None, timeout=7200):
        return self.op.open(urllib.request.Request('http://127.0.0.1:10000' + path,
            headers=self.headers, data=None if body is None else json.dumps(body).encode()), timeout=timeout)

    def metrics(self):
        with self.http('/metrics', timeout=5) as f: return f.read().decode()

    def record(self, name, data): write_json(self.out / (name + '.json'), data)

    def request(self, name, messages, cap=128, speed=False, tools=None):
        dense = self.p['id'].startswith('qwen27b-')
        before = self.metrics() if dense and speed else ''
        body = {'model': self.manager.backend_models()[0]['id'], 'messages': messages,
                'stream': True, 'stream_options': {'include_usage': True}, 'temperature': 0,
                'top_p': 1, 'seed': 261026, 'max_tokens': cap, 'cache_prompt': False,
                'reasoning_effort': 'none', 'chat_template_kwargs': {'enable_thinking': False}}
        if tools: body.update(tools=tools, tool_choice='required')
        self.record(name + '-request', body)
        started = time.monotonic(); first = last = None; text = ''; reasoning = ''; usage = {}; native = {}; calls = {}; done = False
        with (self.out / (name + '-sse.jsonl')).open('w') as events, self.http('/v1/chat/completions', body) as response:
            for line in response:
                if self.errors: raise RuntimeError(self.errors[0])
                if not line.startswith(b'data:'): continue
                payload = line[5:].strip()
                if payload == b'[DONE]': done = True; break
                row = json.loads(payload); events.write(json.dumps(row) + '\n'); events.flush()
                if row.get('error'): raise RuntimeError('Worker returned inference error')
                usage = row.get('usage') or usage; native = row.get('timings') or native
                for choice in row.get('choices', []):
                    delta = choice.get('delta') or {}; part = delta.get('content') or ''
                    reasoning += delta.get('reasoning_content') or ''
                    if part:
                        now = time.monotonic()
                        if first is None: first = now
                        last = now; text += part
                    for tool in delta.get('tool_calls') or []:
                        call = calls.setdefault(tool.get('index', 0), {'name': '', 'arguments': ''})
                        function = tool.get('function') or {}
                        call['name'] += function.get('name') or ''; call['arguments'] += function.get('arguments') or ''
        result = {'done': done, 'answer': text, 'reasoning': reasoning, 'usage': usage, 'native_timings': native,
                  'ttft_s': first - started if first else None, 'generation_s': last - first if last and first else 0,
                  'wall_s': time.monotonic() - started, 'tool_calls': list(calls.values()),
                  'decode_tps': (usage.get('completion_tokens', 0) - 1) / (last - first) if last and first and last > first else None,
                  'prefill_tps': native.get('prompt_per_second')}
        self.record(name + '-response', result)
        if not done or reasoning or not (text.strip() or calls): raise RuntimeError('Incomplete/empty/thinking response')
        if speed:
            if usage.get('completion_tokens') != cap: raise RuntimeError('Speed request ended before fixed output limit')
            cached = native.get('cache_n', (usage.get('prompt_tokens_details') or {}).get('cached_tokens', 0))
            if cached > 32: raise RuntimeError('Fixed speed fixture reused prompt cache')
            if dense:
                from benchmark_models import metric_delta
                metric = 'vllm:request_prefill_time_seconds' if self.p['id'].endswith('hyperqwen') else 'sglang:per_stage_req_latency_seconds'
                stage = None if self.p['id'].endswith('hyperqwen') else 'prefill_forward'
                for _ in range(50):
                    after = self.metrics()
                    count, _ = metric_delta(before, after, metric + '_count', stage)
                    duration, _ = metric_delta(before, after, metric + '_sum', stage)
                    if count >= 1 and duration > 0: break
                    time.sleep(.2)
                (self.out / (name + '-metrics-before.txt')).write_text(before)
                (self.out / (name + '-metrics-after.txt')).write_text(after)
                if count != 1 or duration <= 0 or duration > result['ttft_s'] * 1.05 + .05:
                    raise RuntimeError('Invalid native prefill interval')
                result['prefill_tps'] = usage['prompt_tokens'] / duration
            for metric in ('prefill_tps', 'decode_tps', 'ttft_s'):
                if not result.get(metric) or result[metric] <= 0: raise RuntimeError('Missing speed metric: ' + metric)
        self.record(name + '-response', result)
        return result

    def exact_json(self, name, prompt, expected):
        row = self.request(name, [{'role': 'user', 'content': prompt}])
        text = row['answer'].strip()
        if text.startswith('```'): text = '\n'.join(text.splitlines()[1:-1])
        if json.loads(text) != expected: raise RuntimeError('Wrong JSON/arithmetic/retrieval answer')

    def monitor(self):
        from inference_swap_guard import WorkerWatch
        from profile_catalog import worker_budget
        from worker_manager import unit_property, DENSE_UNIT, MOE_UNIT
        unit = DENSE_UNIT if self.p['id'].startswith('qwen27b-') else MOE_UNIT
        watch = None; invocation = None
        with (self.out / 'resources.jsonl').open('a') as log:
            while not self.stop.is_set():
                try:
                    current = unit_property(unit, 'InvocationID')
                    row = {'time': time.time(), 'unit': unit, 'invocation': current}
                    if not current or unit_property(unit,'ActiveState') not in ('active','activating'):
                        self.stop.wait(1); continue  # normal stop/reload interval
                    self.invocations.add(current)
                    group = unit_property(unit, 'ControlGroup'); cg = Path('/sys/fs/cgroup') / group.lstrip('/')
                    if not group.endswith('/' + unit): raise RuntimeError('Wrong worker cgroup')
                    if current != invocation:
                        invocation = current
                        watch = WorkerWatch(cg, self.p['id'], self.key, evidence=self.out / ('guard-' + current + '.jsonl'), latch=False)
                    budget = worker_budget(self.p)
                    for field, value in [('memory.high', budget['high']), ('memory.max', budget['max']), ('memory.swap.max', None)]:
                        expected = 'max' if value is None else str(value * 1024 ** 3)
                        if (cg / field).read_text().strip() != expected: raise RuntimeError('Worker budget differs from selection')
                    row['memory_events'] = check_memory_events((cg / 'memory.events').read_text())
                    row['cgroup'] = {x: (cg / x).read_text() for x in ('memory.current','memory.swap.current','memory.events','memory.stat','memory.pressure')}
                    memory = dict(x.split(':', 1) for x in Path('/proc/meminfo').read_text().splitlines())
                    row['available_kib'] = int(memory['MemAvailable'].split()[0])
                    if row['available_kib'] < self.floor * 1024 ** 2: raise RuntimeError('Host available below selected floor')
                    gpus = subprocess.check_output(['nvidia-smi', '--query-gpu=index,temperature.gpu,memory.free', '--format=csv,noheader,nounits'], text=True, timeout=5)
                    row['gpus'] = [[float(x.strip()) for x in line.split(',')] for line in gpus.splitlines()]
                    if len(row['gpus']) != 2 or any(x[1] >= 82 for x in row['gpus']): raise RuntimeError('GPU inventory/temperature guard')
                    if self.p['id'].startswith('qwen27b-') and any(x[2] < 512 for x in row['gpus']):
                        raise RuntimeError('Dense GPU headroom below 512 MiB')
                    reason = watch.step()
                    if reason: raise RuntimeError(reason)
                    self.samples += 1
                except Exception as error:
                    # A disappearing old invocation is allowed only at an intentional reload;
                    # invalid readings on an active worker never qualify promotion.
                    row = {'time': time.time(), 'error': str(error)}
                    self.errors.append(str(error))
                log.write(json.dumps(row) + '\n'); log.flush(); self.stop.wait(2)

    def retrieval(self):
        context = self.p['allocated_context']; markers = {'start': 'COPPER-8271-ORBIT', 'middle': 'VELVET-4936-HARBOR', 'end': 'QUARTZ-6182-RIVER'}
        def messages(n):
            rng = random.Random(271027); lines = [f'Entry {i:05d}: ' + ' '.join(rng.choice(VOCAB) for _ in range(12)) for i in range(n)]
            for f, key in [(.03, 'start'), (.5, 'middle'), (.97, 'end')]: lines[int(n * f)] = key.upper() + '_MARKER=' + markers[key]
            return [{'role': 'system', 'content': 'Read the archive and copy its marker values exactly. No reasoning.'},
                    {'role': 'user', 'content': '\n'.join(lines) + '\nReturn only JSON keys start, middle, end with their corresponding marker values.'}]
        # Same checkpoint tokenizer for both production and candidate, not a moving
        # model download. Actual backend usage must confirm the allocated window.
        directory = self.root / 'models/engine-tests/qwen38-27b-hyperqwen-fast'
        if self.p['id'].startswith('qwen27b-'):
            code = 'import sys,json; from tokenizers import Tokenizer; d=json.load(sys.stdin); print(len(Tokenizer.from_file(d["path"]).encode(d["text"]).ids)+64)'
            python = self.root / 'runtimes/env-hyperqwen/bin/python'
        else:
            cfg = json.loads((self.root / 'data/router' / (self.p['id'] + '-runtime.json')).read_text())
            directory = Path(cfg['tokenizer'])
            code = 'import sys,json; from tokenizers import Tokenizer; d=json.load(sys.stdin); print(len(Tokenizer.from_file(d["path"]).encode(d["text"]).ids)+64)'
            python = self.root / 'runtimes/env-hyperqwen/bin/python'
        n = max(10, int(context * .9) // 20)
        for _ in range(5):
            msg = messages(n); text = '\n'.join(m['content'] for m in msg)
            if not self.p['id'].startswith('qwen27b-'):
                with self.http('/api/tokens', {'messages':msg,'reasoning_effort':'none','chat_template_kwargs':{'enable_thinking':False}}, timeout=120) as response:
                    count = int(json.load(response)['tokens'])
            else:
                count = int(subprocess.check_output([str(python), '-c', code], input=json.dumps({'path': str(directory / 'tokenizer.json'), 'text': text}), text=True, timeout=120))
            if abs(count - context * .9) < 150: break
            n = max(10, int(n * context * .9 / count))
        row = self.request('retrieval', messages(n)); text = row['answer'].strip()
        if text.startswith('```'): text = '\n'.join(text.splitlines()[1:-1])
        if json.loads(text) != markers: raise RuntimeError('Retrieval marker mismatch')
        actual = row['usage']['prompt_tokens']
        if not .85 * context < actual < context - 128: raise RuntimeError('Retrieval below allocated context')
        if (row['usage'].get('prompt_tokens_details') or {}).get('cached_tokens', 0) > 32:
            raise RuntimeError('Retrieval unexpectedly reused cached tokens')
        return actual

    def stop_owned_idle(self):
        from worker_manager import RouterError
        deadline=time.monotonic()+120
        while True:
            try:
                self.manager.stop_owned(allowed_lock=self.owner); return
            except RouterError as error:
                if error.code not in ('backend_busy','backend_state_unknown','resources_busy') or time.monotonic()>=deadline:
                    raise
                time.sleep(2)

    def run(self):
        thread = threading.Thread(target=self.monitor, daemon=True); thread.start()
        checks = {}
        try:
            self.manager.start(self.p['id'], allowed_lock=self.owner)
            self.request('warmup', self.fixtures[0], 64, speed=True)
            speeds = [self.request('speed-' + str(i), self.fixtures[i + 1], 128, speed=True) for i in range(3)]
            self.exact_json('json', 'Return only JSON keys sum and word with sum=17+25 and word="ready".', {'sum':42,'word':'ready'}); checks['json'] = True
            self.exact_json('arithmetic', 'Return only JSON keys product=19*23 and smallest=min(37,12,29).', {'product':437,'smallest':12}); checks['arithmetic'] = True
            vision = self.p['id'] in ('flash-next-strata','glm-maya','deepseek-maya')
            if vision:
                n = 1024
                def chunk(k, d): return struct.pack('>I',len(d)) + k + d + struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
                png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',n,n,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff\0\0'*n)*n))+chunk(b'IEND',b'')
                row = self.request('image', [{'role':'user','content':[{'type':'text','text':'What is the dominant color? Answer one word.'},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(png).decode()}}]}],32)
                if not re.search(r'\bred\b', row['answer'].lower()): raise RuntimeError('Image answer mismatch')
                checks['image'] = True
            tools = self.p['id'].startswith('qwen27b-')
            if tools:
                tool = [{'type':'function','function':{'name':'add','description':'Add two integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}]
                row = self.request('tool', [{'role':'user','content':'Call add with a=17 and b=25.'}],128,tools=tool)
                if len(row['tool_calls']) != 1 or row['tool_calls'][0]['name'] != 'add' or json.loads(row['tool_calls'][0]['arguments']) != {'a':17,'b':25}: raise RuntimeError('Tool-call mismatch')
                checks['tool'] = True
            count = self.retrieval(); checks['retrieval'] = True
            decode = statistics.median(x['decode_tps'] for x in speeds)
            cap = min(16384, max(128, math.ceil(decode * 120 / 128) * 128))
            row = self.request('sustained', [{'role':'user','content':'Write a very long community-garden handbook: 40 chapters, each at least 400 words of detailed prose. Begin Chapter 1 immediately. No outline, summary or short numbered tips. Continue chapter after chapter until the response limit.'}],cap)
            if row['generation_s'] < 90: raise RuntimeError('Generation ended before 90-second sustained window')
            checks['sustained'] = True
            sustained_s = row['generation_s']
            before = set(self.invocations)
            self.stop.set(); thread.join(timeout=10)
            self.stop_owned_idle()
            self.manager.start(self.p['id'], allowed_lock=self.owner)
            self.stop.clear(); thread = threading.Thread(target=self.monitor, daemon=True); thread.start()
            self.exact_json('reload', 'Return only JSON with key sum=17+25.', {'sum':42}); checks['reload'] = True
            if not self.invocations - before: raise RuntimeError('Reload reused an old worker invocation')
            if self.errors or not self.samples: raise RuntimeError('Resource evidence incomplete: ' + str(self.errors))
            configs = {'profile': self.p}
            if self.p['engine'] in ('Strata','Maya'):
                cfg = json.loads((self.root / 'data/router' / (self.p['id'] + '-runtime.json')).read_text())
                configs['native_settings'] = {k:v for k,v in cfg.items() if k not in ('exe','cwd','lib_dirs','api_key','log')}
            hardware = subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True) + next(x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemTotal:'))
            fingerprint = lambda value: hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
            summary = {'profile': self.p['id'], 'context': self.p['allocated_context'], 'fixture_sha256':fingerprint(self.fixtures),
                'settings_sha256':fingerprint(configs),'hardware_sha256':fingerprint(hardware), 'repetitions':3,
                'prompt_tokens':[x['usage']['prompt_tokens'] for x in speeds],'output_tokens':[x['usage']['completion_tokens'] for x in speeds],
                'prefill_tps':statistics.median(x['prefill_tps'] for x in speeds),'decode_tps':decode,'ttft_s':statistics.median(x['ttft_s'] for x in speeds),
                'vision':vision,'tools':tools,'checks':checks,'retrieval_input_tokens':count,'sustained_generation_s':sustained_s,
                'resources_passed':True,'telemetry_samples':self.samples,'worker_invocations':sorted(self.invocations)}
            self.record('summary',summary); return summary
        finally:
            self.stop.set(); thread.join(timeout=10)
            # The caller handles stop/rollback; save ownership evidence even on failure.
            for invocation in self.invocations:
                text = subprocess.check_output(['journalctl','--user','_SYSTEMD_INVOCATION_ID='+invocation,'--no-pager','-o','cat'],text=True)
                (self.out / ('worker-'+invocation+'.log')).write_text(text.replace(self.key,'[redacted]'))
            self.record('resource-errors', {'errors':self.errors,'samples':self.samples})
