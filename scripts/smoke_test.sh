#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/Crush.skill/execute.py"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python3}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

export CRUSH_DATA_DIR="${CRUSH_DATA_DIR:-/tmp/crush_skill_smoke_data_$$}"

"$PYTHON_BIN" "$SKILL" --action quick_start --session-id demo --config-json '{"archetype":"experience","gender":"female","relationship_stage":"暧昧期"}' >/tmp/crush_quick_start.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id demo --message '你最近忙什么，今天看起来心情还不错' >/tmp/crush_chat_turn.json
"$PYTHON_BIN" "$SKILL" --action postmortem --session-id demo >/tmp/crush_postmortem.json
"$PYTHON_BIN" "$SKILL" --action chat_import --session-id import_demo --source-text $'她: 笑死，地铁老人看手机了属于是\n我: 哈哈哈那周末要不要一起看电影\n她: 看情况吧，别太上头\n她: 我真的会谢，你怎么这么抽象\n我: 那我收一点，慢慢来\n她: 嗯嗯这样还行' >/tmp/crush_chat_import.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id import_demo --message '你猜我今天看到啥了，不是哥们真的抽象' >/tmp/crush_import_chat_turn.json
"$PYTHON_BIN" "$SKILL" --action record_reply --session-id import_demo --message '你猜我今天看到啥了，不是哥们真的抽象' --npc-reply '又开始了是吧，怎么天天这么抽象哈哈' >/tmp/crush_record_reply.json
"$PYTHON_BIN" "$SKILL" --action quick_start --session-id nickname_demo --config-json '{"archetype":"experience","gender":"female","relationship_stage":"暧昧期"}' >/tmp/crush_nickname_start.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id nickname_demo --message '我可以叫你宝宝吗' >/tmp/crush_nickname_1.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id nickname_demo --message '那我以后一直叫你宝宝好不好，可以吗' >/tmp/crush_nickname_2.json
"$PYTHON_BIN" "$SKILL" --action quick_start --session-id symbolic_demo --config-json '{"archetype":"experience","gender":"female","relationship_stage":"暧昧期"}' >/tmp/crush_symbolic_start.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id symbolic_demo --message '那可不是哦 你的名字对于我来说可不能随便是个代号 我叫你camellia吧' >/tmp/crush_symbolic_1.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id symbolic_demo --message '因为camellia直译过来是山茶花，山茶花的花语是理想的爱' >/tmp/crush_symbolic_2.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id symbolic_demo --message '你不拒绝 那我就叫你camellia啦' >/tmp/crush_symbolic_3.json
"$PYTHON_BIN" "$SKILL" --action quick_start --session-id pressure_demo --config-json '{"archetype":"experience","gender":"female","relationship_stage":"暧昧期"}' >/tmp/crush_pressure_start.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id pressure_demo --message '你喜欢我吗' >/tmp/crush_pressure_like.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id pressure_demo --message '真话' >/tmp/crush_pressure_truth.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id pressure_demo --message '因为我不喜欢你' >/tmp/crush_pressure_reject.json
"$PYTHON_BIN" "$SKILL" --action chat_turn --session-id pressure_demo --message '逗逗你玩的' >/tmp/crush_pressure_joke.json
CRUSH_HOME=/tmp/crush_cli_smoke "$PYTHON_BIN" -m crush_cli --plain --session cli_smoke --home /tmp/crush_cli_smoke --data-dir /tmp/crush_cli_smoke/data --message '今天有点想你' >/tmp/crush_cli_smoke.txt
"$PYTHON_BIN" - <<'PY' >/tmp/crush_cli_429.txt
import io
from urllib.error import HTTPError

import crush_cli.app as app


def fake_urlopen(req, timeout=60):
    raise HTTPError(
        req.full_url,
        429,
        "Too Many Requests",
        hdrs=None,
        fp=io.BytesIO(b'{"error":{"message":"mock rate limit"}}'),
    )


app.urlopen = fake_urlopen
client = app.ChatClient({
    "api_key": "dummy",
    "api_base": "https://platform.deepseek.com",
    "model": "deepseek-v4-pro",
})
assert client.api_base == "https://api.deepseek.com", client.api_base
try:
    client.reply("runtime", "hello")
except app.ModelError as exc:
    print(str(exc))
else:
    raise AssertionError("ModelError was not raised")
PY
"$PYTHON_BIN" - <<'PY' >/tmp/crush_cli_proactive.txt
import json
import shutil
from pathlib import Path

import crush_cli.app as app


class FakeResponse:
    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": "刚刚怎么突然安静啦？"}}]
        }).encode()


def fake_urlopen(req, timeout=60):
    return FakeResponse()


home = Path("/tmp/crush_cli_proactive")
if home.exists():
    shutil.rmtree(home)
app.urlopen = fake_urlopen
app.random.random = lambda: 0.0
app.random.uniform = lambda low, high: 1.0
args = app.build_parser().parse_args([
    "--plain",
    "--home",
    str(home),
    "--data-dir",
    str(home / "data"),
    "--session",
    "timeline_demo",
    "--api-key",
    "dummy",
    "--api-base",
    "https://platform.deepseek.com",
    "--model",
    "deepseek-v4-pro",
])
cli = app.CrushCLI(args)
cli.ensure_session()
state = cli.timeline_state()
state["paused"] = False
state["next_proactive_at"] = 0
cli.save_timeline_state(state)
errors = []


def run_from_background_thread():
    try:
        cli.maybe_proactive_message()
    except Exception as exc:
        errors.append(str(exc))


thread = app.threading.Thread(target=run_from_background_thread)
thread.start()
thread.join(timeout=5)
assert not thread.is_alive(), "timeline thread did not finish"
assert not errors, errors
episodes = cli.runtime.memory.sqlite.get_recent_episodes("timeline_demo", limit=5)
assert any(item["role"] == "npc" and "安静" in item["content"] for item in episodes), episodes
print("proactive ok")
PY

"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

imported = json.loads(Path("/tmp/crush_chat_import.json").read_text())
turn = json.loads(Path("/tmp/crush_import_chat_turn.json").read_text())
recorded = json.loads(Path("/tmp/crush_record_reply.json").read_text())
nickname = json.loads(Path("/tmp/crush_nickname_2.json").read_text())
symbolic = json.loads(Path("/tmp/crush_symbolic_3.json").read_text())
like = json.loads(Path("/tmp/crush_pressure_like.json").read_text())
truth = json.loads(Path("/tmp/crush_pressure_truth.json").read_text())
reject = json.loads(Path("/tmp/crush_pressure_reject.json").read_text())
joke = json.loads(Path("/tmp/crush_pressure_joke.json").read_text())
cli_output = Path("/tmp/crush_cli_smoke.txt").read_text()
cli_429_output = Path("/tmp/crush_cli_429.txt").read_text()
cli_proactive_output = Path("/tmp/crush_cli_proactive.txt").read_text()

assert imported["success"], imported
assert turn["success"], turn
assert recorded["success"] and recorded["recorded"], recorded
assert imported["persona"]["expression"]["signature_phrases"], imported["persona"]["expression"]
assert "地铁老人看手机" in imported["analysis"]["slang_hits"], imported["analysis"]
assert turn["analysis"]["slang_hits"], turn["analysis"]
assert turn["agent_contract"]["mode"] == "roleplay_only", turn["agent_contract"]
assert turn["runtime_prompt"].find("本轮潜台词理解") >= 0, turn["runtime_prompt"]
assert nickname["analysis"]["neediness_score"] >= 0.65, nickname["analysis"]
assert nickname["analysis"]["pressure_score"] >= 0.6, nickname["analysis"]
assert "nickname_boundary" in nickname["analysis"]["register_tags"], nickname["analysis"]
assert symbolic["analysis"]["neediness_score"] >= 0.75, symbolic["analysis"]
assert symbolic["analysis"]["pressure_score"] >= 0.7, symbolic["analysis"]
assert "symbolic_naming" in symbolic["analysis"]["register_tags"], symbolic["analysis"]
assert "默认同意规则" in symbolic["runtime_prompt"], symbolic["runtime_prompt"]
assert "最近逐字上下文" in symbolic["runtime_prompt"], symbolic["runtime_prompt"]
assert "direct_validation" in like["analysis"]["register_tags"], like["analysis"]
assert "direct_validation" in truth["analysis"]["register_tags"], truth["analysis"]
assert like["coach"]["line_type"] == "索取确认", like["coach"]
assert like["coach"]["risk_level"] in {"中高", "高"}, like["coach"]
assert "不要直接给满分答案" in like["runtime_prompt"], like["runtime_prompt"]
assert "rejection_tease" in reject["analysis"]["register_tags"], reject["analysis"]
assert reject["coach"]["risk_level"] == "高", reject["coach"]
assert "伤害性" in reject["coach"]["line_type"], reject["coach"]
assert "操控" in reject["coach"]["pressure_note"], reject["coach"]
assert "rejection_tease" in joke["analysis"]["register_tags"], joke["analysis"]
assert "Model not configured" in cli_output, cli_output
assert "HTTP 429" in cli_429_output and "Traceback" not in cli_429_output, cli_429_output
assert "proactive ok" in cli_proactive_output, cli_proactive_output
PY

echo "[smoke-test] quick_start/chat_turn/postmortem/chat_import/pragmatics/nickname/symbolic/pressure/timeline/cli passed"
