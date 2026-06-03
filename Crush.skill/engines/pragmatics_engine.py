from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class PragmaticSignal:
    surface_intent: str = "普通聊天"
    subtext: str = "没有明显潜台词"
    deep_need: str = "保持自然互动"
    emotional_state: str = "neutral"
    test_flag: bool = False
    test_type: str | None = None
    reply_strategy: str = "自然接话，不解释，不上价值"
    register_tags: list[str] = field(default_factory=list)
    slang_hits: list[str] = field(default_factory=list)
    implied_boundary: str = ""
    confidence: float = 0.35

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


SLANG_LEXICON: list[tuple[str, Dict[str, Any]]] = [
    ("地铁老人看手机", {
        "subtext": "对方觉得这句话/行为尴尬、土、难以评价，但多半带调侃感",
        "emotional_state": "playful",
        "reply_strategy": "接住自嘲，别认真解释；可以顺着说自己确实有点土",
        "tags": ["meme", "teasing", "awkward"],
    }),
    ("我真的会谢", {
        "subtext": "轻度崩溃式吐槽，不一定是真的生气",
        "emotional_state": "playful",
        "reply_strategy": "用轻松语气接住，不要道歉过度",
        "tags": ["slang", "mock_complaint"],
    }),
    ("抽象", {
        "subtext": "对方觉得内容离谱、跳脱、难以按常规理解",
        "emotional_state": "playful",
        "reply_strategy": "别解释逻辑；用短句承认离谱并回到轻松互动",
        "tags": ["slang", "absurd"],
    }),
    ("不是哥们", {
        "subtext": "熟人式吐槽开场，通常是轻度嫌弃或震惊",
        "emotional_state": "playful",
        "reply_strategy": "按熟人吐槽接，不要显得被冒犯",
        "tags": ["slang", "teasing"],
    }),
    ("上头", {
        "subtext": "关系投入过快、情绪浓度偏高，可能让对方感到压力",
        "emotional_state": "guarded",
        "reply_strategy": "降温，承认有点投入，但不要索取承诺",
        "tags": ["boundary", "neediness"],
    }),
    ("看情况", {
        "subtext": "软性拒绝或保留选项，不是明确答应",
        "emotional_state": "guarded",
        "reply_strategy": "给空间，轻轻收住，不继续追问",
        "tags": ["soft_decline", "boundary"],
    }),
    ("再说吧", {
        "subtext": "软性回避，当前推进欲望不高",
        "emotional_state": "guarded",
        "reply_strategy": "停止推进，换成低压力话题",
        "tags": ["soft_decline", "avoidance"],
    }),
    ("别太认真", {
        "subtext": "对方在提醒关系节奏过快或情绪浓度过高",
        "emotional_state": "guarded",
        "reply_strategy": "把节奏放轻，不要证明真心",
        "tags": ["boundary", "pace"],
    }),
    ("你猜", {
        "subtext": "轻度测试/撒娇/保持悬念，取决于上下文",
        "emotional_state": "playful",
        "reply_strategy": "轻松猜，不要审问；给一个有趣但不油的回答",
        "tags": ["test", "playful"],
        "test_type": "investment_test",
    }),
    ("随便", {
        "subtext": "可能是低能量、失望或不想继续争论",
        "emotional_state": "cold",
        "reply_strategy": "先降低对抗，不逼对方给真实答案",
        "tags": ["cold", "avoidance"],
    }),
]


TEST_PATTERNS: list[tuple[str, str, str]] = [
    (r"你是不是.*(对谁都|跟谁都|经常)", "character_test", "对方在测试你的边界、稳定性或真诚度"),
    (r"(你会不会|你是不是).*离开", "attachment_test", "对方在确认安全感"),
    (r"(如果|那你).*怎么办", "investment_test", "对方在测试投入意愿"),
    (r"(前任|别人|她们|他们).*", "jealousy_test", "对方可能在触发比较或嫉妒测试"),
]


def interpret_message(message: str) -> PragmaticSignal:
    text = message.strip()
    if not text:
        return PragmaticSignal()

    hits: List[str] = []
    tags: List[str] = []
    subtexts: List[str] = []
    strategies: List[str] = []
    emotional_states: List[str] = []
    test_type: str | None = None

    for phrase, meta in SLANG_LEXICON:
        if phrase in text:
            hits.append(phrase)
            tags.extend(meta.get("tags", []))
            subtexts.append(meta.get("subtext", ""))
            strategies.append(meta.get("reply_strategy", ""))
            emotional_states.append(meta.get("emotional_state", "neutral"))
            test_type = test_type or meta.get("test_type")

    for pattern, candidate_type, meaning in TEST_PATTERNS:
        if re.search(pattern, text):
            test_type = test_type or candidate_type
            tags.append("test")
            subtexts.append(meaning)
            strategies.append("不要急着自证；用稳定、轻松、边界清楚的方式回应")

    if re.search(r"(哈哈|笑死|hhh|233|绝了)", text):
        tags.append("playful")
        emotional_states.append("playful")
    if re.search(r"(别|不要|算了|冷静|先这样|不想)", text):
        tags.append("boundary")
        emotional_states.append("guarded")
    if re.search(r"(想你|喜欢|在乎|舍不得)", text):
        tags.append("warmth")
        emotional_states.append("warm")

    deduped_tags = list(dict.fromkeys(tags))
    state = _dominant_state(emotional_states)
    subtext = "；".join(s for s in subtexts if s) or _fallback_subtext(text, deduped_tags)
    strategy = "；".join(s for s in strategies if s) or _fallback_strategy(deduped_tags)

    return PragmaticSignal(
        surface_intent=_surface_intent(text, deduped_tags),
        subtext=subtext,
        deep_need=_deep_need(deduped_tags, state),
        emotional_state=state,
        test_flag="test" in deduped_tags or test_type is not None,
        test_type=test_type,
        reply_strategy=strategy,
        register_tags=deduped_tags,
        slang_hits=hits,
        implied_boundary=_boundary(deduped_tags),
        confidence=0.72 if hits or test_type else 0.42,
    )


def _dominant_state(states: List[str]) -> str:
    for candidate in ["guarded", "cold", "anxious", "playful", "warm"]:
        if candidate in states:
            return candidate
    return states[0] if states else "neutral"


def _surface_intent(text: str, tags: List[str]) -> str:
    if "soft_decline" in tags:
        return "保留或婉拒"
    if "test" in tags:
        return "关系测试"
    if "playful" in tags:
        return "调侃互动"
    if "boundary" in tags:
        return "边界提醒"
    if text.endswith("?") or text.endswith("？"):
        return "提问"
    return "普通聊天"


def _fallback_subtext(text: str, tags: List[str]) -> str:
    if "playful" in tags:
        return "表面在吐槽，实际是在维持轻松互动"
    if "boundary" in tags:
        return "对方在要求空间或降低关系压力"
    if "warmth" in tags:
        return "对方释放了一点情绪连接"
    return "没有明显潜台词，按自然聊天处理"


def _fallback_strategy(tags: List[str]) -> str:
    if "boundary" in tags:
        return "降压、短句、给空间，不追问"
    if "playful" in tags:
        return "轻松接梗，可以自嘲，不要解释太多"
    if "warmth" in tags:
        return "接住情绪，但不要突然拔高关系"
    return "保持自然语气，像真实聊天一样回应"


def _deep_need(tags: List[str], state: str) -> str:
    if "boundary" in tags or state == "guarded":
        return "需要空间和低压力"
    if "test" in tags:
        return "需要确认你的稳定性和边界"
    if "playful" in tags:
        return "需要轻松、有来有回的情绪流动"
    if "warmth" in tags:
        return "需要被接住但不被逼近"
    return "需要被自然理解"


def _boundary(tags: List[str]) -> str:
    if "soft_decline" in tags:
        return "暂时不明确答应"
    if "pace" in tags:
        return "节奏太快，需要降温"
    if "avoidance" in tags:
        return "不想继续当前话题"
    if "boundary" in tags:
        return "需要空间"
    return ""
