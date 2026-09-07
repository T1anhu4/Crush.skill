from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .privacy import (
    SAFE_PRIVACY_WARNING,
    media_placeholder,
    normalize_message_type,
    sanitize_session,
    sanitize_text,
    split_quote,
    stable_hash,
    validate_privacy_mode,
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


def load_weflow_source(source: str | Path | Dict[str, Any]) -> tuple[Dict[str, Any], str, Path | None]:
    base_dir: Path | None = None
    if isinstance(source, dict):
        raw = json.dumps(source, ensure_ascii=False, sort_keys=True)
        data = source
    else:
        source_text = str(source)
        if source_text.lstrip().startswith("{"):
            raw = source_text
        else:
            path = Path(source_text).expanduser()
            if path.exists():
                base_dir = path.parent
                raw = path.read_text(encoding="utf-8")
            else:
                raw = source_text
        data = json.loads(raw)
    if not detect_weflow_format(data):
        raise ValueError("不是有效的 WeFlow JSON：必须包含 weflow、session 和非空 messages 数组。")
    if not data.get("messages"):
        raise ValueError("WeFlow JSON 格式正确，但 messages 为空。")
    return data, raw, base_dir


def _resolve_relative_media(value: str, base_dir: Path | None) -> str:
    if not value or not base_dir:
        return value
    if value.startswith(("http://", "https://", "/")):
        return value
    candidate = (base_dir / value).resolve()
    return str(candidate) if candidate.exists() else value


def _local_emoji_path(md5: str, base_dir: Path | None) -> str:
    if not md5 or not base_dir:
        return ""
    roots = [base_dir / "../emojis", base_dir / "emojis", base_dir.parent / "emojis"]
    for root in roots:
        root = root.resolve()
        if not root.exists():
            continue
        for ext in (".gif", ".png", ".jpg", ".jpeg", ".webp"):
            candidate = root / f"{md5}{ext}"
            if candidate.exists():
                return str(candidate)
    return ""


def extract_media(row: Dict[str, Any], msg_type: str, base_dir: Path | None, privacy_mode: str) -> Dict[str, Any]:
    validate_privacy_mode(privacy_mode)
    if privacy_mode == "safe":
        return {}
    media: Dict[str, Any] = {}
    content = str(row.get("content") or "")
    if msg_type == "emoji":
        md5 = str(row.get("emojiMd5") or "")
        media = {
            "kind": "emoji",
            "id": md5 or f"emoji_{row.get('localId', '')}",
            "md5": md5,
            "localPath": _local_emoji_path(md5, base_dir),
            "cdnUrl": str(row.get("emojiCdnUrl") or "") if privacy_mode == "full" else "",
        }
    elif msg_type in {"image", "video", "voice"}:
        media = {
            "kind": msg_type,
            "id": Path(content).name or f"{msg_type}_{row.get('localId', '')}",
            "localPath": _resolve_relative_media(content, base_dir),
            "cdnUrl": "",
        }
    return {k: v for k, v in media.items() if v not in {"", None}}


def media_content_label(msg_type: str, media: Dict[str, Any], privacy_mode: str) -> str:
    placeholder = media_placeholder(msg_type)
    if privacy_mode != "full" or not media:
        return placeholder
    ident = media.get("md5") or media.get("id") or media.get("localPath") or msg_type
    if msg_type == "emoji":
        return f"[表情包:{ident}]"
    if msg_type == "image":
        return f"[图片:{Path(str(ident)).name}]"
    if msg_type == "video":
        return f"[视频:{Path(str(ident)).name}]"
    if msg_type == "voice":
        return f"[语音:{Path(str(ident)).name}]"
    return placeholder


def normalize_weflow_messages(data: Dict[str, Any], import_id: str, *, privacy_mode: str = "safe", base_dir: Path | None = None) -> tuple[List[NormalizedMessage], Dict[str, int]]:
    validate_privacy_mode(privacy_mode)
    messages = []
    stats = {"raw": len(data.get("messages", [])), "me": 0, "target": 0, "media_or_system": 0, "redacted": 0, "emoji": 0, "image": 0, "video": 0, "voice": 0}
    seen = set()
    sorted_rows = sorted(
        data.get("messages", []),
        key=lambda item: (int(item.get("createTime") or 0), int(item.get("localId") or 0)),
    )
    for row in sorted_rows:
        speaker = "me" if int(row.get("isSend") or 0) == 1 else "target"
        msg_type = normalize_message_type(row.get("type", ""), row.get("localType"))
        media = extract_media(row, msg_type, base_dir, privacy_mode)
        content = sanitize_text(row.get("content", ""), privacy_mode=privacy_mode)
        placeholder = media_placeholder(msg_type)
        if placeholder and (not content or msg_type != "text"):
            content = media_content_label(msg_type, media, privacy_mode)
            stats["media_or_system"] += 1
            if msg_type in stats:
                stats[msg_type] += 1
        if not content:
            continue
        if privacy_mode != "full" and any(key in str(row.get(key, "")) for key in ("wxid", "avatar", "source", "platformMessageId")):
            stats["redacted"] += 1
        reply, quoted, quoted_speaker = split_quote(content, speaker, privacy_mode=privacy_mode)
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
                sender_display_name=str(row.get("senderDisplayName") or "") if privacy_mode == "full" else "",
                sender_username=str(row.get("senderUsername") or "") if privacy_mode == "full" else "",
                media=media,
            )
        )
    return messages, stats


def parse_weflow_export(source: str | Path | Dict[str, Any], *, privacy_mode: str = "safe") -> Dict[str, Any]:
    validate_privacy_mode(privacy_mode)
    data, raw, base_dir = load_weflow_source(source)
    file_hash = stable_hash(raw, "file_")
    import_id = stable_hash(file_hash + "|" + str(data.get("session", {}).get("lastTimestamp", "")), "wf_")
    safe_session, redacted_session, session_hash = sanitize_session(data.get("session", {}), privacy_mode=privacy_mode)
    messages, stats = normalize_weflow_messages(data, import_id, privacy_mode=privacy_mode, base_dir=base_dir)
    stats["redacted"] += redacted_session
    stats["privacy_mode"] = privacy_mode
    stats["privacy_warning"] = SAFE_PRIVACY_WARNING if privacy_mode == "safe" else "full 保留原始身份信息和媒体路径，仅适用于用户明确选择的私有导入。"
    if not messages:
        raise ValueError("WeFlow JSON 中没有可用消息：文本为空或全部被过滤。")
    return {
        "import_id": import_id,
        "file_hash": file_hash,
        "session_hash": session_hash,
        "session": safe_session,
        "messages": messages,
        "stats": stats,
        "base_dir": str(base_dir) if base_dir else "",
    }
