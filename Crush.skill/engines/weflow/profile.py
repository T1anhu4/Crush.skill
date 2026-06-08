from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple

from .builders import infer_style_tags
from .types import NormalizedMessage


PARTICLES = ["呀", "啦", "嘛", "吧", "呢", "啊", "哦", "嗯", "就", "然后", "其实", "感觉"]
CARE_WORDS = ["休息", "吃饭", "到家", "早点", "别太累", "辛苦", "喝水"]


def build_persona_profile(
    messages: List[NormalizedMessage],
    clusters: List[Dict[str, Any]],
    *,
    session: Dict[str, Any] | None = None,
    media_assets: List[Dict[str, Any]] | None = None,
    privacy_mode: str = "safe",
) -> Tuple[Dict[str, Any], str]:
    session = session or {}
    media_assets = media_assets or []
    target = [m for m in messages if m.speaker == "target"]
    text_target = [m for m in target if m.message_type in {"text", "quote", "link", "unknown"}]
    lengths = [len(strip_media_tokens(m.content)) for m in text_target if strip_media_tokens(m.content)]
    avg_len = round(sum(lengths) / max(1, len(lengths)), 2)
    laugh_counter = Counter()
    ending_counter = Counter()
    particle_counter = Counter()
    emoji_counter = Counter()
    phrase_counter = Counter()
    for msg in text_target:
        text = strip_media_tokens(msg.content)
        if not text:
            continue
        for laugh in re.findall(r"(哈{2,}|h{2,}|笑死|绝了)", text, re.I):
            laugh_counter[laugh] += 1
        if text:
            ending_counter[text[-1:]] += 1
        for particle in PARTICLES:
            if particle in text:
                particle_counter[particle] += 1
        for emoji in re.findall(r"[\U0001F300-\U0001FAFF]|[☀-➿]", text):
            emoji_counter[emoji] += 1
        for phrase in extract_phrases(text):
            phrase_counter[phrase] += 1

    multi_line_ratio = len(clusters) / max(1, len(target))
    sender_names = Counter(m.sender_display_name for m in messages if m.sender_display_name)
    target_media = [asset for asset in media_assets if asset.get("speakerCounts", {}).get("target", 0) > 0]
    profile = {
        "safety": {
            "role": "fictionalized_wechat_companion",
            "source": "full_private_weflow_import" if privacy_mode == "full" else "sanitized_style_samples",
            "must_not_claim_real_person": True,
            "privacy": "local full import; may use names/places/media from private memory" if privacy_mode == "full" else "no real name, wxid, avatar, phone, address, school, company, source XML",
            "privacy_mode": privacy_mode,
        },
        "identity_context": {
            "display_label": session.get("displayLabel") or session.get("displayName") or session.get("remark") or session.get("nickname") or "target",
            "session_type": session.get("type", "私聊"),
            "participants": [name for name, _ in sender_names.most_common(4)],
            "avatar": session.get("avatar", "") if privacy_mode == "full" else "",
        },
        "reply_length": {
            "average_chars": avg_len,
            "common_range": common_range(lengths),
            "short_reply_rate": round(sum(1 for n in lengths if n <= 8) / max(1, len(lengths)), 3),
        },
        "rhythm": {
            "multi_message_ratio": round(multi_line_ratio, 3),
            "usually_sends_multiple": multi_line_ratio > 0.08,
            "max_lines_suggested": 3 if multi_line_ratio > 0.08 else 1,
        },
        "expression": {
            "signature_phrases": [p for p, c in phrase_counter.most_common(12) if c >= 2],
            "particles": [p for p, _ in particle_counter.most_common(8)],
            "laughs": [p for p, _ in laugh_counter.most_common(6)],
            "emoji": [p for p, _ in emoji_counter.most_common(8)],
            "common_endings": [p for p, _ in ending_counter.most_common(8)],
        },
        "media_style": {
            "target_media_count": sum(asset.get("speakerCounts", {}).get("target", 0) for asset in target_media),
            "common_target_media": [
                {
                    "kind": asset.get("kind", "media"),
                    "mediaKey": asset.get("mediaKey", ""),
                    "localPath": asset.get("localPath", ""),
                    "cdnUrl": asset.get("cdnUrl", ""),
                    "targetUses": asset.get("speakerCounts", {}).get("target", 0),
                }
                for asset in target_media[:12]
            ],
        },
        "interaction_patterns": interaction_patterns(messages),
        "generation_rules": [
            "默认像微信短消息，1-3 行。",
            "不要长篇心理分析，不要说根据聊天记录。",
            "可以自然使用口头禅，但不要每次硬塞。",
            "不要声称自己是现实中的任何具体个人。",
        ],
    }
    return profile, render_profile_md(profile)


def extract_phrases(text: str) -> List[str]:
    phrases = []
    for size in (2, 3, 4):
        for i in range(0, max(0, len(text) - size + 1)):
            part = text[i : i + size]
            if re.fullmatch(r"[\u4e00-\u9fff]+", part) and part not in {"我们", "你们", "这个", "那个"}:
                phrases.append(part)
    for token in re.findall(r"[A-Za-z]{2,}|哈{2,}|笑死|绝了", text):
        phrases.append(token)
    return phrases


def strip_media_tokens(text: str) -> str:
    return re.sub(r"\[(表情包|图片|视频|语音|链接|系统提示)(:[^\]]+)?\]", "", text or "").strip()


def common_range(lengths: List[int]) -> str:
    if not lengths:
        return "5-20"
    sorted_lengths = sorted(lengths)
    low = sorted_lengths[int(len(sorted_lengths) * 0.25)]
    high = sorted_lengths[int(len(sorted_lengths) * 0.75)]
    return f"{low}-{high}"


def interaction_patterns(messages: List[NormalizedMessage]) -> Dict[str, Any]:
    patterns: Dict[str, Any] = {}
    for idx, msg in enumerate(messages):
        if msg.speaker != "target":
            continue
        before = " ".join(m.content for m in messages[max(0, idx - 3):idx] if m.speaker == "me")
        label = None
        if any(word in before for word in ["累", "加班", "困", "烦"]):
            label = "user_tired"
        elif any(word in before for word in ["哈哈", "笑死", "逗"]):
            label = "user_joking"
        elif any(word in before for word in ["吃饭", "到家", "下班"]):
            label = "daily_life"
        elif any(word in before for word in ["喜欢", "想你", "叫你"]):
            label = "ambiguous_or_intimate"
        if label:
            bucket = patterns.setdefault(label, {"examples": [], "styleTags": []})
            if len(bucket["examples"]) < 5:
                bucket["examples"].append(msg.content)
            bucket["styleTags"].extend(infer_style_tags(msg.content))
    for value in patterns.values():
        value["styleTags"] = list(dict.fromkeys(value["styleTags"]))[:8]
    return patterns


def render_profile_md(profile: Dict[str, Any]) -> str:
    exp = profile.get("expression", {})
    length = profile.get("reply_length", {})
    rhythm = profile.get("rhythm", {})
    identity = profile.get("identity_context", {})
    media = profile.get("media_style", {})
    common_media = media.get("common_target_media", [])
    return "\n".join(
        [
            "# WeFlow 语言风格卡",
            "",
            f"- 导入模式：{profile.get('safety', {}).get('privacy_mode', 'safe')}",
            f"- 显示对象：{identity.get('display_label', 'target')}",
            f"- 参与者：{', '.join(identity.get('participants', [])[:4]) or '未识别'}",
            f"- 平均回复长度：{length.get('average_chars')} 字",
            f"- 常见长度区间：{length.get('common_range')} 字",
            f"- 连续短句倾向：{'明显' if rhythm.get('usually_sends_multiple') else '一般'}",
            f"- 口头禅：{', '.join(exp.get('signature_phrases', [])[:8]) or '暂无明显重复'}",
            f"- 语气词：{', '.join(exp.get('particles', [])[:8]) or '暂无'}",
            f"- 笑声：{', '.join(exp.get('laughs', [])[:6]) or '暂无'}",
            f"- 表情：{', '.join(exp.get('emoji', [])[:6]) or '暂无'}",
            f"- 媒体/表情包资产：{media.get('target_media_count', 0)} 次对方发送",
            f"- 常用表情包：{', '.join(item.get('mediaKey', '')[:10] for item in common_media[:6]) or '暂无'}",
            "",
            "生成边界：full 模式会使用本地私有姓名/地点/媒体记忆，但仍不能声称自己就是现实本人。",
        ]
    )
