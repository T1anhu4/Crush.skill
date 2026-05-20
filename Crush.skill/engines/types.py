from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict


MIN_STATE = -100.0
MAX_STATE = 100.0


def clamp(value: float, minimum: float = MIN_STATE, maximum: float = MAX_STATE) -> float:
    return max(minimum, min(maximum, value))


@dataclass
class RelationshipProfile:
    archetype: str
    attachment_style: str = "Secure"
    mbti: str = "ENFP"
    gender: str = "female"
    age: int = 24
    relationship_stage: str = "暧昧期"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CoreState:
    favorability: float = 0.0
    tension: float = 0.0
    neediness: float = 0.0
    frame_control: float = 0.0
    exploration: float = 0.0
    defense_level: float = 0.0
    propulsion: float = 0.0
    attachment_activation: float = 0.0
    trauma_level: float = 0.0
    push_pull_sensitivity: float = 0.0

    def normalize(self) -> "CoreState":
        self.favorability = clamp(self.favorability)
        self.tension = clamp(self.tension)
        self.neediness = clamp(self.neediness)
        self.frame_control = clamp(self.frame_control)
        self.exploration = clamp(self.exploration)
        self.defense_level = clamp(self.defense_level)
        self.propulsion = clamp(self.propulsion)
        self.attachment_activation = clamp(self.attachment_activation)
        self.trauma_level = clamp(self.trauma_level)
        self.push_pull_sensitivity = clamp(self.push_pull_sensitivity)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoreState":
        return cls(**{k: float(v) for k, v in data.items()}).normalize()


@dataclass
class TurnAnalysis:
    valence: float = 0.0
    neediness_score: float = 0.0
    pressure_score: float = 0.0
    authenticity_score: float = 0.0
    playfulness_score: float = 0.0
    stability_score: float = 0.0
    value_signal_score: float = 0.0
    attachment_trigger_score: float = 0.0
    notes: list[str] = field(default_factory=list)

    def bounded(self) -> "TurnAnalysis":
        self.valence = clamp(self.valence, -1.0, 1.0)
        self.neediness_score = clamp(self.neediness_score, 0.0, 1.0)
        self.pressure_score = clamp(self.pressure_score, 0.0, 1.0)
        self.authenticity_score = clamp(self.authenticity_score, 0.0, 1.0)
        self.playfulness_score = clamp(self.playfulness_score, 0.0, 1.0)
        self.stability_score = clamp(self.stability_score, 0.0, 1.0)
        self.value_signal_score = clamp(self.value_signal_score, 0.0, 1.0)
        self.attachment_trigger_score = clamp(self.attachment_trigger_score, 0.0, 1.0)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
