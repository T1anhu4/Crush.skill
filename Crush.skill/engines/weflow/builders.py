from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List

from .types import NormalizedMessage


def role_label(speaker: str) -> str:
    return "我" if speaker == "me" else "对方"


def infer_style_tags(text: str) -> List[str]:
    tags: List[str] = []
    length = len(text)
    if length <= 6:
        tags.append("极短")
    elif length <= 18:
        tags.append("短句")
    else:
        tags.append("中长句")
    if re.search(r"哈|笑死|hhh|233", text, re.I):
        tags.append("哈哈哈")
    if any(word in text for word in ["休息", "吃饭", "到家", "早点", "别太累", "辛苦"]):
        tags.append("关心")
    if any(word in text for word in ["嗯", "哦", "行吧", "好吧", "随便"]):
        tags.append("冷淡/保留")
    if "[表情包]" in text:
        tags.append("表情包")
    if not tags:
        tags.append("自然")
    return list(dict.fromkeys(tags))


def infer_emotion(text: str) -> str:
    if any(word in text for word in ["休息", "辛苦", "早点", "别太累"]):
        return "轻松关心"
    if re.search(r"哈|笑死|绝了|hhh", text, re.I):
        return "轻松玩笑"
    if any(word in text for word in ["嗯", "哦", "行吧", "好吧"]):
        return "克制保留"
    return "自然日常"


def build_dialogue_chunks(messages: List[NormalizedMessage], max_messages: int = 26) -> List[Dict[str, Any]]:
    chunks: List[List[NormalizedMessage]] = []
    current: List[NormalizedMessage] = []
    previous_ts = 0
    for msg in messages:
        gap = msg.timestamp - previous_ts if previous_ts else 0
        if current and (gap > 1800 or len(current) >= max_messages):
            chunks.append(current)
            current = []
        current.append(msg)
        previous_ts = msg.timestamp
    if current:
        chunks.append(current)

    result = []
    for idx, chunk in enumerate(chunks, start=1):
        text = "\n".join(f"{role_label(m.speaker)}：{m.content}" for m in chunk)
        target_text = " ".join(m.content for m in chunk if m.speaker == "target")
        tags = infer_style_tags(target_text or text)[:4]
        result.append(
            {
                "chunkId": f"chunk_{idx}",
                "startTime": chunk[0].time or str(chunk[0].timestamp),
                "endTime": chunk[-1].time or str(chunk[-1].timestamp),
                "messageCount": len(chunk),
                "text": text,
                "summary": summarize_chunk(chunk),
                "tags": tags,
                "emotionalTone": infer_emotion(target_text or text),
                "relationshipStage": "unknown",
            }
        )
    return result


def summarize_chunk(chunk: List[NormalizedMessage]) -> str:
    sample = [m.content for m in chunk if m.content and not m.content.startswith("[")][:4]
    if not sample:
        return "一段以媒体或短回应为主的微信互动。"
    return " / ".join(s[:28] for s in sample)


def build_target_reply_examples(messages: List[NormalizedMessage], max_context: int = 6) -> List[Dict[str, Any]]:
    examples = []
    for idx, msg in enumerate(messages):
        if msg.speaker != "target":
            continue
        context = messages[max(0, idx - max_context):idx]
        if not context:
            continue
        context_text = "\n".join(f"{role_label(m.speaker)}：{m.content}" for m in context)
        tags = infer_style_tags(msg.content)
        weight = 0.45 if len(msg.content) <= 2 else 0.75 if len(msg.content) <= 6 else 1.0
        examples.append(
            {
                "exampleId": f"reply_{len(examples) + 1}",
                "contextText": context_text,
                "targetReply": msg.content,
                "styleTags": tags,
                "emotion": infer_emotion(msg.content),
                "replyLength": len(msg.content),
                "replyPattern": "短句关心" if "关心" in tags else "连续微信感短答" if len(msg.content) <= 8 else "自然回应",
                "embeddingText": f"上下文：{context_text}\n对方回复：{msg.content}\n风格：{'、'.join(tags)}",
                "weight": weight,
                "time": msg.time,
            }
        )
    return examples


def build_target_reply_clusters(messages: List[NormalizedMessage], max_gap_seconds: int = 180) -> List[Dict[str, Any]]:
    clusters = []
    idx = 0
    while idx < len(messages):
        msg = messages[idx]
        if msg.speaker != "target":
            idx += 1
            continue
        run = [msg]
        j = idx + 1
        while j < len(messages) and messages[j].speaker == "target":
            if messages[j].timestamp - run[-1].timestamp > max_gap_seconds:
                break
            if len(run) >= 5:
                break
            run.append(messages[j])
            j += 1
        if len(run) >= 2:
            context = messages[max(0, idx - 6):idx]
            context_text = "\n".join(f"{role_label(m.speaker)}：{m.content}" for m in context)
            replies = [m.content for m in run]
            combined = "\n".join(replies)
            tags = infer_style_tags(combined)
            tags.insert(0, "连续短句")
            clusters.append(
                {
                    "clusterId": f"cluster_{len(clusters) + 1}",
                    "contextText": context_text,
                    "targetReplies": replies,
                    "combinedReply": combined,
                    "styleTags": list(dict.fromkeys(tags)),
                    "emotion": infer_emotion(combined),
                    "replyPattern": "连续短句回应",
                    "embeddingText": f"上下文：{context_text}\n连续回复：{combined}\n风格：{'、'.join(tags)}",
                    "weight": 0.9 if len(combined) > 6 else 0.55,
                    "time": run[0].time,
                }
            )
        idx = max(j, idx + 1)
    return clusters


def count_days(messages: Iterable[NormalizedMessage]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for msg in messages:
        day = msg.time[:10] if msg.time else datetime.fromtimestamp(msg.timestamp).strftime("%Y-%m-%d")
        counter[day] += 1
    return dict(counter)

