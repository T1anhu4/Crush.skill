from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from .types import CoreState, RelationshipProfile, TurnAnalysis


@dataclass
class CoachAssessment:
    line_type: str
    relationship_stage: str
    interest_read: str
    persona_read: str
    user_neediness: str
    risk_level: str
    pressure_note: str
    next_move: str
    should_flirt: str
    warning_flags: list[str] = field(default_factory=list)
    prompt_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RelationshipCoach:
    """Relationship-literacy layer for training, not manipulation.

    It gives the NPC prompt realistic stakes and gives the CLI user a compact
    readout: what just happened, whether to push/pull, and what to learn.
    """

    def assess(
        self,
        message: str,
        analysis: TurnAnalysis,
        previous_state: CoreState,
        new_state: Dict[str, Any],
        delta: Dict[str, Any],
        profile: RelationshipProfile,
        canonical: str,
        recent_user: List[str] | None = None,
    ) -> CoachAssessment:
        recent_user = recent_user or []
        tags = set(analysis.register_tags)
        text = re.sub(r"\s+", "", message.lower())
        stage = self._stage(new_state)
        line_type = self._line_type(text, tags, analysis)
        interest = self._interest_read(new_state, delta, analysis)
        persona = self._persona_read(profile, canonical, new_state)
        neediness = self._neediness_read(analysis, previous_state, recent_user)
        risk = self._risk_level(analysis, delta, tags, line_type)
        should_flirt = self._should_flirt(new_state, analysis, tags, line_type)
        pressure_note = self._pressure_note(line_type, analysis, delta, tags)
        next_move = self._next_move(line_type, risk, should_flirt, tags)
        flags = self._warning_flags(text, tags, analysis, delta)
        rules = self._prompt_rules(line_type, risk, should_flirt, tags)
        return CoachAssessment(
            line_type=line_type,
            relationship_stage=stage,
            interest_read=interest,
            persona_read=persona,
            user_neediness=neediness,
            risk_level=risk,
            pressure_note=pressure_note,
            next_move=next_move,
            should_flirt=should_flirt,
            warning_flags=flags,
            prompt_rules=rules,
        )

    def _line_type(self, text: str, tags: set[str], analysis: TurnAnalysis) -> str:
        if "rejection_tease" in tags:
            return "伤害性拉扯/假性拒绝"
        if "direct_validation" in tags:
            return "索取确认"
        if "symbolic_naming" in tags or "assumed_intimacy" in tags:
            return "专属命名推进"
        if "nickname_boundary" in tags:
            return "亲密称呼推进"
        if re.search(r"(需要我|还是说需要我|都要|想我|喜欢我)", text):
            return "暧昧试探"
        if "soft_decline" in tags or "boundary" in tags:
            return "边界/保留"
        if "playful" in tags:
            return "轻松接梗"
        if analysis.authenticity_score > 0.45:
            return "真诚表达"
        return "普通推进"

    def _stage(self, state: Dict[str, Any]) -> str:
        fav = float(state.get("favorability", 0))
        tension = float(state.get("tension", 0))
        defense = float(state.get("defense_level", 0))
        exploration = float(state.get("exploration", 0))
        need = float(state.get("neediness", 0))
        if defense > 58:
            return "警惕期：先降压，不要继续要答案"
        if need > 55:
            return "需求暴露期：你需要收住节奏"
        if fav > 58 and tension > 45 and exploration > 42:
            return "暧昧窗口：可以轻推，但别索取承诺"
        if tension > 50 and exploration > 35:
            return "拉扯期：适合轻挑逗和低压邀约"
        if fav < 25:
            return "观察期：先建立舒适感和价值感"
        return "熟悉期：维持有来有回，别急着定性"

    def _interest_read(self, state: Dict[str, Any], delta: Dict[str, Any], analysis: TurnAnalysis) -> str:
        fav = float(state.get("favorability", 0))
        defense = float(state.get("defense_level", 0))
        exploration = float(state.get("exploration", 0))
        if defense > 55 or delta.get("defense_level", 0) >= 8:
            return "她有防备：不是没兴趣，但此刻不想被推进"
        if fav > 55 and exploration > 45:
            return "有好感且愿意探索：但仍需要不确定性"
        if exploration > 45 and fav <= 55:
            return "愿意聊天，更多是觉得有趣，未必等于喜欢"
        if fav < 25:
            return "偏普通/朋友感：先别抛高浓度暧昧"
        if analysis.playfulness_score > 0.45:
            return "她在接情绪，不代表已经接关系"
        return "信号不明：按普通聊天处理更安全"

    def _persona_read(self, profile: RelationshipProfile, canonical: str, state: Dict[str, Any]) -> str:
        archetype = {
            "experience": "体验型/E倾向：吃新鲜感，怕无聊和被束缚",
            "emotional": "情绪型：看重被接住，也容易被忽冷忽热触发",
            "security": "安全型：看重稳定和一致性，不吃过度拉扯",
            "value": "价值型：更看长期价值、边界和现实匹配",
            "passive": "被动/慢热型：少主动，不代表完全没感觉",
        }.get(canonical, "混合型：先观察她对推进的反应")
        attachment = profile.attachment_style or "Unknown"
        if "Avoidant" in attachment:
            return archetype + "；回避倾向，越被逼答案越后退"
        if "Anxious" in attachment:
            return archetype + "；焦虑倾向，会测试稳定性"
        return archetype

    def _neediness_read(self, analysis: TurnAnalysis, state: CoreState, recent_user: List[str]) -> str:
        repeated_questions = sum(1 for text in recent_user[-5:] if text.strip().endswith(("?", "？")))
        score = max(analysis.neediness_score, min(1.0, repeated_questions / 5))
        if score >= 0.75 or state.neediness > 58:
            return "高：你在要确认/要身份，容易失去张力"
        if score >= 0.45:
            return "中：可以表达，但别继续追问她态度"
        return "低：目前还算松弛"

    def _risk_level(self, analysis: TurnAnalysis, delta: Dict[str, Any], tags: set[str], line_type: str) -> str:
        if "rejection_tease" in tags or delta.get("defense_level", 0) >= 12:
            return "高"
        if analysis.pressure_score >= 0.6 or analysis.neediness_score >= 0.65:
            return "高"
        if line_type in {"索取确认", "专属命名推进", "亲密称呼推进"}:
            return "中高"
        if analysis.playfulness_score > 0.45 and analysis.pressure_score < 0.35:
            return "低"
        return "中"

    def _should_flirt(self, state: Dict[str, Any], analysis: TurnAnalysis, tags: set[str], line_type: str) -> str:
        defense = float(state.get("defense_level", 0))
        tension = float(state.get("tension", 0))
        exploration = float(state.get("exploration", 0))
        if defense > 50 or analysis.pressure_score > 0.55:
            return "不该抛高浓度暧昧：先降压"
        if line_type == "暧昧试探" and tension > 42 and exploration > 35:
            return "可以轻暧昧：短、玩笑、可撤回"
        if tension > 48 and exploration > 42:
            return "可以轻推：不要问喜欢不喜欢"
        return "先普通聊天：补舒适感和具体话题"

    def _pressure_note(self, line_type: str, analysis: TurnAnalysis, delta: Dict[str, Any], tags: set[str]) -> str:
        if "rejection_tease" in tags:
            return "这类玩笑会制造失去感，但也会伤信任；现实里不要用来操控。"
        if line_type == "索取确认":
            return "直接问喜不喜欢会把暧昧从感受变成考试，对方容易尴尬或防御。"
        if "symbolic_naming" in tags:
            return "专属名和花语很浪漫，但过早绑定会像在替对方确认关系。"
        if analysis.playfulness_score > 0.45:
            return "她接梗说明情绪在线，但不等于愿意关系升级。"
        if delta.get("defense_level", 0) > 0:
            return "她的防御在升高，下一句最好减少解释和索取。"
        return "当前压力可控，重点是保持节奏和具体互动。"

    def _next_move(self, line_type: str, risk: str, should_flirt: str, tags: set[str]) -> str:
        if risk == "高":
            return "收住：短句承认玩笑/压力，换低压具体话题，不追问态度。"
        if line_type == "索取确认":
            return "不要继续问真话；改成轻松自嘲或分享一个具体场景。"
        if line_type == "暧昧试探":
            return "接她的梗，轻轻推一下再撤，保留不确定性。"
        if "soft_decline" in tags:
            return "接受保留，不争辩；换成她容易接的日常话题。"
        if "可以轻" in should_flirt:
            return "可以抛一句低成本暧昧，但不要要承诺。"
        return "问一个具体、有画面的问题，少问抽象态度。"

    def _warning_flags(self, text: str, tags: set[str], analysis: TurnAnalysis, delta: Dict[str, Any]) -> list[str]:
        flags = []
        if "direct_validation" in tags:
            flags.append("索取喜欢确认")
        if "rejection_tease" in tags:
            flags.append("伤害性玩笑")
        if "assumed_intimacy" in tags:
            flags.append("默认同意")
        if re.search(r"(红包|转账|买.*包|给我买|礼物|请我)", text):
            flags.append("物质索取信号：需要结合长期行为判断，不能一刀切贴拜金标签")
        if re.search(r"(哥哥|弟弟|好朋友|朋友)", text) and analysis.pressure_score < 0.4:
            flags.append("朋友框架风险")
        if delta.get("defense_level", 0) > 8:
            flags.append("防御上升")
        return flags

    def _prompt_rules(self, line_type: str, risk: str, should_flirt: str, tags: set[str]) -> list[str]:
        rules = [
            "不要像陪聊客服一样永远积极；你有自己的情绪、边界和不确定性。",
            "减少表情包堆叠；同一条最多 1-2 个 emoji，不要每句都笑死/💀/🤣。",
        ]
        if line_type == "索取确认":
            rules.append("对方在问你喜不喜欢他。不要直接给满分答案；用尴尬、转移、轻微防御或半真半假的方式回应。")
        if "rejection_tease" in tags:
            rules.append("对方刚用不喜欢/拒绝来逗你。你会被刺到一点，回复要短一点、冷一点，不要被一句逗你的马上哄好。")
        if risk in {"高", "中高"}:
            rules.append("当前压力偏高。降低热情和探索欲，不主动帮对方推进关系。")
        if "不该抛高浓度" in should_flirt:
            rules.append("避免暧昧升级，先保留空间。")
        return rules
