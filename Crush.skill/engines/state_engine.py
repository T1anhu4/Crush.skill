"""
Nonlinear Relationship State Engine.

Key improvements over linear formula:
1. S-curve saturation — diminishing returns at extremes (70→80 harder than 0→10)
2. Habituation decay — repeated identical signals lose impact
3. Tipping points — thresholds where small changes cause big shifts
4. Cross-dimension coupling — high defense dampens favorability gain
5. Context-dependent weighting — same signal, different meaning at different stages
"""
from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from .defense_engine import DefenseEngine
from .types import CoreState, RelationshipProfile, TurnAnalysis, clamp

# ── S-curve function (logistic) for diminishing returns ─────────
def s_curve(x: float, k: float = 0.12, midpoint: float = 50.0) -> float:
    """
    Logistic S-curve centered at `midpoint` with steepness `k`.
    Maps (-inf, inf) → (0, 1). Used to model how the same delta
    has different impact at different baseline levels.
    """
    try:
        return 1.0 / (1.0 + math.exp(-k * (x - midpoint)))
    except OverflowError:
        return 0.0 if x < midpoint else 1.0


def saturation_factor(current: float, direction: float) -> float:
    """
    How much harder/easier it is to move further in `direction`.
    - Moving toward +100 when already at 70: harder (factor ~0.5)
    - Moving toward +100 when at 10: easier (factor ~1.0)
    - Moving toward -100 when at 10: easier (factor ~1.0)
    """
    if direction > 0:
        return 1.0 - s_curve(current, k=0.08, midpoint=55.0) * 0.7
    elif direction < 0:
        return 1.0 - (1.0 - s_curve(current, k=0.08, midpoint=-55.0)) * 0.7
    return 1.0


ARCHETYPE_WEIGHTS = {
    "emotional": {
        "authenticity": 1.4, "stability": 0.7, "value": 0.6, "playfulness": 1.1,
    },
    "security": {
        "authenticity": 1.0, "stability": 1.5, "value": 1.1, "playfulness": 0.7,
    },
    "experience": {
        "authenticity": 0.9, "stability": 0.6, "value": 0.7, "playfulness": 1.6,
    },
    "value": {
        "authenticity": 0.8, "stability": 1.0, "value": 1.6, "playfulness": 0.6,
    },
    "passive": {
        "authenticity": 0.8, "stability": 1.0, "value": 0.8, "playfulness": 0.5,
    },
}


class StateEngine:
    def __init__(self) -> None:
        self.defense = DefenseEngine()
        # Track recent signals for habituation detection
        self._signal_history: Dict[str, List[float]] = {}
        self._habituation_window = 5

    def _weight(self, canonical_archetype: str) -> Dict[str, float]:
        return ARCHETYPE_WEIGHTS.get(canonical_archetype, ARCHETYPE_WEIGHTS["experience"])

    def _habituation_penalty(self, session_id: str, signal_key: str, value: float) -> float:
        """Reduce impact of repeated similar signals. Returns penalty multiplier 0-1."""
        key = f"{session_id}:{signal_key}"
        if key not in self._signal_history:
            self._signal_history[key] = []
        history = self._signal_history[key]
        history.append(value)
        if len(history) > self._habituation_window:
            history.pop(0)

        if len(history) < 2:
            return 1.0

        # If last N signals are similar (std dev low), reduce impact
        avg = sum(history) / len(history)
        variance = sum((v - avg) ** 2 for v in history) / len(history)
        std = math.sqrt(variance)
        if std < 0.1 and abs(value - avg) < 0.15:
            penalty = max(0.35, 1.0 - len(history) * 0.13)
            return penalty
        return 1.0

    def _cross_dimension_modifier(self, state: CoreState, target_dim: str, delta: float) -> float:
        """Cross-dimension coupling: certain state combos amplify/dampen changes."""
        modifier = 1.0

        # High defense dampens positive favorability changes
        if target_dim == "favorability" and delta > 0 and state.defense_level > 50:
            modifier *= max(0.4, 1.0 - (state.defense_level - 50) / 100)

        # High tension amplifies both positive and negative changes
        if target_dim == "favorability" and state.tension > 60:
            modifier *= 1.3

        # High neediness in user dampens favorability growth
        if target_dim == "favorability" and state.neediness > 50:
            modifier *= 0.7

        # Low exploration makes favorability harder to grow
        if target_dim == "favorability" and delta > 0 and state.exploration < 20 and state.favorability > 30:
            modifier *= 0.8

        return modifier

    def apply_turn(
        self,
        state: CoreState,
        profile: RelationshipProfile,
        canonical_archetype: str,
        analysis: TurnAnalysis,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        w = self._weight(canonical_archetype)
        defense_result = self.defense.evaluate(state, analysis)

        # ── Base deltas (improved linear combination) ──
        # Apply habituation penalties to repeated signals
        auth_penalty = self._habituation_penalty(session_id, "authenticity", analysis.authenticity_score)
        play_penalty = self._habituation_penalty(session_id, "playfulness", analysis.playfulness_score)
        need_penalty = self._habituation_penalty(session_id, "neediness", analysis.neediness_score)

        favorability_base = (
            analysis.valence * 16.0
            + analysis.authenticity_score * 10.0 * w["authenticity"] * auth_penalty
            + analysis.stability_score * 6.0 * w["stability"]
            + analysis.value_signal_score * 5.0 * w["value"]
            + analysis.playfulness_score * 7.0 * w["playfulness"] * play_penalty
            - analysis.neediness_score * 18.0 * need_penalty
            - analysis.pressure_score * 16.0
            + defense_result.favorability_delta
        )

        tension_base = (
            analysis.playfulness_score * 18.0 * w["playfulness"]
            + analysis.valence * 7.0
            - analysis.neediness_score * 10.0
            - analysis.pressure_score * 8.0
        )

        exploration_base = (
            analysis.playfulness_score * 11.0 * w["playfulness"]
            + analysis.authenticity_score * 5.0
            - analysis.pressure_score * 8.0
            + defense_result.exploration_delta
        )

        propulsion_base = analysis.playfulness_score * 9.0 + analysis.valence * 6.0 - analysis.pressure_score * 7.0

        # ── Apply nonlinear saturation ──
        favorability_delta = favorability_base * saturation_factor(state.favorability, favorability_base)
        tension_delta = tension_base * saturation_factor(state.tension, tension_base)
        exploration_delta = exploration_base * saturation_factor(state.exploration, exploration_base)
        neediness_delta = analysis.neediness_score * 26.0 - analysis.stability_score * 8.0
        frame_delta = analysis.authenticity_score * 8.0 + analysis.value_signal_score * 5.0 - analysis.neediness_score * 12.0
        propulsion_delta = propulsion_base * saturation_factor(state.propulsion, propulsion_base)
        attachment_delta = analysis.attachment_trigger_score * 13.0 + analysis.pressure_score * 5.0 - analysis.stability_score * 4.0
        defense_delta = defense_result.defense_delta

        # ── Apply cross-dimension modifiers ──
        favorability_delta *= self._cross_dimension_modifier(state, "favorability", favorability_delta)
        tension_delta *= self._cross_dimension_modifier(state, "tension", tension_delta)
        exploration_delta *= self._cross_dimension_modifier(state, "exploration", exploration_delta)

        # ── Update state ──
        previous = state.to_dict()
        state.favorability = clamp(state.favorability + favorability_delta)
        state.tension = clamp(state.tension + tension_delta)
        state.exploration = clamp(state.exploration + exploration_delta)
        state.neediness = clamp(state.neediness + neediness_delta)
        state.frame_control = clamp(state.frame_control + frame_delta)
        state.propulsion = clamp(state.propulsion + propulsion_delta)
        state.attachment_activation = clamp(state.attachment_activation + attachment_delta)
        state.defense_level = clamp(state.defense_level + defense_delta)

        # ── Tipping points (phase transitions) ──
        if state.favorability > 70 and previous.get("favorability", 0) <= 70:
            state.exploration = clamp(state.exploration + 12)

        if state.defense_level > 65 and previous.get("defense_level", 0) <= 65:
            state.tension = clamp(state.tension + 15)

        if state.favorability < -30 and previous.get("favorability", 0) >= -30:
            state.defense_level = clamp(state.defense_level + 10)
            state.tension = clamp(state.tension + 10)

        # Relationship vector classification
        triggered_tags: list[str] = []
        if defense_result.triggered:
            triggered_tags.append("defense_triggered")
        if favorability_delta >= 10:
            triggered_tags.append("attraction_peak")
        if favorability_delta <= -10:
            triggered_tags.append("frame_collapse_risk")

        delta = {
            "favorability": round(state.favorability - previous["favorability"], 2),
            "tension": round(state.tension - previous["tension"], 2),
            "neediness": round(state.neediness - previous["neediness"], 2),
            "frame_control": round(state.frame_control - previous["frame_control"], 2),
            "exploration": round(state.exploration - previous["exploration"], 2),
            "defense_level": round(state.defense_level - previous["defense_level"], 2),
            "propulsion": round(state.propulsion - previous["propulsion"], 2),
            "attachment_activation": round(state.attachment_activation - previous["attachment_activation"], 2),
        }

        relationship_vector = self._relationship_vector(state)

        return {
            "state": state.to_dict(),
            "delta": delta,
            "defense": defense_result.to_dict(),
            "analysis": analysis.to_dict(),
            "profile": asdict(profile),
            "tags": triggered_tags,
            "relationship_vector": relationship_vector,
        }

    def _relationship_vector(self, state: CoreState) -> str:
        if state.defense_level > 60 and state.favorability < 20:
            return "高防御-低连接"
        if state.favorability > 50 and state.exploration > 40:
            return "高连接-高探索"
        if state.tension > 50 and state.defense_level < 40:
            return "高张力-可推进"
        if state.favorability > 60 and state.tension < 30:
            return "舒适区-稳定发展"
        if state.neediness > 50:
            return "需求感过高-需要降温"
        if state.attachment_activation > 60:
            return "依恋激活-需要安全感"
        return "观察期"
