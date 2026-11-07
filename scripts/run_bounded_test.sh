#!/usr/bin/env bash
# Run an experimental worker outside the desktop application's cgroup.
set -euo pipefail
if [[ $# -lt 2 || ! "$1" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
  echo "Usage: $0 TEST-NAME /absolute/command [arguments...]" >&2
  exit 2
fi
name="$1"
shift
if [[ "$1" != /* ]]; then
  echo 'The command must use an absolute path.' >&2
  exit 2
fi
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
swap_limit=1G
ram_high=32G
ram_max=36G
if [[ "$name" == qwen27b && $# -eq 3 && "$1" == /usr/bin/python3 &&
      "$2" == "$root/scripts/supervise_dense.py" &&
      ( "$3" == hyperqwen || "$3" == sglang ) ]]; then
  swap_limit=infinity
  read -r ram_high ram_max < <(/usr/bin/python3 - "$root" "$3" <<'PY'
import sys
sys.path.insert(0,sys.argv[1]+'/scripts')
from profile_catalog import get_profile,worker_budget,budget_limit_string
budget=worker_budget(get_profile('qwen27b-'+sys.argv[2]))
print(budget_limit_string(budget['high']),budget_limit_string(budget['max']))
PY
  )
fi
monitor_args=(--title "LLM: $name" --unit "llm-test-${name}.service")
if [[ "$name" == qwen27b ]]; then
  if [[ "${3:-}" == sglang ]]; then
    monitor_args=(--title "SGLang backend" --unit "llm-test-${name}.service")
  else
    monitor_args=(--title "HyperQwen vLLM backend" --unit "llm-test-${name}.service")
  fi
  monitor_args+=(--log "$root/data/qwen27b-server.log")
fi
if [[ "${NVIDIA_API_ONLY:-0}" != 1 ]]; then
  /usr/bin/python3 "$root/scripts/visible_terminal.py" open "${monitor_args[@]}"
fi
exec systemd-run --user --unit="llm-test-${name}" --collect --service-type=exec \
  --property="MemoryHigh=$ram_high" --property="MemoryMax=$ram_max" \
  --property="MemorySwapMax=$swap_limit" --property=OOMPolicy=kill --setenv="NVIDIA_API_ONLY=${NVIDIA_API_ONLY:-0}" \
  --working-directory="$root" "$@"
