"""Check advertised dense context against native allocation, not a stress test."""
import re

def sglang_kv_capacity(log):
    values=[int(v) for v in re.findall(r'max_total_num_tokens\s*=\s*(\d+)',log)]
    values += [int(v) for v in re.findall(r'KV Cache is allocated[^\n]*#tokens:\s*(\d+)',log)]
    if not values:
        raise ValueError('Native SGLang KV capacity telemetry is missing')
    return min(values)

def require_sglang_context(context,log):
    capacity=sglang_kv_capacity(log)
    if capacity<context:
        raise ValueError(f'Advertised context {context} exceeds allocated SGLang KV capacity {capacity}')
    return capacity

def require_p2p_transport(log):
    directions={(int(a),int(b)) for a,b in re.findall(r'\b([01])\[\d+\]\s*->\s*([01])\[\d+\][^\n]*via P2P/',log)}
    if not {(0,1),(1,0)} <= directions:
        raise ValueError('Native NCCL logs do not confirm P2P transport in both directions')
    return sorted(directions)

def read_engine_log(path):
    with path.open(errors='replace') as stream:
        return stream.read(2*1024*1024)

def check_p2p_progress(log,phase,now,since=None,allow_lazy=False,grace_s=30):
    try:
        require_p2p_transport(log)
        return True,None,None
    except ValueError as error:
        if allow_lazy:
            traffic=phase=='inference' or bool(re.search(r'Prefill batch|Decode batch|POST /v1/chat/completions',log))
            if since is None and not traffic:
                return False,None,None
            if since is None:
                since=now
            if now-since<grace_s:
                return False,since,None
        return False,since,str(error)
