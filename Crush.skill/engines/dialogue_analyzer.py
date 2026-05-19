from __future__ import annotations

import re

from .types import TurnAnalysis

POSITIVE_WORDS = {
    "开心", "想你", "喜欢", "欣赏", "有趣", "放松", "舒服", "信任", "温柔", "理解", "respect", "care", "thank", "thanks",
}
NEGATIVE_WORDS = {
    "烦", "失望", "冷淡", "生气", "吵", "拉黑", "讨厌", "难受", "压抑", "算了", "bad", "angry", "annoyed",
}
NEEDINESS_CUES = {
    "你为什么不回", "你在吗", "求你", "一定要", "马上回", "想我了吗", "是不是不爱", "别离开", "只有你", "求回复",
}
PRESSURE_CUES = {
    "给我答案", "现在就", "必须", "你应该", "你得", "立刻", "确定关系", "我们今天就", "逼", "承诺",
}
AUTHENTIC_CUES = {
    "我真实想法", "我会尊重", "你可以拒绝", "我理解", "我愿意慢一点", "坦白", "真诚", "边界", "尊重",
}
PLAYFUL_CUES = {
    "哈哈", "开玩笑", "逗你", "轻松", "好玩", "调皮",
}
STABILITY_CUES = {
    "计划", "长期", "稳定", "负责", "节奏", "边界", "一致", "可预期", "明天", "下周", "安排",
}
VALUE_SIGNAL_CUES = {
    "成长", "目标", "事业", "学习", "自律", "价值", "资源", "能力", "担当", "执行",
}
ATTACHMENT_TRIGGER_CUES = {
    "消失", "突然", "安全感", "忽冷忽热", "不确定", "被抛弃", "失控", "不安", "焦虑",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())


def _cue_score(text: str, cues: set[str], max_hits: int = 4) -> float:
    hits = sum(1 for cue in cues if cue and cue.lower() in text.lower())
    return min(1.0, hits / max_hits)


def analyze_text(message: str) -> TurnAnalysis:
    text = message.strip()
    tokens = _tokenize(text)

    pos_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg_hits = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    valence = 0.0
    if pos_hits or neg_hits:
        valence = (pos_hits - neg_hits) / max(1, pos_hits + neg_hits)

    analysis = TurnAnalysis(
        valence=valence,
        neediness_score=_cue_score(text, NEEDINESS_CUES),
        pressure_score=_cue_score(text, PRESSURE_CUES),
        authenticity_score=_cue_score(text, AUTHENTIC_CUES),
        playfulness_score=_cue_score(text, PLAYFUL_CUES),
        stability_score=_cue_score(text, STABILITY_CUES),
        value_signal_score=_cue_score(text, VALUE_SIGNAL_CUES),
        attachment_trigger_score=_cue_score(text, ATTACHMENT_TRIGGER_CUES),
    ).bounded()

    if analysis.neediness_score > 0.45:
        analysis.notes.append("需求感偏高")
    if analysis.pressure_score > 0.45:
        analysis.notes.append("推进压力偏高")
    if analysis.authenticity_score > 0.35:
        analysis.notes.append("表达了真实性和边界感")
    if analysis.playfulness_score > 0.35:
        analysis.notes.append("有轻松互动信号")

    return analysis
