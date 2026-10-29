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
