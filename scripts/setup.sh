#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENV_ROOT="$ROOT/.venv"
PYTHON=python3.11
while [ "$#" -gt 0 ]; do
  case "$1" in
    --env-root) ENV_ROOT=$2; shift 2 ;;
    --python) PYTHON=$2; shift 2 ;;
    *) echo "Usage: scripts/setup.sh [--env-root PATH] [--python PYTHON3.11]"; exit 2 ;;
  esac
done
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 is required"'
mkdir -p "$ENV_ROOT"
"$PYTHON" -m venv "$ENV_ROOT/inference"
"$PYTHON" -m venv "$ENV_ROOT/alfworld"
"$ENV_ROOT/inference/bin/python" -m pip install -r "$ROOT/requirements/vllm.txt"
"$ENV_ROOT/inference/bin/python" -m pip check
export PATH="$ENV_ROOT/alfworld/bin:$PATH"
"$ENV_ROOT/alfworld/bin/python" -m pip install -r "$ROOT/requirements/alfworld.txt"
"$ENV_ROOT/alfworld/bin/python" "$ROOT/scripts/patch_fast_downward.py"
"$ENV_ROOT/alfworld/bin/python" -m pip check
echo "Inference Python: $ENV_ROOT/inference/bin/python"
echo "ALFWorld Python: $ENV_ROOT/alfworld/bin/python"
