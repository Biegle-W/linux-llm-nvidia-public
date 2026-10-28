#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
model="${1:-qwen}"
engine="${2:-hyperqwen}"
if [[ $# -gt 2 || ( $# -gt 1 && "$model" != qwen27b ) ]]; then
    echo 'Usage: start_model.sh qwen|qwen27b [hyperqwen|sglang]|strata-deepseek|glm|maya-deepseek' >&2
    exit 2
fi
if [[ "$model" == qwen27b && "$engine" != hyperqwen && "$engine" != sglang ]]; then
    echo 'Dense Qwen engine must be hyperqwen or sglang.' >&2
    exit 2
fi
case "$model" in
    qwen|qwen27b|strata-deepseek|glm|maya-deepseek) ;;
    *) echo 'Usage: start_model.sh qwen|qwen27b|strata-deepseek|glm|maya-deepseek' >&2; exit 2 ;;
esac
# Normal CLI calls use router ownership; only its internal worker path runs preflight below.
case "$model" in
    qwen) route_model="flash-next-strata" ;;
    glm) route_model="glm-maya" ;;
    strata-deepseek) route_model="deepseek-strata" ;;
    maya-deepseek) route_model="deepseek-maya" ;;
    qwen27b) route_model="qwen27b-$engine" ;;
esac
if [[ "$model" != qwen27b || "${LOCAL_LLM_ROUTER_WORKER:-}" != 1 ]]; then
    exec /usr/bin/python3 "$project_dir/scripts/router_client.py" --model "$route_model"
fi
python3 - "$project_dir" "$model" "$engine" <<'PY'
import json, os, socket, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))
from profile_catalog import load_catalog
from storage_policy import verify_storage
selection = [sys.argv[2], sys.argv[3]] if sys.argv[2] == 'qwen27b' else [sys.argv[2]]
selected = next((profile for profile in load_catalog()['profiles'] if profile['launch'] == selection), None)
if selected is None:
    sys.exit('That model/engine has no maintained, qualified quantization profile.')
verify_storage(selected)
pid_file = root / 'data/setup-coordinator.pid'
state_file = root / 'data/model-setup-state.json'
if pid_file.exists() and state_file.exists():
    state = json.loads(state_file.read_text())
    if state.get('stage') not in ('complete', 'failed'):
        try:
            os.kill(int(pid_file.read_text()), 0)
        except ProcessLookupError:
            pass
        else:
            sys.exit('The model setup queue is still running. Check data/model-setup-state.json.')
try:
    with socket.create_connection(('127.0.0.1', 10000), timeout=1):
        sys.exit('Port 10000 is occupied. Stop the current model before starting another.')
except OSError:
    pass
PY
exec "$project_dir/scripts/run_bounded_test.sh" qwen27b /usr/bin/python3 \
    "$project_dir/scripts/supervise_dense.py" "$engine"
