#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/Crush.skill/execute.py"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python3}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" "$SKILL" --action quick_start --session-id demo --config-json '{"archetype":"experience","gender":"female","relationship_stage":"暧昧期"}' >/tmp/crush_quick_start.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id demo --message '你最近忙什么，今天看起来心情还不错' >/tmp/crush_chat_turn.json
"$PYTHON_BIN" "$SKILL" --action postmortem --session-id demo >/tmp/crush_postmortem.json
"$PYTHON_BIN" "$SKILL" --action chat_import --session-id import_demo --source-text $'她: 笑死，地铁老人看手机了属于是\n我: 哈哈哈那周末要不要一起看电影\n她: 看情况吧，别太上头\n她: 我真的会谢，你怎么这么抽象\n我: 那我收一点，慢慢来\n她: 嗯嗯这样还行' >/tmp/crush_chat_import.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id import_demo --message '你猜我今天看到啥了，不是哥们真的抽象' >/tmp/crush_import_chat_turn.json
"$PYTHON_BIN" "$SKILL" --action record_reply --session-id import_demo --message '你猜我今天看到啥了，不是哥们真的抽象' --npc-reply '又开始了是吧，怎么天天这么抽象哈哈' >/tmp/crush_record_reply.json
CRUSH_HOME=/tmp/crush_cli_smoke "$PYTHON_BIN" -m crush_cli --plain --session cli_smoke --home /tmp/crush_cli_smoke --data-dir /tmp/crush_cli_smoke/data --message '今天有点想你' >/tmp/crush_cli_smoke.txt

"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

imported = json.loads(Path("/tmp/crush_chat_import.json").read_text())
turn = json.loads(Path("/tmp/crush_import_chat_turn.json").read_text())
recorded = json.loads(Path("/tmp/crush_record_reply.json").read_text())
cli_output = Path("/tmp/crush_cli_smoke.txt").read_text()

assert imported["success"], imported
assert turn["success"], turn
assert recorded["success"] and recorded["recorded"], recorded
assert imported["persona"]["expression"]["signature_phrases"], imported["persona"]["expression"]
assert "地铁老人看手机" in imported["analysis"]["slang_hits"], imported["analysis"]
assert turn["analysis"]["slang_hits"], turn["analysis"]
assert turn["agent_contract"]["mode"] == "roleplay_only", turn["agent_contract"]
assert turn["runtime_prompt"].find("本轮潜台词理解") >= 0, turn["runtime_prompt"]
assert "Model not configured" in cli_output, cli_output
PY

echo "[smoke-test] quick_start/chat_turn/postmortem/chat_import/pragmatics/cli passed"
