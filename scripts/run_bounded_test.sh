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
if [[ "$name" == qwen27b && $# -eq 3 && "$1" == /usr/bin/python3 &&
      "$2" == "$root/scripts/supervise_dense.py" &&
      ( "$3" == hyperqwen || "$3" == sglang ) ]]; then
  swap_limit=infinity
fi
exec systemd-run --user --unit="llm-test-${name}" --collect --service-type=exec \
  --property=MemoryHigh=30G --property=MemoryMax=36G \
  --property="MemorySwapMax=$swap_limit" --property=OOMPolicy=kill \
  --working-directory="$root" "$@"
