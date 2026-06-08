from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from .types import NormalizedMessage


def build_timeline_summary(messages: List[NormalizedMessage]) -> List[Dict[str, Any]]:
    by_day: Dict[str, List[NormalizedMessage]] = defaultdict(list)
    for msg in messages:
        day = msg.time[:10] if msg.time else datetime.fromtimestamp(msg.timestamp).strftime("%Y-%m-%d")
        by_day[day].append(msg)

    result = []
    for day, items in sorted(by_day.items()):
        target_text = " ".join(m.content for m in items if m.speaker == "target")
        trend = infer_trend(target_text)
        result.append(
            {
                "periodStart": day,
                "periodEnd": day,
                "title": f"{day} 的微信互动",
                "summary": summarize_day(items),
                "keyEvents": pick_key_events(items),
                "emotionalTrend": trend,
                "relationshipStage": "未知",
            }
        )
    return result


def summarize_day(items: List[NormalizedMessage]) -> str:
    count = len(items)
    sample = [m.content for m in items if m.content and not m.content.startswith("[")][:3]
    base = "；".join(s[:32] for s in sample) if sample else "以短消息或媒体互动为主"
    return f"当天约 {count} 条消息。从历史对话中只能推测：{base}。"


def pick_key_events(items: List[NormalizedMessage]) -> List[str]:
    events = []
    for msg in items:
        if any(word in msg.content for word in ["喜欢", "吵", "生气", "见面", "下班", "到家", "累"]):
            events.append(f"{'我' if msg.speaker == 'me' else '对方'}：{msg.content[:36]}")
        if len(events) >= 4:
            break
    return events


def infer_trend(text: str) -> str:
    if any(word in text for word in ["生气", "烦", "算了", "不想"]):
        return "冲突/冷淡"
    if any(word in text for word in ["哈哈", "开心", "见面", "想你"]):
        return "升温/轻松"
    return "稳定/未知"

