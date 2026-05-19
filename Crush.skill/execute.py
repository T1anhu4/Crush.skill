#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from engines.archetype_engine import ArchetypeEngine
from engines.dialogue_analyzer import analyze_text
from engines.memory_backend import HybridMemoryBackend
from engines.reality_import_engine import RealityImportEngine
from engines.replay_engine import ReplayEngine
from engines.state_engine import StateEngine
from engines.types import CoreState, RelationshipProfile

ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "prompts" / "npc_runtime.txt"


class CrushSkillRuntime:
    def __init__(self) -> None:
        self.archetypes = ArchetypeEngine(ROOT / "presets")
        self.state_engine = StateEngine()
        self.memory = HybridMemoryBackend(ROOT / "data")
        self.reality_import = RealityImportEngine()
        self.replay = ReplayEngine()
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    def run(self, action: str, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = (action or "").strip().lower()

        if action == "quick_start":
            return self.quick_start(session_id, payload)
        if action == "custom_sandbox":
            return self.custom_sandbox(session_id, payload)
        if action == "reality_import":
            return self.reality_import_mode(session_id, payload)
        if action == "chat_turn":
            return self.chat_turn(session_id, payload)
        if action == "postmortem":
            return self.postmortem(session_id)
        if action == "timeline_append":
            return self.timeline_append(session_id, payload)
        if action == "dashboard":
            return self.dashboard(session_id)

        raise ValueError(f"Unsupported action: {action}")

    def quick_start(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = payload.get("config", {})
        archetype = config.get("relationship_archetype") or config.get("archetype") or "experience"
        profile_overrides = {
            "gender": config.get("gender"),
            "age": config.get("age"),
            "relationship_stage": config.get("relationship_stage"),
            "mbti": config.get("mbti"),
            "attachment_style": config.get("attachment_style"),
        }
        profile = self.archetypes.build_profile(archetype, overrides=profile_overrides)
        state = self.archetypes.initial_state(archetype)
        canonical = self.archetypes.normalize_archetype(archetype)

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), canonical)
        self.memory.sqlite.append_timeline_event(
            session_id=session_id,
            event_type="session_started",
            summary=f"Session started with archetype={profile.archetype}",
            payload={"mode": "quick_start", "canonical_archetype": canonical},
        )
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True,
            "action": "quick_start",
            "session_id": session_id,
            "profile": profile.to_dict(),
            "canonical_archetype": canonical,
            "state": state.to_dict(),
            "dashboard": self._dashboard_from_state(state.to_dict(), {}),
            "runtime_prompt": self._build_runtime_prompt(profile, state, session_id, ""),
            "memory_backend": self.memory.status.to_dict(),
        }

    def custom_sandbox(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = payload.get("config", {})
        archetype = config.get("relationship_archetype") or config.get("archetype") or "experience"

        profile_overrides = {
            "gender": config.get("gender"),
            "age": config.get("age"),
            "relationship_stage": config.get("relationship_stage"),
            "mbti": config.get("mbti"),
            "attachment_style": config.get("attachment_style"),
        }
        profile = self.archetypes.build_profile(archetype, overrides=profile_overrides)
        canonical = self.archetypes.normalize_archetype(archetype)

        state = self.archetypes.initial_state(
            archetype,
            overrides={
                "favorability": config.get("favorability"),
                "tension": config.get("tension"),
                "neediness": config.get("neediness"),
                "exploration": config.get("exploration"),
                "frame_control": config.get("frame_control"),
                "defense_level": config.get("defense_level"),
                "trauma_level": config.get("trauma_level"),
                "push_pull_sensitivity": config.get("push_pull_sensitivity"),
            },
        )

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), canonical)
        self.memory.sqlite.append_timeline_event(
            session_id=session_id,
            event_type="session_started",
            summary=f"Custom sandbox started: {profile.archetype}",
            payload={"mode": "custom_sandbox", "canonical_archetype": canonical},
        )
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True,
            "action": "custom_sandbox",
            "session_id": session_id,
            "profile": profile.to_dict(),
            "canonical_archetype": canonical,
            "state": state.to_dict(),
            "dashboard": self._dashboard_from_state(state.to_dict(), {}),
            "runtime_prompt": self._build_runtime_prompt(profile, state, session_id, ""),
            "memory_backend": self.memory.status.to_dict(),
        }

    def reality_import_mode(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        source_text = payload.get("source_text", "")
        if not source_text.strip():
            raise ValueError("reality_import requires payload.source_text")

        seed_profile = payload.get("profile", {})
        result = self.reality_import.import_from_text(seed_profile, source_text)

        self.memory.sqlite.upsert_session(
            session_id,
            result.profile.to_dict(),
            result.state.to_dict(),
            result.canonical_archetype,
        )
        self.memory.append_episode(
            session_id=session_id,
            role="import",
            content=source_text[:1000],
            tags=["reality_import"],
            meta={"mode": "reality_import"},
        )
        self.memory.sqlite.append_timeline_event(
            session_id=session_id,
            event_type="reality_import",
            summary="完成现实关系文本导入并重建人格",
            payload=result.evidence,
        )
        self.memory.sqlite.append_state_snapshot(
            session_id=session_id,
            state=result.state.to_dict(),
            delta={},
            tags=["reality_import"],
            note="Reality Import 初始状态",
        )
        self.memory.sqlite.update_summary(session_id)

        return {
            "success": True,
            "action": "reality_import",
            "session_id": session_id,
            "profile": result.profile.to_dict(),
            "canonical_archetype": result.canonical_archetype,
            "state": result.state.to_dict(),
            "evidence": result.evidence,
            "dashboard": self._dashboard_from_state(result.state.to_dict(), {}),
            "runtime_prompt": self._build_runtime_prompt(result.profile, result.state, session_id, source_text),
            "memory_backend": self.memory.status.to_dict(),
        }

    def chat_turn(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message", "").strip()
        if not message:
            raise ValueError("chat_turn requires payload.message")

        session = self.memory.sqlite.load_session(session_id)
        if not session:
            boot = self.quick_start(session_id, {"config": {"archetype": "experience"}})
            session = self.memory.sqlite.load_session(session_id)
            assert session is not None
            boot_note = "Session auto-created via quick_start(experience)"
        else:
            boot_note = ""

        profile = RelationshipProfile(**session["profile"])
        state = CoreState.from_dict(session["state"])
        canonical = session["canonical_archetype"]

        analysis = analyze_text(message)
        calculated = self.state_engine.apply_turn(state, profile, canonical, analysis)

        self.memory.append_episode(
            session_id=session_id,
            role="user",
            content=message,
            tags=calculated["tags"],
            meta={"analysis": calculated["analysis"]},
        )

        npc_reply = payload.get("npc_reply", "").strip()
        if npc_reply:
            self.memory.append_episode(
                session_id=session_id,
                role="npc",
                content=npc_reply,
                tags=calculated["tags"],
                meta={},
            )

        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), calculated["state"], canonical)
        note_parts = [calculated["defense"]["reason"]] + analysis.notes
        note = " | ".join([p for p in note_parts if p])
        self.memory.sqlite.append_state_snapshot(
            session_id=session_id,
            state=calculated["state"],
            delta=calculated["delta"],
            tags=calculated["tags"],
            note=note,
        )

        for tag in calculated["tags"]:
            self.memory.sqlite.append_timeline_event(
                session_id=session_id,
                event_type=tag,
                summary=f"触发事件: {tag}",
                payload={"delta": calculated["delta"], "analysis": calculated["analysis"]},
            )

        summary = self.memory.sqlite.update_summary(session_id)
        memory_context = self.memory.sqlite.build_memory_context(session_id, query=message, limit=6)

        runtime_prompt = self._build_runtime_prompt(
            profile=profile,
            state=CoreState.from_dict(calculated["state"]),
            session_id=session_id,
            user_message=message,
            memory_context=memory_context,
        )

        return {
            "success": True,
            "action": "chat_turn",
            "session_id": session_id,
            "boot_note": boot_note,
            "state": calculated["state"],
            "delta": calculated["delta"],
            "defense": calculated["defense"],
            "analysis": calculated["analysis"],
            "tags": calculated["tags"],
            "relationship_vector": calculated["relationship_vector"],
            "dashboard": self._dashboard_from_state(calculated["state"], calculated["delta"], calculated["tags"]),
            "memory_context": memory_context,
            "memory_summary": summary,
            "runtime_prompt": runtime_prompt,
            "memory_backend": self.memory.status.to_dict(),
        }

    def postmortem(self, session_id: str) -> Dict[str, Any]:
        report = self.replay.build_postmortem(self.memory.sqlite, session_id=session_id)
        markdown = self._render_report_markdown(report)
        return {
            "success": True,
            "action": "postmortem",
            "session_id": session_id,
            "report": report,
            "markdown": markdown,
        }

    def timeline_append(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type = payload.get("event_type", "manual_event")
        summary = payload.get("summary", "")
        if not summary:
            raise ValueError("timeline_append requires payload.summary")
        extra = payload.get("payload", {})
        self.memory.sqlite.append_timeline_event(session_id, event_type, summary, extra)
        return {
            "success": True,
            "action": "timeline_append",
            "session_id": session_id,
            "event_type": event_type,
            "summary": summary,
        }

    def dashboard(self, session_id: str) -> Dict[str, Any]:
        session = self.memory.sqlite.load_session(session_id)
        if not session:
            raise ValueError(f"session not found: {session_id}")
        history = self.memory.sqlite.get_state_history(session_id, limit=1)
        delta = history[0]["delta"] if history else {}
        tags = history[0]["tags"] if history else []
        return {
            "success": True,
            "action": "dashboard",
            "session_id": session_id,
            "profile": session["profile"],
            "state": session["state"],
            "dashboard": self._dashboard_from_state(session["state"], delta, tags),
            "memory_backend": self.memory.status.to_dict(),
        }

    def _dashboard_from_state(self, state: Dict[str, Any], delta: Dict[str, Any], tags: list[str] | None = None) -> Dict[str, Any]:
        tags = tags or []
        return {
            "cards": {
                "Favorability": round(float(state.get("favorability", 0)), 2),
                "Tension": round(float(state.get("tension", 0)), 2),
                "Neediness": round(float(state.get("neediness", 0)), 2),
                "Defense": round(float(state.get("defense_level", 0)), 2),
                "Exploration": round(float(state.get("exploration", 0)), 2),
                "FrameControl": round(float(state.get("frame_control", 0)), 2),
            },
            "delta": delta,
            "events": tags,
        }

    def _build_runtime_prompt(
        self,
        profile: RelationshipProfile,
        state: CoreState,
        session_id: str,
        user_message: str,
        memory_context: Dict[str, Any] | None = None,
    ) -> str:
        memory_context = memory_context or self.memory.sqlite.build_memory_context(session_id, query=user_message or "关系回顾", limit=4)

        snippets = memory_context.get("snippets", [])
        snippet_text = "\n".join(f"- {line}" for line in snippets[:5]) if snippets else "- 暂无"

        return self.prompt_template.format(
            archetype=profile.archetype,
            attachment_style=profile.attachment_style,
            mbti=profile.mbti,
            favorability=round(state.favorability, 2),
            tension=round(state.tension, 2),
            neediness=round(state.neediness, 2),
            exploration=round(state.exploration, 2),
            defense=round(state.defense_level, 2),
            frame=round(state.frame_control, 2),
            memory_summary=memory_context.get("summary", "暂无记忆摘要"),
            memory_snippets=snippet_text,
        )

    def _render_report_markdown(self, report: Dict[str, Any]) -> str:
        diagnostics = report.get("diagnostics", {})
        frame = diagnostics.get("frame_collapses", [])
        peak = diagnostics.get("attraction_peaks", [])
        defense = diagnostics.get("defense_triggers", [])

        def _lines(items: list[Dict[str, Any]]) -> str:
            if not items:
                return "- 暂无"
            rows = []
            for item in items:
                rows.append(f"- {item.get('created_at', '')} | {item.get('why', '')}")
            return "\n".join(rows)

        return (
            "# Relationship Combat Replay\n\n"
            "## 框架崩塌点\n"
            f"{_lines(frame)}\n\n"
            "## 吸引力峰值\n"
            f"{_lines(peak)}\n\n"
            "## 防御触发点\n"
            f"{_lines(defense)}\n\n"
            "## 总结建议\n"
            f"{report.get('narrative', '')}\n"
        )


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
    parser = argparse.ArgumentParser(description="Crush Xiehou Relationship Simulation Skill")
    parser.add_argument("--action", required=True)
    parser.add_argument("--session-id", default="default")
    parser.add_argument("--payload-json", help="Raw JSON payload")
    parser.add_argument("--config-json", help="JSON for mode configuration")
    parser.add_argument("--profile-json", help="JSON profile seed for reality import")
    parser.add_argument("--source-text", help="Reality import source text")
    parser.add_argument("--source-text-file", help="Path to source text file")
    parser.add_argument("--message", help="User message for chat_turn")
    parser.add_argument("--npc-reply", help="Optional generated NPC reply to persist")
    parser.add_argument("--pretty", action="store_true")
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
        error = {
            "success": False,
            "action": args.action,
            "session_id": args.session_id,
            "error": str(exc),
        }
        if args.pretty:
            print(json.dumps(error, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(error, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
