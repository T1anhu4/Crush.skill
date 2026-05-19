#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/Crush邂逅.skill/execute.py"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python3}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" "$SKILL" --action quick_start --session-id demo --config-json '{"archetype":"experience","gender":"female","relationship_stage":"暧昧期"}' >/tmp/crush_quick_start.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id demo --message '你最近忙什么，今天看起来心情还不错' >/tmp/crush_chat_turn.json
"$PYTHON_BIN" "$SKILL" --action postmortem --session-id demo >/tmp/crush_postmortem.json

echo "[smoke-test] quick_start/chat_turn/postmortem passed"
