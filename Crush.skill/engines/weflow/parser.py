from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .privacy import (
    media_placeholder,
    normalize_message_type,
    sanitize_session,
    sanitize_text,
    split_quote,
    stable_hash,
)
from .types import NormalizedMessage


def detect_weflow_format(data: Any) -> bool:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return False
    return (
        isinstance(data, dict)
        and isinstance(data.get("weflow"), dict)
        and isinstance(data.get("session"), dict)
        and isinstance(data.get("messages"), list)
    )


def load_weflow_source(source: str | Path | Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    if isinstance(source, dict):
        raw = json.dumps(source, ensure_ascii=False, sort_keys=True)
        data = source
    else:
        source_text = str(source)
        if source_text.lstrip().startswith("{"):
            raw = source_text
        else:
            path = Path(source_text).expanduser()
            raw = path.read_text(encoding="utf-8") if path.exists() else source_text
        data = json.loads(raw)
    if not detect_weflow_format(data):
        raise ValueError("不是有效的 WeFlow JSON：必须包含 weflow、session 和非空 messages 数组。")
    if not data.get("messages"):
        raise ValueError("WeFlow JSON 格式正确，但 messages 为空。")
    return data, raw


def normalize_weflow_messages(data: Dict[str, Any], import_id: str) -> tuple[List[NormalizedMessage], Dict[str, int]]:
    messages = []
    stats = {"raw": len(data.get("messages", [])), "me": 0, "target": 0, "media_or_system": 0, "redacted": 0}
    seen = set()
    sorted_rows = sorted(
        data.get("messages", []),
        key=lambda item: (int(item.get("createTime") or 0), int(item.get("localId") or 0)),
    )
    for row in sorted_rows:
        speaker = "me" if int(row.get("isSend") or 0) == 1 else "target"
        msg_type = normalize_message_type(row.get("type", ""), row.get("localType"))
        content = sanitize_text(row.get("content", ""))
        placeholder = media_placeholder(msg_type)
        if placeholder and (not content or msg_type != "text"):
            content = placeholder
            stats["media_or_system"] += 1
        if not content:
            continue
        if any(key in str(row.get(key, "")) for key in ("wxid", "avatar", "source", "platformMessageId")):
            stats["redacted"] += 1
        reply, quoted, quoted_speaker = split_quote(content, speaker)
        timestamp = int(row.get("createTime") or 0)
        time_text = str(row.get("formattedTime") or "")
        source_local_id = row.get("localId")
        hash_seed = f"{source_local_id}|{timestamp}|{speaker}|{reply}|{quoted or ''}"
        content_hash = stable_hash(hash_seed, "msg_")
        if content_hash in seen:
            continue
        seen.add(content_hash)
        stats[speaker] += 1
        messages.append(
            NormalizedMessage(
                id=f"{import_id}_{len(messages) + 1}",
                import_id=import_id,
                timestamp=timestamp,
                time=time_text,
                speaker=speaker,
                message_type=msg_type,
                content=reply,
                quoted_content=quoted,
                quoted_speaker=quoted_speaker,
                raw_type=str(row.get("type", "")),
                source_local_id=source_local_id,
                content_hash=content_hash,
            )
        )
    return messages, stats


def parse_weflow_export(source: str | Path | Dict[str, Any]) -> Dict[str, Any]:
    data, raw = load_weflow_source(source)
    file_hash = stable_hash(raw, "file_")
    import_id = stable_hash(file_hash + "|" + str(data.get("session", {}).get("lastTimestamp", "")), "wf_")
    safe_session, redacted_session, session_hash = sanitize_session(data.get("session", {}))
    messages, stats = normalize_weflow_messages(data, import_id)
    stats["redacted"] += redacted_session
    if not messages:
        raise ValueError("WeFlow JSON 中没有可用消息：文本为空或全部被过滤。")
    return {
        "import_id": import_id,
        "file_hash": file_hash,
        "session_hash": session_hash,
        "session": safe_session,
        "messages": messages,
        "stats": stats,
    }
