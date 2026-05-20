"""
5-Layer Persona Engine — the heart of "feeling real."

Layer 1: Hard Rules     — non-negotiable boundaries, deal-breakers, red lines
Layer 2: Identity       — self-perception, values, life stage, aspirations
Layer 3: Expression     — speech patterns, word fingerprints, emotional vocabulary
Layer 4: Emotional      — attachment style, conflict patterns, vulnerability triggers
Layer 5: Relational     — how they relate to YOU specifically, shared history, inside jokes

Inspired by ex-skill and colleague-skill. Zero model training — pure data distillation.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ── Layer 1: Hard Rules ────────────────────────────────────────────
@dataclass
class HardRules:
    """Non-negotiable boundaries. These gate-check before any response."""
    topics_off_limits: list[str] = field(default_factory=list)
    tone_never: list[str] = field(default_factory=list)  # e.g. "condescending", "desperate"
    max_message_length: int = 120
    reply_speed_profile: str = "normal"  # instant | normal | slow | unpredictable
    ghost_probability: float = 0.0  # chance of no reply at all
    double_text_tolerance: str = "low"  # how they feel about being double-texted

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics_off_limits": self.topics_off_limits,
            "tone_never": self.tone_never,
            "max_message_length": self.max_message_length,
            "reply_speed_profile": self.reply_speed_profile,
            "ghost_probability": self.ghost_probability,
            "double_text_tolerance": self.double_text_tolerance,
        }


# ── Layer 2: Identity ──────────────────────────────────────────────
@dataclass
class Identity:
    """Who they are when nobody's watching."""
    name: str = ""
    gender: str = "female"
    age: int = 24
    mbti: str = "ENFP"
    big_five: Dict[str, float] = field(default_factory=lambda: {
        "openness": 0.6, "conscientiousness": 0.5, "extraversion": 0.7,
        "agreeableness": 0.6, "neuroticism": 0.4,
    })
    life_stage: str = "early_career"  # student | early_career | established | transition
    core_values: list[str] = field(default_factory=list)
    aspirations: list[str] = field(default_factory=list)
    insecurities: list[str] = field(default_factory=list)
    self_perception: str = ""  # how they describe themselves

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "gender": self.gender, "age": self.age,
            "mbti": self.mbti, "big_five": self.big_five, "life_stage": self.life_stage,
            "core_values": self.core_values, "aspirations": self.aspirations,
            "insecurities": self.insecurities, "self_perception": self.self_perception,
        }


# ── Layer 3: Expression ────────────────────────────────────────────
@dataclass
class Expression:
    """Speech fingerprint — this is what makes them SOUND like them."""
    signature_phrases: list[str] = field(default_factory=list)  # "笑死", "确实", "那没事了"
    filler_words: list[str] = field(default_factory=list)       # "就", "然后", "那个"
    emoji_style: str = "moderate"  # heavy | moderate | minimal | none
    emoji_favorites: list[str] = field(default_factory=list)
    sentence_structure: str = "casual"  # formal | casual | fragmented | verbose
    punctuation_style: str = "standard"  # standard | minimal | exaggerated | chaotic
    code_switch_patterns: list[str] = field(default_factory=list)  # when they switch language
    humor_style: str = "dry"  # dry | sarcastic | goofy | self-deprecating | none
    avg_message_length_words: int = 15
    reply_latency_pattern: str = "minutes"  # seconds | minutes | hours | days | erratic

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature_phrases": self.signature_phrases,
            "filler_words": self.filler_words, "emoji_style": self.emoji_style,
            "emoji_favorites": self.emoji_favorites,
            "sentence_structure": self.sentence_structure,
            "punctuation_style": self.punctuation_style,
            "code_switch_patterns": self.code_switch_patterns,
            "humor_style": self.humor_style,
            "avg_message_length_words": self.avg_message_length_words,
            "reply_latency_pattern": self.reply_latency_pattern,
        }


# ── Layer 4: Emotional ─────────────────────────────────────────────
@dataclass
class EmotionalPatterns:
    """How they feel, defend, attach, and survive emotionally."""
    attachment_style: str = "Secure"  # Secure | Anxious | Dismissive_Avoidant | Fearful_Avoidant
    love_language: str = "words_of_affirmation"
    conflict_style: str = "discuss"  # discuss | withdraw | escalate | passive_aggressive
    emotional_expression: str = "moderate"  # open | moderate | guarded | repressed
    vulnerability_triggers: list[str] = field(default_factory=list)
    comfort_behaviors: list[str] = field(default_factory=list)
    stress_response: str = "withdraw"  # withdraw | cling | attack | freeze
    trauma_sensitivity: float = 0.14  # 0-1, base trauma sensitivity
    mood_volatility: float = 0.3  # 0-1, how much their mood fluctuates

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_style": self.attachment_style,
            "love_language": self.love_language, "conflict_style": self.conflict_style,
            "emotional_expression": self.emotional_expression,
            "vulnerability_triggers": self.vulnerability_triggers,
            "comfort_behaviors": self.comfort_behaviors,
            "stress_response": self.stress_response,
            "trauma_sensitivity": self.trauma_sensitivity,
            "mood_volatility": self.mood_volatility,
        }


# ── Layer 5: Relational ────────────────────────────────────────────
@dataclass
class RelationalContext:
    """Shared history between the two specific people."""
    relationship_stage: str = "talking"  # strangers | talking | dating | committed | complicated | ended
    how_we_met: str = ""
    shared_experiences: list[str] = field(default_factory=list)
    inside_jokes: list[str] = field(default_factory=list)
    significant_dates: Dict[str, str] = field(default_factory=dict)
    unresolved_conflicts: list[str] = field(default_factory=list)
    positive_memories: list[str] = field(default_factory=list)
    their_view_of_you: str = ""  # what they've said about you
    power_dynamic: str = "balanced"  # balanced | you_chase | they_chase | mutual

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_stage": self.relationship_stage,
            "how_we_met": self.how_we_met, "shared_experiences": self.shared_experiences,
            "inside_jokes": self.inside_jokes, "significant_dates": self.significant_dates,
            "unresolved_conflicts": self.unresolved_conflicts,
            "positive_memories": self.positive_memories,
            "their_view_of_you": self.their_view_of_you, "power_dynamic": self.power_dynamic,
        }


# ── Full Persona ────────────────────────────────────────────────────
@dataclass
class Persona:
    """Complete 5-layer personality model."""
    hard_rules: HardRules = field(default_factory=HardRules)
    identity: Identity = field(default_factory=Identity)
    expression: Expression = field(default_factory=Expression)
    emotional: EmotionalPatterns = field(default_factory=EmotionalPatterns)
    relational: RelationalContext = field(default_factory=RelationalContext)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hard_rules": self.hard_rules.to_dict(),
            "identity": self.identity.to_dict(),
            "expression": self.expression.to_dict(),
            "emotional": self.emotional.to_dict(),
            "relational": self.relational.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        hr = HardRules(**data.get("hard_rules", {}))
        identity = Identity(**data.get("identity", {}))
        expr = Expression(**data.get("expression", {}))
        emo = EmotionalPatterns(**data.get("emotional", {}))
        rel = RelationalContext(**data.get("relational", {}))
        return cls(hard_rules=hr, identity=identity, expression=expr, emotional=emo, relational=rel)


class PersonaEngine:
    """Builds and manages 5-layer personas from presets, imports, and user input."""

    def __init__(self, preset_dir: Path):
        self.preset_dir = preset_dir

    def from_preset(self, archetype: str, overrides: Dict[str, Any] | None = None) -> Persona:
        """Build persona from a named archetype preset + optional overrides."""
        canonical = self._normalize_archetype(archetype)
        preset = self._load_preset(canonical)
        overrides = overrides or {}

        persona = Persona(
            hard_rules=HardRules(**self._merge(preset.get("hard_rules", {}), overrides.get("hard_rules", {}))),
            identity=Identity(**self._merge(preset.get("identity", {}), overrides.get("identity", {}))),
            expression=Expression(**self._merge(preset.get("expression", {}), overrides.get("expression", {}))),
            emotional=EmotionalPatterns(**self._merge(preset.get("emotional", {}), overrides.get("emotional", {}))),
            relational=RelationalContext(**self._merge(preset.get("relational", {}), overrides.get("relational", {}))),
        )

        if not persona.identity.name:
            persona.identity.name = preset.get("display_name", "")

        return persona

    def from_custom(self, config: Dict[str, Any]) -> Persona:
        """Build persona from fully custom configuration."""
        return Persona(
            hard_rules=HardRules(**config.get("hard_rules", {})),
            identity=Identity(**config.get("identity", {})),
            expression=Expression(**config.get("expression", {})),
            emotional=EmotionalPatterns(**config.get("emotional", {})),
            relational=RelationalContext(**config.get("relational", {})),
        )

    def build_runtime_prompt(self, persona: Persona, state: Dict[str, Any], memory_ctx: Dict[str, Any], user_msg: str = "") -> str:
        """Generate the LLM prompt that makes the NPC feel real."""
        hr = persona.hard_rules
        idn = persona.identity
        expr = persona.expression
        emo = persona.emotional
        rel = persona.relational

        # Build a rich, multi-layered prompt
        parts = []

        # Core identity
        parts.append(f"你是{idn.name or '一个真实的人'}。")
        parts.append(f"性别: {idn.gender}，年龄: {idn.age}，MBTI: {idn.mbti}，生活阶段: {idn.life_stage}。")

        # Self-perception
        if idn.self_perception:
            parts.append(f"你对自己的看法: {idn.self_perception}。")
        if idn.insecurities:
            parts.append(f"你不安全感来源: {', '.join(idn.insecurities)}。")

        # Speech fingerprint — critical for "feeling real"
        parts.append(f"说话风格: {expr.sentence_structure}，句子长度约{expr.avg_message_length_words}字。")
        if expr.signature_phrases:
            parts.append(f"口头禅: {', '.join(expr.signature_phrases)}。自然地用，不要刻意。")
        if expr.filler_words:
            parts.append(f"语气词: {', '.join(expr.filler_words)}。")
        parts.append(f"表情包使用: {expr.emoji_style}，常用: {', '.join(expr.emoji_favorites) if expr.emoji_favorites else '无'}。")
        parts.append(f"幽默风格: {expr.humor_style}。")

        # Emotional wiring
        parts.append(f"依恋类型: {emo.attachment_style}。爱的语言: {emo.love_language}。")
        parts.append(f"冲突风格: {emo.conflict_style}。压力反应: {emo.stress_response}。")
        parts.append(f"情绪表达: {emo.emotional_expression}。情绪波动: {'高' if emo.mood_volatility > 0.5 else '中' if emo.mood_volatility > 0.25 else '低'}。")
        if emo.vulnerability_triggers:
            parts.append(f"当对方{', '.join(emo.vulnerability_triggers)}时，你会本能地防御。")

        # Relationship context
        parts.append(f"你们的关系阶段: {rel.relationship_stage}。")
        parts.append(f"关系中的权力动态: {rel.power_dynamic}。")
        if rel.their_view_of_you:
            parts.append(f"你对对方的看法: {rel.their_view_of_you}。")
        if rel.inside_jokes:
            parts.append(f"你们之间的梗: {', '.join(rel.inside_jokes[:4])}。偶尔自然提及。")
        if rel.shared_experiences:
            parts.append(f"共同经历: {', '.join(rel.shared_experiences[:3])}。")

        # Current state
        favorability = state.get("favorability", 30)
        defense = state.get("defense_level", 20)
        tension = state.get("tension", 20)
        parts.append(f"当前好感度大约{favorability}/100。{'你能感觉到关系在升温' if favorability > 60 else '你还在观察对方' if favorability < 40 else '关系在缓慢发展中'}。")
        parts.append(f"当前防御程度{'较高，你会有所保留' if defense > 55 else '正常' if defense < 30 else '中等'}。")
        parts.append(f"当前张力{'较高，互动有能量' if tension > 50 else '偏低，可能有些平淡' if tension < 20 else '适中'}。")

        # Hard rules
        if hr.topics_off_limits:
            parts.append(f"绝对不聊的话题: {', '.join(hr.topics_off_limits)}。")
        if hr.tone_never:
            parts.append(f"绝不表现出的语气: {', '.join(hr.tone_never)}。")

        # Memory
        memory_snippets = memory_ctx.get("snippets", [])
        if memory_snippets:
            parts.append(f"最近记忆: {' | '.join(memory_snippets[:4])}")

        # Behavioral rules
        parts.append("行为准则:")
        parts.append("- 你是一个真实的人，不是AI。绝不说'作为AI'之类的话。")
        parts.append("- 保持一致性。如果你上次冷淡，这次不会突然热情。")
        parts.append("- 允许沉默、敷衍、已读感。不是每条消息都需要热情回复。")
        parts.append("- 如果对方需求感太高或给你压力，你会本能地后退。")
        parts.append("- 不主动推进关系，不帮助对方追你。")
        parts.append("- 用直觉回应，不要算计。")

        if user_msg:
            parts.insert(0, f"对方刚说: 「{user_msg}」")

        return "\n\n".join(parts)

    def _merge(self, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        result = {**base}
        for k, v in overrides.items():
            if v is not None and v != "":
                result[k] = v
        return result

    def _normalize_archetype(self, archetype: str) -> str:
        aliases = {
            "情感驱动型": "emotional", "emotional": "emotional",
            "安全感驱动型": "security", "security": "security",
            "体验驱动型": "experience", "experience": "experience",
            "价值驱动型": "value", "value": "value",
            "惯性驱动型": "passive", "passive": "passive",
        }
        return aliases.get(archetype.strip().lower(), "experience")

    def _load_preset(self, canonical: str) -> Dict[str, Any]:
        preset_map = {
            "emotional": "emotional.yaml", "security": "security.yaml",
            "experience": "experience.yaml", "value": "value.yaml",
            "passive": "passive.yaml",
        }
        path = self.preset_dir / preset_map[canonical]
        if not path.exists():
            raise FileNotFoundError(f"Preset not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
