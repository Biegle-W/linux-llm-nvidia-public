"""Fail-closed paired promotion policy, independent of engine deployment."""
import math

CHECKS = ('json', 'arithmetic', 'retrieval', 'sustained', 'reload')


def compare(baseline, candidate):
    reasons = []
    for field in ('profile', 'context', 'fixture_sha256', 'settings_sha256', 'hardware_sha256', 'prompt_tokens', 'output_tokens'):
        if baseline.get(field) is None or baseline.get(field) != candidate.get(field):
            reasons.append('Unmatched ' + field)
    for label, row in [('production', baseline), ('candidate', candidate)]:
        if row.get('repetitions') != 3 or row.get('output_tokens') != [128, 128, 128]:
            reasons.append(label + ': incomplete three-request screen')
        for key in ('prefill_tps', 'decode_tps', 'ttft_s'):
            value = row.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                reasons.append(label + ': invalid ' + key)
        required = CHECKS + (('image',) if row.get('vision') else ()) + (('tool',) if row.get('tools') else ())
        if any(row.get('checks', {}).get(key) is not True for key in required):
            reasons.append(label + ': quality or lifecycle coverage incomplete')
        if row.get('resources_passed') is not True or not row.get('telemetry_samples', 0):
            reasons.append(label + ': missing/failed resource evidence')
        if not .85 * row.get('context', 0) < row.get('retrieval_input_tokens', 0) < row.get('context', 0) - 128:
            reasons.append(label + ': insufficient retrieval coverage')
        if row.get('sustained_generation_s', 0) < 90:
            reasons.append(label + ': insufficient continuous generation')
    if not reasons:
        for key in ('prefill_tps', 'decode_tps'):
            if candidate[key] < .95 * baseline[key]: reasons.append('Regression >5%: ' + key)
        if candidate['ttft_s'] > max(1.25 * baseline['ttft_s'], baseline['ttft_s'] + .05):
            reasons.append('TTFT regression')
    return {'passed': not reasons, 'reasons': reasons}


def compare_short(baseline,candidate):
    """Promote unless the candidate breaks. Owner policy (2026-11-07): always update unless the update breaks
    something; minor speed changes, cache reuse and token-count differences are recorded as warnings only.
    Breaking: invalid comparison identity, failed DSH/lifecycle checks, missing resource evidence, invalid
    metrics, or a severe slowdown (under half the speed, or over three times the TTFT)."""
    reasons=[];warnings=[]
    for field in ('profile','context','settings_sha256','hardware_sha256','fixture_sha256'):
        if baseline.get(field) is None or baseline.get(field)!=candidate.get(field):reasons.append('Unmatched '+field)
    for field in ('prompt_tokens','output_tokens','cached_tokens'):
        if baseline.get(field)!=candidate.get(field):warnings.append('Unmatched '+field)
    for label,row,sink in [('production',baseline,warnings),('candidate',candidate,reasons)]:
        if row.get('qualification')!='short-dsh-v1':sink.append(label+': wrong qualification protocol')
        if any(row.get('checks',{}).get(k)is not True for k in ('tool','tool_result','followup','unload')):
            sink.append(label+': incomplete actual DSH/lifecycle check')
        if row.get('resources_passed')is not True or row.get('telemetry_samples',0)<1:sink.append(label+': missing resource evidence')
        if row.get('cached_tokens')!=0:warnings.append(label+': prompt cache reuse prevents matching')
        for key in ('prefill_tps','decode_tps','ttft_s'):
            value=row.get(key)
            if type(value)not in (int,float)or not math.isfinite(value)or value<=0:sink.append(label+': invalid '+key)
    def valid(row,key):
        value=row.get(key);return type(value)in (int,float)and math.isfinite(value)and value>0
    cached=baseline.get('cached_tokens')!=0 or candidate.get('cached_tokens')!=0
    if cached:warnings.append('Speed not compared: prompt cache reuse')
    for key in ('prefill_tps','decode_tps'):
        if not cached and valid(baseline,key)and valid(candidate,key):
            if candidate[key]<.5*baseline[key]:reasons.append('Severe regression >50%: '+key)
            elif candidate[key]<.95*baseline[key]:warnings.append('Regression >5%: '+key)
    if not cached and valid(baseline,'ttft_s')and valid(candidate,'ttft_s'):
        if candidate['ttft_s']>max(3*baseline['ttft_s'],baseline['ttft_s']+.05):reasons.append('Severe TTFT regression >3x')
        elif candidate['ttft_s']>max(1.25*baseline['ttft_s'],baseline['ttft_s']+.05):warnings.append('TTFT regression')
    return {'passed':not reasons,'reasons':reasons,'warnings':warnings,'scope':'Single matched short DSH tool calls; no sustained/full-context claim'}
