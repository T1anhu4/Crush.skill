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

SAFE_PRIVACY_WARNING = (
    "safe 使用本地规则遮盖常见联系方式和明确标注的姓名、地址、学校、公司，"
    "并移除发送者标识和媒体路径；不能保证完整匿名化。"
    "未标注的身份信息、间接线索和特殊写法仍可能保留，请在分享或发送给模型前检查。"
)


def validate_privacy_mode(privacy_mode: str) -> None:
    if privacy_mode not in ("safe", "full"):
        raise ValueError("privacy_mode 必须为 safe 或 full；full 需要明确选择。")


def stable_hash(text: str, prefix: str = "") -> str:
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{prefix}{digest}" if prefix else digest


def clean_xml_noise(text: str, *, preserve_lines: bool = False) -> str:
    if not text:
        return ""
    text = html.unescape(str(text))
    text = re.sub(r"<(msgsource|appmsg|xml|msg)[\s\S]*?</\1>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^\S\r\n]+" if preserve_lines else r"\s+", " ", text).strip()
    return text


def sanitize_text(text: str, privacy_mode: str = "safe") -> str:
    validate_privacy_mode(privacy_mode)
    text = clean_xml_noise(text, preserve_lines=privacy_mode == "safe")
    if privacy_mode == "full":
        return text.strip()
    text = re.sub(r"wxid_[A-Za-z0-9_\\-]+", "[wxid]", text)
    text = re.sub(r"(?<![0-9])1[3-9][0-9]{9}(?![0-9])", "[手机号]", text)
    text = re.sub(r"https?://\S+", "[链接]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[邮箱]", text)
    # Match explicit identity statements, never arbitrary capitalized words or
    # all Chinese nouns. Keep punctuation, quotes and line boundaries intact.
    value = r"[^.\r\n，。！？；,!?;\[\]：:\"“”‘’]+"
    text = re.sub(
        rf"((?:姓名|真实姓名|名字|学校|公司|单位|地址|住址|\bname|\bschool|\bemployer|\bcompany|\baddress)[:：])[ \t]*(?:\r?\n[ \t]*)?{value}",
        r"\1[已脱敏]", text, flags=re.I,
    )
    text = re.sub(
        r"(我(?:的名字是|名叫|叫))(?!你|他|她|大家|了|外卖|车|人)"
        r"[\u4e00-\u9fff·]{2,8}(?=$|[\s，。！？；,!?;\]\"“”‘’])",
        r"\1[姓名]", text,
    )
    text = re.sub(
        r"((?:我)?住在)([^\r\n，。！？；,!?;\[\]\"“”‘’]{0,50}"
        r"(?:路|街|巷|小区|公寓|号楼|栋|单元)[^\r\n，。！？；,!?;\[\]\"“”‘’]{0,30})",
        r"\1[地址]", text,
    )
    text = re.sub(
        r"(在)([^\s，。！？；,!?;\[\]\"“”‘’]{1,40}?(?:大学|学院|学校|中学|小学))"
        r"(?=上课|读书|上学|学习|就读)", r"\1[学校]", text,
    )
    text = re.sub(
        r"(在)(?!家|这里|那里|外面|路上)([^\s，。！？；,!?;\[\]\"“”‘’]{2,40}?)(?=上班|工作|任职)",
        r"\1[公司]", text,
    )
    text = re.sub(
        r"(\bmy name is[ \t]+)[A-Za-z][A-Za-z '\-]{1,70}(?=$|[.\r\n,!?;\]\"])",
        r"\1[姓名]", text, flags=re.I,
    )
    text = re.sub(
        r"(\bI (?:live at|work (?:at|for)|study at|attend)[ \t]+)"
        r"(?!(?:home|school|the office|the library|a school|a company)(?=[.\r\n,!?;]|$))"
        r"[^.\r\n,!?;\[\]\"]+", r"\1[已脱敏]", text, flags=re.I,
    )
    return re.sub(r"\s+", " ", text).strip()


def sanitize_session(session: Dict[str, Any], privacy_mode: str = "safe") -> Tuple[Dict[str, Any], int, str]:
    validate_privacy_mode(privacy_mode)
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
