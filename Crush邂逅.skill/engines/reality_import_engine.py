from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict

from .types import CoreState, RelationshipProfile, clamp


ARCHETYPE_KEYWORDS = {
    "emotional": ["真诚", "情绪价值", "共鸣", "被理解", "在乎", "灵魂", "走心"],
    "security": ["稳定", "未来", "计划", "责任", "靠谱", "长期", "安全感"],
    "experience": ["新鲜感", "刺激", "开心", "好玩", "氛围", "体验", "情绪峰值"],
    "value": ["价值", "条件", "资源", "能力", "上进", "现实", "匹配"],
    "passive": ["随缘", "佛系", "懒得", "无所谓", "顺其自然", "慢热"],
}

ATTACHMENT_KEYWORDS = {
    "Secure": ["稳定", "沟通", "边界", "信任"],
    "Anxious": ["焦虑", "患得患失", "怕失去", "秒回", "不安"],
    "Dismissive Avoidant": ["冷淡", "独立", "距离", "不想被管"],
    "Fearful Avoidant": ["忽冷忽热", "拉扯", "矛盾", "想靠近又害怕"],
}

MBTI_KEYWORDS = {
    "ENFP": ["热情", "灵感", "自由", "感受", "表达"],
    "INFJ": ["深度", "意义", "理想", "洞察"],
    "ESTJ": ["规则", "效率", "执行", "结果"],
    "ISTJ": ["稳重", "秩序", "可靠", "细节"],
    "ESFP": ["社交", "现场", "玩", "情绪"]
}


@dataclass
class ImportResult:
    profile: RelationshipProfile
    state: CoreState
    canonical_archetype: str
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "state": self.state.to_dict(),
            "canonical_archetype": self.canonical_archetype,
            "evidence": self.evidence,
        }


class RealityImportEngine:
    def import_from_text(self, seed_profile: Dict[str, Any], source_text: str) -> ImportResult:
        text = source_text.lower()

        archetype, archetype_scores = self._best_label(text, ARCHETYPE_KEYWORDS)
        attachment, attachment_scores = self._best_label(text, ATTACHMENT_KEYWORDS)
        mbti, mbti_scores = self._best_label(text, MBTI_KEYWORDS)

        profile = RelationshipProfile(
            archetype=seed_profile.get("archetype", archetype),
            attachment_style=seed_profile.get("attachment_style", attachment),
            mbti=seed_profile.get("mbti", mbti),
            gender=seed_profile.get("gender", "female"),
            age=int(seed_profile.get("age", 24)),
            relationship_stage=seed_profile.get("relationship_stage", "拉扯期"),
        )

        sentiment = self._sentiment(text)
        volatility = self._volatility(text)
        pressure = self._pressure(text)

        base = {
            "emotional": (35, 32, 20),
            "security": (30, 18, 15),
            "experience": (42, 56, 30),
            "value": (28, 22, 24),
            "passive": (22, 8, 10),
        }
        favorability_base, tension_base, exploration_base = base.get(archetype, base["experience"])

        state = CoreState(
            favorability=clamp(favorability_base + sentiment * 30 - pressure * 20),
            tension=clamp(tension_base + volatility * 28 + sentiment * 8),
            neediness=clamp(pressure * 78 - sentiment * 12),
            frame_control=clamp(20 + sentiment * 20 - pressure * 22),
            exploration=clamp(exploration_base + volatility * 18),
            defense_level=clamp(26 + pressure * 48 - sentiment * 18),
            propulsion=clamp(14 + sentiment * 24 + volatility * 10),
            attachment_activation=clamp(22 + pressure * 35 + volatility * 22),
            trauma_level=clamp(18 + self._conflict_intensity(text) * 55),
            push_pull_sensitivity=clamp(20 + volatility * 44),
        ).normalize()

        evidence = {
            "archetype_scores": archetype_scores,
            "attachment_scores": attachment_scores,
            "mbti_scores": mbti_scores,
            "sentiment": sentiment,
            "volatility": volatility,
            "pressure": pressure,
        }

        return ImportResult(
            profile=profile,
            state=state,
            canonical_archetype=archetype,
            evidence=evidence,
        )

    def _best_label(self, text: str, table: Dict[str, list[str]]) -> tuple[str, Dict[str, int]]:
        scores: Dict[str, int] = {}
        for label, kws in table.items():
            scores[label] = sum(1 for kw in kws if kw in text)
        label = max(scores.items(), key=lambda x: x[1])[0]
        return label, scores

    def _sentiment(self, text: str) -> float:
        positive = len(re.findall(r"开心|喜欢|信任|期待|想见|温柔|理解", text))
        negative = len(re.findall(r"生气|失望|冷淡|吵|拉黑|崩溃|烦", text))
        if positive == negative == 0:
            return 0.0
        return clamp((positive - negative) / max(1, positive + negative), -1.0, 1.0)

    def _volatility(self, text: str) -> float:
        hits = len(re.findall(r"忽冷忽热|突然|反复|拉扯|时好时坏|又好又坏", text))
        return clamp(hits / 4.0, 0.0, 1.0)

    def _pressure(self, text: str) -> float:
        hits = len(re.findall(r"必须|立刻|马上|给我答复|逼|求你|为什么不回", text))
        return clamp(hits / 5.0, 0.0, 1.0)

    def _conflict_intensity(self, text: str) -> float:
        hits = len(re.findall(r"争吵|冷战|分手|拉黑|崩|情绪失控|指责", text))
        return clamp(hits / 5.0, 0.0, 1.0)
