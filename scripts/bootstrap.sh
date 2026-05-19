#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"

python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r "$ROOT/requirements.txt"

if [[ "${WITH_MEM0:-0}" == "1" ]]; then
  python3 -m pip install -r "$ROOT/requirements-mem0.txt"
  echo "[bootstrap] mem0 optional dependencies installed"
fi

echo "[bootstrap] done"
echo "activate env: source $VENV/bin/activate"
echo "run smoke test: bash $ROOT/scripts/smoke_test.sh"
