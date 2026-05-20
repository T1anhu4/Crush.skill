#!/usr/bin/env python3
"""
Crush.skill — Relationship Persona Simulation Engine.

Actions:
  quick_start       — Start a new session from a preset archetype
  custom_sandbox    — Build a fully custom persona and start simulation
  reality_import    — Import real chat logs, reconstruct personality + state
  chat_turn         — Process one message turn, update state, generate NPC prompt
  postmortem        — Full relationship combat replay + diagnostic report
  timeline_append   — Manually add an event to the timeline
  dashboard         — View current relationship state dashboard
  list_sessions     — List all saved sessions
  delete_session    — Delete a session
  let_go            — Ritual: delete with a closure message

Compatible with: Claude Code, OpenClaw, QwenPaw, WorkBuddy
Follows Agent Skills spec (agentskills.io)
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from engines.persona_engine import PersonaEngine
from engines.dialogue_analyzer import analyze_text
from engines.memory_backend import HybridMemoryBackend
from engines.chat_import import ChatImporter
from engines.reality_import_engine import RealityImportEngine
from engines.replay_engine import ReplayEngine
from engines.state_engine import StateEngine
from engines.types import CoreState, RelationshipProfile

ROOT = Path(__file__).resolve().parent


class CrushSkillRuntime:
    def __init__(self) -> None:
        self.persona = PersonaEngine(ROOT / "presets")
        self.state_engine = StateEngine()
        self.memory = HybridMemoryBackend(ROOT / "data")
        self.reality_import = RealityImportEngine()
        self.chat_importer = ChatImporter()
        self.replay = ReplayEngine()

    def run(self, action: str, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = (action or "").strip().lower()

        actions = {
            "quick_start": self.quick_start,
            "custom_sandbox": self.custom_sandbox,
            "reality_import": self.reality_import_mode,
            "chat_import": self.chat_import_mode,
            "chat_turn": self.chat_turn,
            "postmortem": self.postmortem,
            "timeline_append": self.timeline_append,
            "dashboard": self.dashboard,
            "list_sessions": self.list_sessions,
            "delete_session": self.delete_session,
            "let_go": self.let_go,
        }

        if action not in actions:
            raise ValueError(f"Unsupported action: {action}. Available: {', '.join(actions.keys())}")

        return actions[action](session_id, payload)

    # ── Actions ──────────────────────────────────────────────────

    def quick_start(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = payload.get("config", {})
        archetype = config.get("archetype") or config.get("relationship_archetype") or "experience"

        # Build full 5-layer persona from preset
        persona_obj = self.persona.from_preset(archetype, overrides={
            "identity": {
                "name": config.get("name"),
                "gender": config.get("gender"),
                "age": config.get("age"),
                "mbti": config.get("mbti"),
            },
            "emotional": {
                "attachment_style": config.get("attachment_style"),
            },
            "relational": {
                "relationship_stage": config.get("relationship_stage"),
            },
        })

        # Build state from preset baseline
        state = self._initial_state_from_preset(archetype, config)
        canonical = self.persona._normalize_archetype(archetype)
        profile = RelationshipProfile(
            archetype=archetype,
            attachment_style=persona_obj.emotional.attachment_style,
            mbti=persona_obj.identity.mbti,
            gender=persona_obj.identity.gender,
            age=persona_obj.identity.age,
            relationship_stage=persona_obj.relational.relationship_stage,
        )

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), canonical)
        self.memory.sqlite.append_timeline_event(session_id, "session_started",
            f"Quick start: {archetype} ({persona_obj.identity.name or 'unnamed'})",
            {"mode": "quick_start", "canonical_archetype": canonical})
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True, "action": "quick_start", "session_id": session_id,
            "persona": persona_obj.to_dict(),
            "profile": profile.to_dict(), "canonical_archetype": canonical,
            "state": state.to_dict(),
            "dashboard": self._dashboard(state.to_dict(), {}),
            "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, state.to_dict(), {}, ""),
            "memory_backend": self.memory.status.to_dict(),
        }

    def custom_sandbox(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = payload.get("config", {})
        persona_obj = self.persona.from_custom(config.get("persona", config))

        archetype = config.get("archetype", "experience")
        state = self._initial_state_from_preset(archetype, config)
        canonical = self.persona._normalize_archetype(archetype)

        profile = RelationshipProfile(
            archetype=archetype,
            attachment_style=persona_obj.emotional.attachment_style,
            mbti=persona_obj.identity.mbti,
            gender=persona_obj.identity.gender,
            age=persona_obj.identity.age,
            relationship_stage=persona_obj.relational.relationship_stage,
        )

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), canonical)
        self.memory.sqlite.append_timeline_event(session_id, "session_started",
            f"Custom sandbox: {persona_obj.identity.name or 'custom'}",
            {"mode": "custom_sandbox"})
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True, "action": "custom_sandbox", "session_id": session_id,
            "persona": persona_obj.to_dict(), "profile": profile.to_dict(),
            "canonical_archetype": canonical, "state": state.to_dict(),
            "dashboard": self._dashboard(state.to_dict(), {}),
            "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, state.to_dict(), {}, ""),
            "memory_backend": self.memory.status.to_dict(),
        }

    def reality_import_mode(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        source_text = payload.get("source_text", "")
        if not source_text.strip():
            raise ValueError("reality_import requires payload.source_text")

        seed_profile = payload.get("profile", {})
        result = self.reality_import.import_from_text(seed_profile, source_text)

        self.memory.sqlite.upsert_session(
            session_id, result.profile.to_dict(), result.state.to_dict(), result.canonical_archetype)
        self.memory.append_episode(session_id, "import", source_text[:1000], tags=["reality_import"],
            meta={"mode": "reality_import"})
        self.memory.sqlite.append_timeline_event(session_id, "reality_import",
            "完成现实关系文本导入并重建人格", result.evidence)
        self.memory.sqlite.append_state_snapshot(session_id, result.state.to_dict(), {}, ["reality_import"],
            "Reality Import 初始状态")
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True, "action": "reality_import", "session_id": session_id,
            "profile": result.profile.to_dict(), "canonical_archetype": result.canonical_archetype,
            "state": result.state.to_dict(), "evidence": result.evidence,
            "dashboard": self._dashboard(result.state.to_dict(), {}),
            "runtime_prompt": self._build_legacy_prompt(result.profile, result.state, session_id, source_text),
            "memory_backend": self.memory.status.to_dict(),
        }

    def chat_import_mode(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-format chat record import → full persona + state reconstruction."""
        source_text = payload.get("source_text", "")
        if not source_text.strip():
            raise ValueError("chat_import requires payload.source_text with chat records")

        # Parse and analyze
        messages = self.chat_importer.detect_and_parse(source_text)
        analysis = self.chat_importer.analyze(messages)

        # Build persona from inferred traits
        persona_dict = {
            "identity": {
                "name": payload.get("config", {}).get("name", ""),
                "gender": payload.get("config", {}).get("gender", "female"),
                "age": payload.get("config", {}).get("age", 24),
                "mbti": analysis.inferred_mbti,
                "big_five": analysis.inferred_big_five,
                "life_stage": "early_career",
                "core_values": analysis.key_topics[:3],
                "self_perception": f"从{analysis.total_messages}条消息推断的人格画像",
            },
            "expression": {
                "signature_phrases": analysis.signature_phrases,
                "filler_words": analysis.filler_words,
                "emoji_style": analysis.emoji_style,
                "emoji_favorites": analysis.emoji_favorites,
                "sentence_structure": analysis.sentence_structure,
                "humor_style": analysis.humor_style,
                "avg_message_length_words": int(analysis.avg_message_length),
                "reply_latency_pattern": "minutes" if analysis.avg_reply_time_minutes < 10 else "hours" if analysis.avg_reply_time_minutes < 120 else "days",
            },
            "emotional": {
                "attachment_style": analysis.inferred_attachment,
                "love_language": analysis.inferred_love_language,
                "trauma_sensitivity": 0.15,
                "mood_volatility": 0.3,
            },
            "relational": {
                "relationship_stage": analysis.relationship_phase,
                "power_dynamic": "balanced",
            },
        }

        persona_obj = self.persona.from_custom(persona_dict)

        # Build state from estimates
        state = CoreState(
            favorability=analysis.estimated_favorability,
            tension=analysis.estimated_tension,
            neediness=5.0,
            frame_control=20.0,
            exploration=30.0,
            defense_level=20.0,
            propulsion=15.0,
            attachment_activation=15.0,
            trauma_level=14.0,
            push_pull_sensitivity=20.0,
        ).normalize()

        archetype = analysis.inferred_archetype
        profile = RelationshipProfile(
            archetype=archetype,
            attachment_style=analysis.inferred_attachment,
            mbti=analysis.inferred_mbti,
            gender=persona_obj.identity.gender,
            age=persona_obj.identity.age,
            relationship_stage=analysis.relationship_phase,
        )

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), archetype)
        self.memory.sqlite.append_timeline_event(session_id, "chat_import",
            f"从 {analysis.total_messages} 条聊天记录导入", analysis.to_dict())
        self.memory.sqlite.append_state_snapshot(session_id, state.to_dict(), {},
            ["chat_import"], f"导入: {analysis.total_messages}条消息, 阶段={analysis.relationship_phase}")
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True, "action": "chat_import", "session_id": session_id,
            "analysis": analysis.to_dict(),
            "persona": persona_obj.to_dict(),
            "profile": profile.to_dict(),
            "state": state.to_dict(),
            "dashboard": self._dashboard(state.to_dict(), {}),
            "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, state.to_dict(), {}, ""),
            "memory_backend": self.memory.status.to_dict(),
        }

    def chat_turn(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message", "").strip()
        if not message:
            raise ValueError("chat_turn requires payload.message")

        session = self.memory.sqlite.load_session(session_id)
        boot_note = ""
        if not session:
            boot = self.quick_start(session_id, {"config": {"archetype": "experience"}})
            session = self.memory.sqlite.load_session(session_id)
            assert session is not None
            boot_note = "Session auto-created via quick_start(experience)"

        profile = RelationshipProfile(**session["profile"])
        state = CoreState.from_dict(session["state"])
        canonical = session["canonical_archetype"]

        # LLM-powered or enhanced local analysis
        analysis = analyze_text(message)
        calculated = self.state_engine.apply_turn(state, profile, canonical, analysis, session_id=session_id)

        # Store episode
        self.memory.append_episode(session_id, "user", message, tags=calculated["tags"],
            meta={"analysis": calculated["analysis"]})

        npc_reply = payload.get("npc_reply", "").strip()
        if npc_reply:
            self.memory.append_episode(session_id, "npc", npc_reply, tags=calculated["tags"], meta={})

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), calculated["state"], canonical)
        note = " | ".join(p for p in [calculated["defense"]["reason"]] + analysis.notes if p)
        self.memory.sqlite.append_state_snapshot(session_id, calculated["state"], calculated["delta"],
            calculated["tags"], note)

        for tag in calculated["tags"]:
            self.memory.sqlite.append_timeline_event(session_id, tag, f"触发: {tag}",
                {"delta": calculated["delta"], "analysis": calculated["analysis"]})

        self.memory.sqlite.update_summary(session_id)
        memory_ctx = self.memory.sqlite.build_memory_context(session_id, query=message, limit=6)

        # Build persona for runtime prompt
        persona_obj = self._load_persona_for_session(session)
        runtime_prompt = self.persona.build_runtime_prompt(
            persona_obj, CoreState.from_dict(calculated["state"]).to_dict(), memory_ctx, message)

        return {
            "success": True, "action": "chat_turn", "session_id": session_id,
            "boot_note": boot_note, "state": calculated["state"], "delta": calculated["delta"],
            "defense": calculated["defense"], "analysis": calculated["analysis"],
            "tags": calculated["tags"], "relationship_vector": calculated["relationship_vector"],
            "dashboard": self._dashboard(calculated["state"], calculated["delta"], calculated["tags"]),
            "memory_context": memory_ctx, "memory_summary": self.memory.sqlite.get_summary(session_id),
            "runtime_prompt": runtime_prompt,
            "memory_backend": self.memory.status.to_dict(),
        }

    def postmortem(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        report = self.replay.build_postmortem(self.memory.sqlite, session_id=session_id)
        markdown = self._render_report(report)
        return {"success": True, "action": "postmortem", "session_id": session_id,
                "report": report, "markdown": markdown}

    def timeline_append(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type = payload.get("event_type", "manual_event")
        summary = payload.get("summary", "")
        if not summary:
            raise ValueError("timeline_append requires payload.summary")
        self.memory.sqlite.append_timeline_event(session_id, event_type, summary, payload.get("payload", {}))
        return {"success": True, "action": "timeline_append", "session_id": session_id,
                "event_type": event_type, "summary": summary}

    def dashboard(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        session = self.memory.sqlite.load_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        history = self.memory.sqlite.get_state_history(session_id, limit=1)
        delta = history[0]["delta"] if history else {}
        tags = history[0]["tags"] if history else []
        return {"success": True, "action": "dashboard", "session_id": session_id,
                "profile": session["profile"], "state": session["state"],
                "dashboard": self._dashboard(session["state"], delta, tags),
                "memory_backend": self.memory.status.to_dict()}

    def list_sessions(self, session_id: str = "", payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """List all saved sessions."""
        sessions = self.memory.sqlite._list_sessions()
        return {"success": True, "action": "list_sessions", "sessions": sessions}

    def delete_session(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Delete a session permanently."""
        self.memory.sqlite._delete_session(session_id)
        return {"success": True, "action": "delete_session", "session_id": session_id,
                "message": f"Session '{session_id}' deleted."}

    def let_go(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Ritual closure: delete the session with a meaningful goodbye."""
        session = self.memory.sqlite.load_session(session_id)
        name = ""
        if session:
            profile = session.get("profile", {})
            name = profile.get("archetype", session_id)

        self.memory.sqlite._delete_session(session_id)

        message = (
            f"你已经放下了「{name}」。\n\n"
            "每一段相遇都有它的意义。它教会了你一些东西，让你更了解自己，"
            "更知道什么是你想要的，什么是你不能接受的。\n\n"
            "带着这些学到的东西，继续往前走吧。"
        )
        return {"success": True, "action": "let_go", "session_id": session_id, "message": message}

    # ── Helpers ──────────────────────────────────────────────────

    def _initial_state_from_preset(self, archetype: str, config: Dict[str, Any]) -> CoreState:
        """Get initial state from preset + optional overrides."""
        import yaml
        canonical = self.persona._normalize_archetype(archetype)
        preset_path = ROOT / "presets" / f"{canonical}.yaml"
        if preset_path.exists():
            with open(preset_path, "r") as f:
                preset = yaml.safe_load(f) or {}
            baseline = preset.get("baseline_state", {})
        else:
            baseline = {}

        state = CoreState(
            favorability=float(config.get("favorability", baseline.get("favorability", 20))),
            tension=float(config.get("tension", baseline.get("tension", 12))),
            neediness=float(config.get("neediness", baseline.get("neediness", 5))),
            frame_control=float(config.get("frame_control", baseline.get("frame_control", 10))),
            exploration=float(config.get("exploration", baseline.get("exploration", 30))),
            defense_level=float(config.get("defense_level", baseline.get("defense_level", 12))),
            propulsion=float(config.get("propulsion", baseline.get("propulsion", 8))),
            attachment_activation=float(config.get("attachment_activation", baseline.get("attachment_activation", 10))),
            trauma_level=float(config.get("trauma_level", baseline.get("trauma_level", 14))),
            push_pull_sensitivity=float(config.get("push_pull_sensitivity", baseline.get("push_pull_sensitivity", 26))),
        ).normalize()
        return state

    def _load_persona_for_session(self, session: Dict[str, Any]) -> Any:
        """Reconstruct Persona from session data (best-effort)."""
        from engines.persona_engine import Persona
        profile = session.get("profile", {})
        canonical = session.get("canonical_archetype", "experience")
        try:
            return self.persona.from_preset(profile.get("archetype", canonical))
        except Exception:
            return self.persona.from_preset("experience")

    def _dashboard(self, state: Dict[str, Any], delta: Dict[str, Any], tags: list | None = None) -> Dict[str, Any]:
        tags = tags or []
        return {
            "cards": {
                "Favorability": round(float(state.get("favorability", 0)), 2),
                "Tension": round(float(state.get("tension", 0)), 2),
                "Neediness": round(float(state.get("neediness", 0)), 2),
                "Defense": round(float(state.get("defense_level", 0)), 2),
                "Exploration": round(float(state.get("exploration", 0)), 2),
                "FrameControl": round(float(state.get("frame_control", 0)), 2),
                "Propulsion": round(float(state.get("propulsion", 0)), 2),
                "AttachmentActivation": round(float(state.get("attachment_activation", 0)), 2),
            },
            "delta": delta,
            "events": tags,
        }

    def _build_legacy_prompt(self, profile: RelationshipProfile, state: CoreState, session_id: str, user_msg: str) -> str:
        """Fallback prompt builder for backward compatibility."""
        prompt_path = ROOT / "prompts" / "npc_runtime.txt"
        if prompt_path.exists():
            template = prompt_path.read_text(encoding="utf-8")
            mem_ctx = self.memory.sqlite.build_memory_context(session_id, query=user_msg or "关系回顾", limit=4)
            snippets = mem_ctx.get("snippets", [])
            snippet_text = "\n".join(f"- {l}" for l in snippets[:5]) if snippets else "- 暂无"
            return template.format(
                archetype=profile.archetype,
                attachment_style=profile.attachment_style,
                mbti=profile.mbti,
                favorability=round(state.favorability, 2),
                tension=round(state.tension, 2),
                neediness=round(state.neediness, 2),
                exploration=round(state.exploration, 2),
                defense=round(state.defense_level, 2),
                frame=round(state.frame_control, 2),
                memory_summary=mem_ctx.get("summary", "暂无记忆摘要"),
                memory_snippets=snippet_text,
            )
        return ""

    def _render_report(self, report: Dict[str, Any]) -> str:
        diagnostics = report.get("diagnostics", {})
        frame = diagnostics.get("frame_collapses", [])
        peak = diagnostics.get("attraction_peaks", [])
        defense = diagnostics.get("defense_triggers", [])

        def _lines(items) -> str:
            if not items: return "- 暂无"
            return "\n".join(f"- {i.get('created_at','')} | {i.get('why','')}" for i in items)

        return (
            "# 🎯 Relationship Combat Replay\n\n"
            "## 💔 框架崩塌点\n" + _lines(frame) + "\n\n"
            "## ⚡ 吸引力峰值\n" + _lines(peak) + "\n\n"
            "## 🛡️ 防御触发点\n" + _lines(defense) + "\n\n"
            "## 📝 总结\n" + report.get("narrative", "")
        )


# ── CLI ──────────────────────────────────────────────────────────

def _load_payload(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if args.payload_json:
        payload.update(json.loads(args.payload_json))
    if args.config_json:
        payload["config"] = json.loads(args.config_json)
    if args.profile_json:
        payload["profile"] = json.loads(args.profile_json)
    if args.source_text:
        payload["source_text"] = args.source_text
    if args.source_text_file:
        payload["source_text"] = Path(args.source_text_file).read_text(encoding="utf-8")
    if args.message:
        payload["message"] = args.message
    if args.npc_reply:
        payload["npc_reply"] = args.npc_reply
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Crush.skill — Relationship Persona Simulation Engine")
    parser.add_argument("--action", required=True, help="Action to execute")
    parser.add_argument("--session-id", default="default", help="Session identifier")
    parser.add_argument("--payload-json", help="Raw JSON payload")
    parser.add_argument("--config-json", help="JSON for configuration")
    parser.add_argument("--profile-json", help="JSON profile seed")
    parser.add_argument("--source-text", help="Source text for import")
    parser.add_argument("--source-text-file", help="Path to source text file")
    parser.add_argument("--message", help="User message for chat_turn")
    parser.add_argument("--npc-reply", help="NPC reply to persist")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    runtime = CrushSkillRuntime()
    payload = _load_payload(args)

    try:
        result = runtime.run(action=args.action, session_id=args.session_id, payload=payload)
        if args.pretty:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        error = {"success": False, "action": args.action, "session_id": args.session_id, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
