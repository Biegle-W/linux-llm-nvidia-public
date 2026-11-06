#!/usr/bin/env python3
"""Generate deterministic synthetic PLE block fixtures with an independent NumPy oracle.

Retains the real table/hash oracle. Block weights exercise Q2_0/BF16/F16 contracts
without requiring the upstream developer's unpublished model pack or captures.
Never uses the CUDA implementation or its host-reference output as expected data.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

N, HC, NT, K, DIL, EPS = 2560, 4, 2, 4, 3, 1e-6
KEY, SCALES, VALUE = 1017723776, 1024277376, 1025219456

def generate(destination):
    out = Path(destination); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261106)
    def uniform(shape, low, high):
        return rng.uniform(low, high, shape).astype('<f4')
    # Exact representable quantized weights, including all four Q2 codes.
    codes = rng.integers(0, 4, (HC*N, N), dtype=np.uint8)
    scales = uniform((HC*N, N//64), .002, .012).astype('<f2')
    key = ((codes.astype(np.int8)-1) * np.repeat(scales.astype('<f4'),64,axis=1)).astype('<f4')
    packed = np.bitwise_or.reduce(codes.reshape(-1,4).astype(np.uint16) << np.array([0,2,4,6],dtype=np.uint16),axis=1).astype('u1')
    value = uniform((N,N), -.02, .02)
    bits = value.view('<u4'); bits[:] &= np.uint32(0xffff0000)
    norms = [uniform((HC,N), .8, 1.2) for _ in range(3)]
    conv = uniform((HC*N,K), -.03, .03).astype('<f2').astype('<f4')
    emb = uniform((NT,N), -.2, .2)
    hidden = uniform((NT,HC*N), -.3, .3)
    hist = uniform((HC*N,(K-1)*DIL), -.2, .2)
    def norm(x,w):
        x=x.reshape(HC,N)
        # Float32 products; high precision summation then float32, matching the reference contract.
        mean=np.mean(x*x,axis=1,dtype=np.float64).astype('<f4')
        return (x / np.sqrt(mean[:,None] + np.float32(EPS)) * w).astype('<f4')
    outputs=[[] for _ in range(7)]; history=hist.copy()
    for t in range(NT):
        kr=(key.astype(np.float64) @ emb[t].astype(np.float64)).astype('<f4')
        kn=norm(kr,norms[0]); qn=norm(hidden[t],norms[1])
        val=(value.astype(np.float64) @ emb[t].astype(np.float64)).astype('<f4')
        score=np.sum(kn.astype(np.float64)*qn.astype(np.float64),axis=1).astype('<f4')/np.sqrt(np.float32(N))
        gate=(1/(1+np.exp(-np.sign(score)*np.sqrt(np.maximum(np.abs(score),np.float32(1e-6)))))).astype('<f4')
        gated=(gate[:,None]*val[None,:]).astype('<f4'); nm=norm(gated,norms[2]).reshape(-1)
        joined=np.concatenate([history,nm[:,None]],axis=1)
        cv=np.zeros(HC*N,dtype='<f4')
        for tap in range(K): cv += joined[:,tap*DIL]*conv[:,tap]
        cv=(cv/(1+np.exp(-cv))).astype('<f4')
        result=(hidden[t]+gated.reshape(-1)+cv).astype('<f4')
        for dest,x in zip(outputs,[kn,val,gate,gated,nm,cv,result]):dest.append(x.reshape(-1))
        history=joined[:,1:]
    with (out/'dense.bin').open('wb') as f:
        for offset,data in [(KEY,packed),(SCALES,scales),(VALUE,value)]:
            f.seek(offset);f.write(data.tobytes())
    with (out/'ple_in.bin').open('wb') as f:
        f.write(struct.pack('<5if',N,HC,NT,K,DIL,EPS))
        for x in [emb,hidden,key,value,*norms,conv,hist]:f.write(x.astype('<f4').tobytes())
    with (out/'ple_out.bin').open('wb') as f:
        f.write(struct.pack('<3i',N,HC*N,NT))
        for rows in outputs:f.write(np.stack(rows).astype('<f4').tobytes())
    manifest={'schema':1,'seed':20261106,'oracle':'Independent NumPy float64 matrix products and float32 structural operations; synthetic quantized block weights; original real table/hash vectors retained','numpy':np.__version__,'sha256':{name:hashlib.file_digest((out/name).open('rb'),'sha256').hexdigest() for name in ['dense.bin','ple_in.bin','ple_out.bin']}}
    (out/'fixture.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination');generate(p.parse_args().destination)
