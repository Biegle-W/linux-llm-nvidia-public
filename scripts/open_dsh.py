#!/usr/bin/env python3
"""Open the existing DSH instance using its private startup URL."""
from pathlib import Path
import re
import subprocess
import time
ROOT = Path(__file__).resolve().parents[1]
subprocess.run(['systemctl', '--user', 'start', 'nvidia-dsh.service'], check=True)
for _ in range(60):
    path = ROOT / 'data/dsh-web.log'
    if path.exists():
        urls = re.findall(r'https?://127\.0\.0\.1:3080/[^\s\x1b]*', path.read_text(errors='replace'))
        if urls:
            subprocess.Popen(['xdg-open', urls[-1]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise SystemExit(0)
    time.sleep(1)
raise SystemExit('DSH is not ready; inspect nvidia-dsh.service.')
