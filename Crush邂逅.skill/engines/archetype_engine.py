from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .types import CoreState, RelationshipProfile

PRESET_FILE_MAP = {
    "emotional": "emotional.yaml",
    "security": "security.yaml",
    "experience": "experience.yaml",
    "value": "value.yaml",
    "passive": "passive.yaml",
}

ALIASES = {
    "情感驱动型": "emotional",
    "emotional": "emotional",
    "emotional driven": "emotional",
    "安全感驱动型": "security",
    "security": "security",
    "security driven": "security",
    "体验驱动型": "experience",
    "experience": "experience",
    "experience driven": "experience",
    "价值驱动型": "value",
    "value": "value",
    "value driven": "value",
    "惯性驱动型": "passive",
    "passive": "passive",
    "passive driven": "passive",
}


class ArchetypeEngine:
    def __init__(self, preset_dir: Path) -> None:
        self.preset_dir = preset_dir

    def normalize_archetype(self, archetype: str) -> str:
        key = archetype.strip().lower()
        return ALIASES.get(archetype.strip(), ALIASES.get(key, "experience"))

    def load_preset(self, archetype: str) -> Dict[str, Any]:
        canonical = self.normalize_archetype(archetype)
        filename = PRESET_FILE_MAP[canonical]
        path = self.preset_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Preset file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data["canonical_archetype"] = canonical
        return data

    def build_profile(self, archetype: str, overrides: Dict[str, Any] | None = None) -> RelationshipProfile:
        preset = self.load_preset(archetype)
        profile = RelationshipProfile(
            archetype=preset.get("display_name", archetype),
            attachment_style=preset.get("attachment_style", "Secure"),
            mbti=preset.get("mbti", "ENFP"),
            relationship_stage=preset.get("relationship_stage", "暧昧期"),
        )
        overrides = overrides or {}
        for key, value in overrides.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        return profile

    def initial_state(self, archetype: str, overrides: Dict[str, Any] | None = None) -> CoreState:
        preset = self.load_preset(archetype)
        baseline = preset.get("baseline_state", {})
        state = CoreState(
            favorability=float(baseline.get("favorability", 20)),
            tension=float(baseline.get("tension", 12)),
            neediness=float(baseline.get("neediness", 5)),
            frame_control=float(baseline.get("frame_control", 10)),
            exploration=float(baseline.get("exploration", 30)),
            defense_level=float(baseline.get("defense_level", 12)),
            propulsion=float(baseline.get("propulsion", 8)),
            attachment_activation=float(baseline.get("attachment_activation", 10)),
            trauma_level=float(baseline.get("trauma_level", 14)),
            push_pull_sensitivity=float(baseline.get("push_pull_sensitivity", 26)),
        ).normalize()

        overrides = overrides or {}
        for key, value in overrides.items():
            if hasattr(state, key) and value is not None:
                setattr(state, key, float(value))
        return state.normalize()
