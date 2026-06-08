#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "Crush.skill"
sys.path.insert(0, str(SKILL))


def sample() -> dict:
    return {
        "weflow": {"version": "1.0.3", "generator": "WeFlow"},
        "session": {"wxid": "wxid_secret", "nickname": "Real Name", "avatar": "http://avatar", "type": "私聊", "messageCount": 8},
        "messages": [
            {"localId": 1, "createTime": 1772180982, "formattedTime": "2026-02-27 16:29:42", "type": "文本消息", "content": "敲了一下午代码，终于能摸会儿鱼了", "isSend": 1, "source": "<msgsource>wxid_xxx</msgsource>"},
            {"localId": 2, "createTime": 1772181000, "formattedTime": "2026-02-27 16:30:00", "type": "引用消息", "content": "好好休息下[引用 Successfully.：敲了一下午代码，终于能摸会儿鱼了]", "isSend": 0},
            {"localId": 3, "createTime": 1772181010, "formattedTime": "2026-02-27 16:30:10", "type": "文本消息", "content": "没有没有", "isSend": 0},
            {"localId": 4, "createTime": 1772181020, "formattedTime": "2026-02-27 16:30:20", "type": "文本消息", "content": "已经美美躺在床上", "isSend": 0},
            {"localId": 5, "createTime": 1772181030, "formattedTime": "2026-02-27 16:30:30", "type": "文本消息", "content": "哈哈哈哈哈哈哈", "isSend": 0},
            {"localId": 6, "createTime": 1772181060, "formattedTime": "2026-02-27 16:31:00", "type": "动画表情", "content": "", "isSend": 0},
            {"localId": 7, "createTime": 1772181200, "formattedTime": "2026-02-27 16:33:20", "type": "文本消息", "content": "你下午那个会顺利结束了吧哈哈哈哈", "isSend": 1},
            {"localId": 8, "createTime": 1772181300, "formattedTime": "2026-02-27 16:35:00", "type": "文本消息", "content": "笑死 结束了", "isSend": 0},
        ],
    }


def main() -> int:
    data_dir = Path(tempfile.mkdtemp(prefix="crush_weflow_smoke_"))
    try:
        os.environ["CRUSH_DATA_DIR"] = str(data_dir)
        from execute import CrushSkillRuntime  # noqa: E402

        runtime = CrushSkillRuntime()
        source = json.dumps(sample(), ensure_ascii=False)
        result = runtime.run("weflow_import", "default", {"source_text": source})
        assert result["success"]
        assert result["stats"]["me"] == 2
        assert result["stats"]["target"] == 6
        assert result["stats"]["target_reply_examples"] >= 5
        assert result["stats"]["target_reply_clusters"] >= 1
        again = runtime.run("weflow_import", "default", {"source_text": source})
        assert again["already_imported"] is True
        other = runtime.run("weflow_import", "weixin", {"source_text": source})
        assert other["success"]
        assert other["already_imported"] is False
        assert other["import_id"] != result["import_id"]
        other_again = runtime.run("weflow_import", "weixin", {"source_text": source})
        assert other_again["already_imported"] is True
        assert other_again["import_id"] == other["import_id"]
        turn = runtime.run("chat_turn", "default", {"message": "今天写代码好累啊", "mode": "companion"})
        prompt = turn["runtime_prompt"]
        assert "虚构化微信聊天陪伴角色" in prompt
        assert "相似回应样本" in prompt
        assert "连续回复样本" in prompt
        assert not any(secret in prompt for secret in ["wxid_secret", "http://avatar", "msgsource"])
        proactive = runtime.run("proactive_prompt", "default", {"event": "晚上下班后低打扰问候"})
        assert "主动给用户发" in proactive["runtime_prompt"]
        print("weflow smoke ok")
        return 0
    finally:
        shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
