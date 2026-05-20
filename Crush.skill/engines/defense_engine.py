from __future__ import annotations

from dataclasses import dataclass

from .types import CoreState, TurnAnalysis, clamp


@dataclass
class DefenseResult:
    triggered: bool
    reason: str
    defense_delta: float
    favorability_delta: float
    exploration_delta: float

    def to_dict(self) -> dict:
        return {
            "triggered": self.triggered,
            "reason": self.reason,
            "defense_delta": self.defense_delta,
            "favorability_delta": self.favorability_delta,
            "exploration_delta": self.exploration_delta,
        }


class DefenseEngine:
    def evaluate(self, state: CoreState, analysis: TurnAnalysis) -> DefenseResult:
        defense_pressure = (
            analysis.neediness_score * 0.45
            + analysis.pressure_score * 0.45
            + analysis.attachment_trigger_score * 0.10
        )
        vulnerability = clamp((50.0 - state.favorability) / 100.0, 0.0, 1.0)
        defense_score = defense_pressure * (1.0 + vulnerability)

        if defense_score >= 0.72:
            return DefenseResult(
                triggered=True,
                reason="高需求感+高压力触发防御",
                defense_delta=24.0,
                favorability_delta=-18.0,
                exploration_delta=-12.0,
            )

        if defense_score >= 0.55:
            return DefenseResult(
                triggered=True,
                reason="关系压力升高，进入警惕状态",
                defense_delta=12.0,
                favorability_delta=-8.0,
                exploration_delta=-6.0,
            )

        if analysis.authenticity_score > 0.45 and analysis.pressure_score < 0.3:
            return DefenseResult(
                triggered=False,
                reason="真诚表达降低防御",
                defense_delta=-8.0,
                favorability_delta=4.0,
                exploration_delta=3.0,
            )

        return DefenseResult(
            triggered=False,
            reason="防御系统平稳",
            defense_delta=-2.0,
            favorability_delta=1.0,
            exploration_delta=1.0,
        )
