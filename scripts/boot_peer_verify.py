#!/usr/bin/env python3
"""Root-owned boot proof: bounded seeded peer correctness, not a model benchmark."""
from pathlib import Path
import json,os,subprocess,time
assert os.geteuid()==0
out=Path('/run/local-llm-p2p');out.mkdir(mode=0o755,exist_ok=True);report=out/'verified.json';report.unlink(missing_ok=True)
# The service runs before the display manager, after exact pair unlock/ACS checks.
env={'PATH':'/usr/bin:/bin','CUDA_DEVICE_ORDER':'PCI_BUS_ID','CUDA_VISIBLE_DEVICES':'0,1'}
run=subprocess.run(['/usr/local/libexec/local-llm-verify-p2p'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=55)
print(run.stdout,flush=True)
row={'passed':run.returncode==0 and 'PASS: both directions verified' in run.stdout,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'nvidia_srcversion':Path('/sys/module/nvidia/srcversion').read_text().strip(),'checked_at':time.time(),'scope':'16 MiB seeded remote read/write; both directions; three patterns','output':run.stdout}
tmp=out/'verified.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.chmod(0o644);tmp.replace(report)
raise SystemExit(0 if row['passed'] else 1)
