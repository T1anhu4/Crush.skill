from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from .defense_engine import DefenseEngine
from .types import CoreState, RelationshipProfile, TurnAnalysis, clamp


ARCHETYPE_WEIGHTS = {
    "emotional": {
        "authenticity": 1.4,
        "stability": 0.7,
        "value": 0.6,
        "playfulness": 1.1,
    },
    "security": {
        "authenticity": 1.0,
        "stability": 1.5,
        "value": 1.1,
        "playfulness": 0.7,
    },
    "experience": {
        "authenticity": 0.9,
        "stability": 0.6,
        "value": 0.7,
        "playfulness": 1.6,
    },
    "value": {
        "authenticity": 0.8,
        "stability": 1.0,
        "value": 1.6,
        "playfulness": 0.6,
    },
    "passive": {
        "authenticity": 0.8,
        "stability": 1.0,
        "value": 0.8,
        "playfulness": 0.5,
    },
}


class StateEngine:
    def __init__(self) -> None:
        self.defense = DefenseEngine()

    def _weight(self, canonical_archetype: str) -> Dict[str, float]:
        return ARCHETYPE_WEIGHTS.get(canonical_archetype, ARCHETYPE_WEIGHTS["experience"])

    def apply_turn(
        self,
        state: CoreState,
        profile: RelationshipProfile,
        canonical_archetype: str,
        analysis: TurnAnalysis,
    ) -> Dict[str, Any]:
        w = self._weight(canonical_archetype)
        defense_result = self.defense.evaluate(state, analysis)

        favorability_delta = (
            analysis.valence * 16.0
            + analysis.authenticity_score * 10.0 * w["authenticity"]
            + analysis.stability_score * 6.0 * w["stability"]
            + analysis.value_signal_score * 5.0 * w["value"]
            + analysis.playfulness_score * 7.0 * w["playfulness"]
            - analysis.neediness_score * 18.0
            - analysis.pressure_score * 16.0
            + defense_result.favorability_delta
        )

        tension_delta = (
            analysis.playfulness_score * 18.0 * w["playfulness"]
            + analysis.valence * 7.0
            - analysis.neediness_score * 10.0
            - analysis.pressure_score * 8.0
        )

        exploration_delta = (
            analysis.playfulness_score * 11.0 * w["playfulness"]
            + analysis.authenticity_score * 5.0
            - analysis.pressure_score * 8.0
            + defense_result.exploration_delta
        )

        neediness_delta = analysis.neediness_score * 26.0 - analysis.stability_score * 8.0
        frame_delta = analysis.authenticity_score * 8.0 + analysis.value_signal_score * 5.0 - analysis.neediness_score * 12.0
        propulsion_delta = analysis.playfulness_score * 9.0 + analysis.valence * 6.0 - analysis.pressure_score * 7.0
        attachment_delta = analysis.attachment_trigger_score * 13.0 + analysis.pressure_score * 5.0 - analysis.stability_score * 4.0
        defense_delta = defense_result.defense_delta

        previous = state.to_dict()
        state.favorability = clamp(state.favorability + favorability_delta)
        state.tension = clamp(state.tension + tension_delta)
        state.exploration = clamp(state.exploration + exploration_delta)
        state.neediness = clamp(state.neediness + neediness_delta)
        state.frame_control = clamp(state.frame_control + frame_delta)
        state.propulsion = clamp(state.propulsion + propulsion_delta)
        state.attachment_activation = clamp(state.attachment_activation + attachment_delta)
        state.defense_level = clamp(state.defense_level + defense_delta)

        if state.favorability < -50:
            state.defense_level = clamp(state.defense_level + 8)
        if state.favorability > 60 and analysis.neediness_score < 0.3:
            state.defense_level = clamp(state.defense_level - 6)

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

        triggered_tags: list[str] = []
        if defense_result.triggered:
            triggered_tags.append("defense_triggered")
        if delta["favorability"] >= 10:
            triggered_tags.append("attraction_peak")
        if delta["favorability"] <= -10:
            triggered_tags.append("frame_collapse_risk")

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
        return "观察期"
