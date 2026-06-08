from __future__ import annotations

import hashlib
import html
import re
from typing import Any, Dict, Tuple


PRIVATE_SESSION_KEYS = {
    "wxid",
    "avatar",
    "senderAvatarKey",
    "emojiCdnUrl",
    "source",
    "platformMessageId",
}


def stable_hash(text: str, prefix: str = "") -> str:
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{prefix}{digest}" if prefix else digest


def clean_xml_noise(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(str(text))
    text = re.sub(r"<(msgsource|appmsg|xml|msg)[\s\S]*?</\1>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sanitize_text(text: str, privacy_mode: str = "safe") -> str:
    text = clean_xml_noise(text)
    if privacy_mode == "full":
        return text.strip()
    text = re.sub(r"wxid_[A-Za-z0-9_\\-]+", "[wxid]", text)
    text = re.sub(r"\b1[3-9]\d{9}\b", "[手机号]", text)
    text = re.sub(r"https?://\S+", "[链接]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[邮箱]", text)
    text = re.sub(r"(学校|公司|地址|住址)[:：]\s*\S+", r"\1：[已脱敏]", text)
    return text.strip()


def sanitize_session(session: Dict[str, Any], privacy_mode: str = "safe") -> Tuple[Dict[str, Any], int, str]:
    raw = dict(session or {})
    redacted_count = sum(1 for key in PRIVATE_SESSION_KEYS if raw.get(key))
    session_hash = stable_hash("|".join(str(raw.get(k, "")) for k in ("wxid", "nickname", "remark", "displayName")), "sess_")
    if privacy_mode == "full":
        safe = dict(raw)
        safe["sessionHash"] = session_hash
        safe["displayLabel"] = raw.get("displayName") or raw.get("remark") or raw.get("nickname") or "target"
        return safe, 0, session_hash
    safe = {
        "type": raw.get("type", "私聊"),
        "messageCount": raw.get("messageCount", 0),
        "lastTimestamp": raw.get("lastTimestamp", 0),
        "displayLabel": "target",
        "sessionHash": session_hash,
    }
    return safe, redacted_count, session_hash


def normalize_message_type(raw_type: str, local_type: Any = None) -> str:
    raw = str(raw_type or "")
    if "引用" in raw:
        return "quote"
    if "文本" in raw:
        return "text"
    if "动画表情" in raw or "表情" in raw:
        return "emoji"
    if "图片" in raw:
        return "image"
    if "语音" in raw:
        return "voice"
    if "视频" in raw:
        return "video"
    if "链接" in raw or "分享" in raw:
        return "link"
    if "系统" in raw or local_type in {10000, "10000"}:
        return "system"
    return "unknown"


def media_placeholder(message_type: str) -> str:
    return {
        "emoji": "[表情包]",
        "image": "[图片]",
        "voice": "[语音]",
        "video": "[视频]",
        "link": "[链接]",
        "system": "[系统提示]",
    }.get(message_type, "")


def split_quote(content: str, current_speaker: str, privacy_mode: str = "safe") -> Tuple[str, str | None, str | None]:
    text = sanitize_text(content, privacy_mode=privacy_mode)
    # WeFlow often serializes quotes as: 回复文本[引用 Nick：quoted text]
    m = re.search(r"\[引用\s*([^：:\]]*)[：:]\s*([\s\S]*?)\]\s*$", text)
    if not m:
        return text, None, None
    reply = text[: m.start()].strip()
    quoted = sanitize_text(m.group(2).strip(), privacy_mode=privacy_mode)
    quoted_speaker = "me" if current_speaker == "target" else "target"
    return reply or "[引用回复]", quoted or None, quoted_speaker
