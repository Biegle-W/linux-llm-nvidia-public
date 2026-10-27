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
exec systemd-run --user --unit="llm-test-${name}" --collect --service-type=exec \
  --property=MemoryHigh=30G --property=MemoryMax=36G \
  --property=MemorySwapMax=1G --property=OOMPolicy=kill \
  --working-directory="$root" "$@"
