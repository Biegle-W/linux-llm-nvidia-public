#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
model="${1:-qwen}"
engine="${2:-hyperqwen}"
if [[ $# -gt 2 || ( $# -gt 1 && "$model" != qwen27b ) ]]; then
    echo 'Usage: start_model.sh qwen|qwen27b [hyperqwen|sglang|llama]|strata-deepseek|glm|maya-deepseek' >&2
    exit 2
fi
if [[ "$model" == qwen27b && "$engine" != hyperqwen && "$engine" != sglang && "$engine" != llama ]]; then
    echo 'Dense Qwen engine must be hyperqwen, sglang or llama.' >&2
    exit 2
fi
case "$model" in
    qwen|qwen27b|strata-deepseek|glm|maya-deepseek) ;;
    *) echo 'Usage: start_model.sh qwen|qwen27b|strata-deepseek|glm|maya-deepseek' >&2; exit 2 ;;
esac
python3 - "$project_dir" "$model" "$engine" <<'PY'
import json, os, socket, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))
from profile_catalog import load_catalog
selection = [sys.argv[2], sys.argv[3]] if sys.argv[2] == 'qwen27b' else [sys.argv[2]]
if selection not in [profile['launch'] for profile in load_catalog()['profiles']]:
    sys.exit('That model/engine has no maintained, qualified quantization profile.')
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
case "$model" in
    qwen)
        exec "$project_dir/runtimes/bin/strata" launch --preset qwen-flash-next --yes --no-tui ;;
    qwen27b)
        if [[ "$engine" != llama ]]; then
            exec "$project_dir/scripts/run_bounded_test.sh" qwen27b /usr/bin/python3 \
                "$project_dir/scripts/serve_qwen27b_engines.py" "$engine"
        fi
        exec "$project_dir/scripts/run_bounded_test.sh" qwen27b /usr/bin/python3 \
            "$project_dir/scripts/serve_qwen27b.py" ;;
    strata-deepseek)
        exec "$project_dir/runtimes/bin/strata" runtime start --profile deepseek-maya-s --wait 600 ;;
    glm)
        exec "$project_dir/runtimes/project-maya/setup.sh" --config \
            "$project_dir/runtimes/project-maya/maya-maya-s24.json" ;;
    maya-deepseek)
        exec "$project_dir/runtimes/project-maya/setup.sh" --config \
            "$project_dir/runtimes/project-maya/maya-ds4.json" ;;
esac
