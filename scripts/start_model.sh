#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
model="${1:-qwen}"
case "$model" in
    qwen|qwen27b|strata-deepseek|glm|maya-deepseek) ;;
    *) echo 'Usage: start_model.sh qwen|qwen27b|strata-deepseek|glm|maya-deepseek' >&2; exit 2 ;;
esac
python3 - "$project_dir" <<'PY'
import json, os, socket, sys
from pathlib import Path
root = Path(sys.argv[1])
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
