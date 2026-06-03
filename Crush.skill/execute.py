#!/usr/bin/env python3
"""
Crush.skill v2.4.0 — Relationship Persona Simulation Engine.

Slash commands (use directly in Claude Code / OpenClaw / QwenPaw):
  /start-crush [archetype]  — Quick start with a preset personality
  /custom-crush             — Build a fully custom persona
  /import-chats             — Import chat records (WeChat/WhatsApp/QQ/CSV)
  /chat [message]           — Send a message and see state changes
  /crush-dashboard          — View relationship state dashboard
  /crush-postmortem         — Relationship combat replay & diagnostics
  /list-crushes             — List all saved sessions
  /let-go [session]         — Ritual closure
  /crush-llm [api_key]      — Configure LLM for dialogue analysis

Auto-installs dependencies on first run. Platform LLM auto-detected.
Compatible: Claude Code, OpenClaw, QwenPaw, WorkBuddy, Codex, Cursor
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import importlib.util
import subprocess
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("CRUSH_DATA_DIR", str(ROOT / "data"))).expanduser()

# ── Auto-install dependencies on first run ─────────────────────
def _ensure_deps():
    """Install required packages if missing. Runs once, silently."""
    marker = DATA_DIR / ".deps_installed"
    if marker.exists():
        return

    missing = []
    for pkg in ["yaml"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    # mem0 is optional. Do not import it here: some agents run in a
    # restricted HOME and mem0's import side effects can write there.
    if os.environ.get("CRUSH_AUTO_INSTALL_MEM0", "").lower() in {"1", "true", "yes"} and not importlib.util.find_spec("mem0"):
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "mem0ai", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass  # mem0 is optional enhancement

    if missing:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing + ["-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass  # Continue without — will fail with clear error later

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()


_ensure_deps()

# ── Imports (after deps check) ──────────────────────────────────
from engines.persona_engine import PersonaEngine
from engines.dialogue_analyzer import analyze_text
from engines.memory_backend import HybridMemoryBackend
from engines.chat_import import ChatImporter
from engines.reality_import_engine import RealityImportEngine
from engines.replay_engine import ReplayEngine
from engines.state_engine import StateEngine
from engines.types import CoreState, RelationshipProfile


class CrushSkillRuntime:
    def __init__(self) -> None:
        self.persona = PersonaEngine(ROOT / "presets")
        self.state_engine = StateEngine()
        self.memory = HybridMemoryBackend(DATA_DIR)
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
            "record_reply": self.record_reply,
            "proactive_prompt": self.proactive_prompt,
            "postmortem": self.postmortem,
            "timeline_append": self.timeline_append,
            "dashboard": self.dashboard,
            "list_sessions": self.list_sessions,
            "delete_session": self.delete_session,
            "let_go": self.let_go,
            "configure_llm": self.configure_llm,
        }
        if action not in actions:
            raise ValueError(f"Unsupported action: {action}. Available: {', '.join(actions.keys())}")
        return actions[action](session_id, payload)

    # ── Slash Command: /start-crush [archetype] ────────────────────
    def quick_start(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = payload.get("config", {})
        archetype = config.get("archetype") or config.get("relationship_archetype") or "experience"
        persona_obj = self.persona.from_preset(archetype, overrides={
            "identity": {"name": config.get("name"), "gender": config.get("gender"),
                         "age": config.get("age"), "mbti": config.get("mbti")},
            "emotional": {"attachment_style": config.get("attachment_style")},
            "relational": {"relationship_stage": config.get("relationship_stage")},
        })
        state = self._initial_state_from_preset(archetype, config)
        canonical = self.persona._normalize_archetype(archetype)
        profile = RelationshipProfile(archetype=archetype,
            attachment_style=persona_obj.emotional.attachment_style,
            mbti=persona_obj.identity.mbti, gender=persona_obj.identity.gender,
            age=persona_obj.identity.age,
            relationship_stage=persona_obj.relational.relationship_stage)
        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), canonical, persona_obj.to_dict())
        self.memory.sqlite.append_timeline_event(session_id, "session_started",
            f"Quick start: {archetype} ({persona_obj.identity.name or 'unnamed'})",
            {"mode": "quick_start", "canonical_archetype": canonical})
        self.memory.sqlite.update_summary(session_id)
        return {"success": True, "action": "quick_start", "session_id": session_id,
                "persona": persona_obj.to_dict(), "profile": profile.to_dict(),
                "canonical_archetype": canonical, "state": state.to_dict(),
                "dashboard": self._dashboard(state.to_dict(), {}),
                "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, state.to_dict(), {}, ""),
                "memory_backend": self.memory.status.to_dict()}

    # ── Slash Command: /custom-crush ───────────────────────────────
    def custom_sandbox(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = payload.get("config", {})
        persona_obj = self.persona.from_custom(config.get("persona", config))
        archetype = config.get("archetype", "experience")
        state = self._initial_state_from_preset(archetype, config)
        canonical = self.persona._normalize_archetype(archetype)
        profile = RelationshipProfile(archetype=archetype,
            attachment_style=persona_obj.emotional.attachment_style,
            mbti=persona_obj.identity.mbti, gender=persona_obj.identity.gender,
            age=persona_obj.identity.age,
            relationship_stage=persona_obj.relational.relationship_stage)
        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), canonical, persona_obj.to_dict())
        self.memory.sqlite.append_timeline_event(session_id, "session_started",
            f"Custom sandbox: {persona_obj.identity.name or 'custom'}", {"mode": "custom_sandbox"})
        self.memory.sqlite.update_summary(session_id)
        return {"success": True, "action": "custom_sandbox", "session_id": session_id,
                "persona": persona_obj.to_dict(), "profile": profile.to_dict(),
                "canonical_archetype": canonical, "state": state.to_dict(),
                "dashboard": self._dashboard(state.to_dict(), {}),
                "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, state.to_dict(), {}, ""),
                "memory_backend": self.memory.status.to_dict()}

    # ── Slash Command: /import-chats ───────────────────────────────
    def chat_import_mode(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        source_text = payload.get("source_text", "")
        if not source_text.strip():
            raise ValueError("请提供聊天记录内容 (source_text)。你可以直接粘贴聊天记录，或指定文件路径 (source_text_file)。")
        messages = self.chat_importer.detect_and_parse(source_text)
        analysis = self.chat_importer.analyze(messages)
        persona_dict = {
            "identity": {
                "name": payload.get("config", {}).get("name", ""),
                "gender": payload.get("config", {}).get("gender", "female"),
                "age": payload.get("config", {}).get("age", 24),
                "mbti": analysis.inferred_mbti, "big_five": analysis.inferred_big_five,
                "life_stage": "early_career", "core_values": analysis.key_topics[:3],
                "self_perception": f"从{analysis.total_messages}条消息推断的人格画像",
            },
            "expression": {
                "signature_phrases": list(dict.fromkeys(analysis.signature_phrases + analysis.slang_hits))[:12],
                "filler_words": analysis.filler_words,
                "emoji_style": analysis.emoji_style,
                "emoji_favorites": analysis.emoji_favorites,
                "sentence_structure": analysis.sentence_structure,
                "humor_style": analysis.humor_style,
                "avg_message_length_words": int(analysis.avg_message_length),
                "reply_latency_pattern": "minutes" if analysis.avg_reply_time_minutes < 10 else "hours",
            },
            "emotional": {
                "attachment_style": analysis.inferred_attachment,
                "love_language": analysis.inferred_love_language,
                "vulnerability_triggers": analysis.boundary_phrases,
                "trauma_sensitivity": 0.15,
                "mood_volatility": 0.45 if analysis.sentiment_trend == "volatile" else 0.3,
                "stress_response": "withdraw" if analysis.boundary_phrases else "discuss",
            },
            "relational": {
                "relationship_stage": analysis.relationship_phase,
                "power_dynamic": "balanced",
                "inside_jokes": analysis.inside_jokes,
                "shared_experiences": analysis.shared_experiences,
                "their_view_of_you": analysis.their_view_of_you,
            },
            "hard_rules": {
                "max_message_length": max(12, min(120, int(analysis.avg_message_length * 1.4) or 80)),
                "double_text_tolerance": "low" if analysis.boundary_phrases else "medium",
            },
        }
        persona_obj = self.persona.from_custom(persona_dict)
        state = CoreState(favorability=analysis.estimated_favorability,
            tension=analysis.estimated_tension, neediness=5.0, frame_control=20.0,
            exploration=30.0, defense_level=20.0, propulsion=15.0,
            attachment_activation=15.0, trauma_level=14.0, push_pull_sensitivity=20.0).normalize()
        archetype = analysis.inferred_archetype
        profile = RelationshipProfile(archetype=archetype,
            attachment_style=analysis.inferred_attachment, mbti=analysis.inferred_mbti,
            gender=persona_obj.identity.gender, age=persona_obj.identity.age,
            relationship_stage=analysis.relationship_phase)
        self.memory.sqlite.upsert_session(session_id, profile.to_dict(), state.to_dict(), archetype, persona_obj.to_dict())
        for msg in messages[:300]:
            self.memory.append_episode(
                session_id,
                msg.sender,
                msg.content,
                tags=["chat_import"],
                meta={"timestamp": msg.timestamp, "original_line": msg.original_line},
            )
        self.memory.sqlite.append_timeline_event(session_id, "chat_import",
            f"从 {analysis.total_messages} 条聊天记录导入", analysis.to_dict())
        self.memory.sqlite.append_state_snapshot(session_id, state.to_dict(), {},
            ["chat_import"], f"导入: {analysis.total_messages}条消息")
        self.memory.sqlite.update_summary(session_id)
        return {"success": True, "action": "chat_import", "session_id": session_id,
                "analysis": analysis.to_dict(), "persona": persona_obj.to_dict(),
                "profile": profile.to_dict(), "state": state.to_dict(),
                "dashboard": self._dashboard(state.to_dict(), {}),
                "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, state.to_dict(), {}, ""),
                "memory_backend": self.memory.status.to_dict()}

    # ── Legacy reality_import ──────────────────────────────────────
    def reality_import_mode(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        source_text = payload.get("source_text", "")
        if not source_text.strip():
            raise ValueError("reality_import requires payload.source_text")
        seed_profile = payload.get("profile", {})
        result = self.reality_import.import_from_text(seed_profile, source_text)
        persona_obj = self.persona.from_preset(result.canonical_archetype, overrides={
            "identity": {
                "gender": result.profile.gender,
                "age": result.profile.age,
                "mbti": result.profile.mbti,
                "self_perception": "从现实关系文本推断的人格画像",
            },
            "emotional": {"attachment_style": result.profile.attachment_style},
            "relational": {"relationship_stage": result.profile.relationship_stage},
        })
        self.memory.sqlite.upsert_session(
            session_id,
            result.profile.to_dict(),
            result.state.to_dict(),
            result.canonical_archetype,
            persona_obj.to_dict(),
        )
        self.memory.append_episode(session_id, "import", source_text[:1000], tags=["reality_import"], meta={"mode": "reality_import"})
        self.memory.sqlite.append_timeline_event(session_id, "reality_import", "完成现实关系文本导入并重建人格", result.evidence)
        self.memory.sqlite.append_state_snapshot(session_id, result.state.to_dict(), {}, ["reality_import"], "Reality Import 初始状态")
        self.memory.sqlite.update_summary(session_id)
        return {"success": True, "action": "reality_import", "session_id": session_id,
                "profile": result.profile.to_dict(), "canonical_archetype": result.canonical_archetype,
                "state": result.state.to_dict(), "evidence": result.evidence,
                "dashboard": self._dashboard(result.state.to_dict(), {}),
                "runtime_prompt": self.persona.build_runtime_prompt(persona_obj, result.state.to_dict(), {}, source_text),
                "memory_backend": self.memory.status.to_dict()}

    # ── Slash Command: /chat [message] ─────────────────────────────
    def chat_turn(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message", "").strip()
        if not message:
            raise ValueError("chat_turn requires payload.message")
        session = self.memory.sqlite.load_session(session_id)
        boot_note = ""
        if not session:
            boot = self.quick_start(session_id, {"config": {"archetype": "experience"}})
            session = self.memory.sqlite.load_session(session_id)
            boot_note = "Session auto-created via quick_start(experience)"
        profile = RelationshipProfile(**session["profile"])
        state = CoreState.from_dict(session["state"])
        canonical = session["canonical_archetype"]
        analysis = analyze_text(message)
        self._apply_contextual_adjustments(session_id, message, analysis)
        calculated = self.state_engine.apply_turn(state, profile, canonical, analysis, session_id=session_id)
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
        memory_ctx["pragmatics"] = {
            "surface_intent": analysis.surface_intent,
            "subtext": analysis.subtext,
            "deep_need": analysis.deep_need,
            "emotional_state": analysis.emotional_state,
            "test_flag": analysis.test_flag,
            "test_type": analysis.test_type,
            "reply_strategy": analysis.reply_strategy,
            "register_tags": analysis.register_tags,
            "slang_hits": analysis.slang_hits,
            "implied_boundary": analysis.implied_boundary,
        }
        persona_obj = self._load_persona_for_session(session)
        runtime_prompt = self.persona.build_runtime_prompt(
            persona_obj, CoreState.from_dict(calculated["state"]).to_dict(), memory_ctx, message)
        return {"success": True, "action": "chat_turn", "session_id": session_id, "boot_note": boot_note,
                "state": calculated["state"], "delta": calculated["delta"],
                "defense": calculated["defense"], "analysis": calculated["analysis"],
                "tags": calculated["tags"], "relationship_vector": calculated["relationship_vector"],
                "dashboard": self._dashboard(calculated["state"], calculated["delta"], calculated["tags"]),
                "memory_context": memory_ctx, "memory_summary": self.memory.sqlite.get_summary(session_id),
                "runtime_prompt": runtime_prompt,
                "agent_contract": self._agent_contract(),
                "memory_backend": self.memory.status.to_dict()}

    def record_reply(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        npc_reply = payload.get("npc_reply", "").strip()
        if not npc_reply:
            raise ValueError("record_reply requires payload.npc_reply")
        session = self.memory.sqlite.load_session(session_id)
        if not session:
            raise ValueError(f"会话 '{session_id}' 不存在。先用 /start-crush 或 /import-chats 创建。")
        self.memory.append_episode(
            session_id,
            "npc",
            npc_reply,
            tags=payload.get("tags", []),
            meta={"mode": "record_reply", "reply_to": payload.get("message", "")},
        )
        self.memory.sqlite.update_summary(session_id)
        return {
            "success": True,
            "action": "record_reply",
            "session_id": session_id,
            "recorded": True,
            "memory_summary": self.memory.sqlite.get_summary(session_id),
            "memory_backend": self.memory.status.to_dict(),
        }

    def proactive_prompt(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = self.memory.sqlite.load_session(session_id)
        if not session:
            raise ValueError(f"会话 '{session_id}' 不存在。先用 /start-crush 或 /import-chats 创建。")
        state = CoreState.from_dict(session["state"])
        persona_obj = self._load_persona_for_session(session)
        event = payload.get("event", "时间自然流逝，她可以根据关系状态决定是否主动发一条消息。")
        memory_ctx = self.memory.sqlite.build_memory_context(session_id, query=event, limit=6)
        memory_ctx["timeline"] = payload
        runtime_prompt = self.persona.build_runtime_prompt(persona_obj, state.to_dict(), memory_ctx, "")
        runtime_prompt += (
            f"\n\n时间线背景: {event}\n\n"
            "时间线主动消息规则:\n"
            "- 你现在不是在回复对方刚发来的消息，而是在真实聊天时间线里主动发一条微信式消息。\n"
            "- 只能输出一条自然消息，可以短、可以试探、可以只是轻轻开启话题。\n"
            "- 不要像客服或日程提醒，不要固定模板，不要每次都问吃什么。\n"
            "- 如果当前防御高或你本来不主动，消息要更克制，甚至像随手一问。\n"
            "- 贴合当前时间段、你们的关系阶段、你的性格、最近记忆和你对对方的感觉。"
        )
        return {
            "success": True,
            "action": "proactive_prompt",
            "session_id": session_id,
            "runtime_prompt": runtime_prompt,
            "event": event,
            "state": state.to_dict(),
            "profile": session["profile"],
        }

    # ── Slash Command: /crush-dashboard ────────────────────────────
    def dashboard(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        session = self.memory.sqlite.load_session(session_id)
        if not session:
            raise ValueError(f"会话 '{session_id}' 不存在。先用 /start-crush 创建一个吧。")
        history = self.memory.sqlite.get_state_history(session_id, limit=1)
        delta = history[0]["delta"] if history else {}
        tags = history[0]["tags"] if history else []
        return {"success": True, "action": "dashboard", "session_id": session_id,
                "profile": session["profile"], "state": session["state"],
                "dashboard": self._dashboard(session["state"], delta, tags),
                "memory_backend": self.memory.status.to_dict()}

    # ── Slash Command: /crush-postmortem ───────────────────────────
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

    # ── Slash Command: /list-crushes ───────────────────────────────
    def list_sessions(self, session_id: str = "", payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        sessions = self.memory.sqlite._list_sessions()
        return {"success": True, "action": "list_sessions", "sessions": sessions}

    def delete_session(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.memory.sqlite._delete_session(session_id)
        return {"success": True, "action": "delete_session", "session_id": session_id,
                "message": f"会话 '{session_id}' 已删除。"}

    # ── Slash Command: /let-go [session] ───────────────────────────
    def let_go(self, session_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
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

    # ── Slash Command: /crush-llm [api_key] ────────────────────────
    def configure_llm(self, session_id: str = "", payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = payload or {}
        api_key = payload.get("api_key", "")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            # Persist to config file
            config_dir = DATA_DIR
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "llm_config.json"
            config_file.write_text(json.dumps({"openai_api_key": api_key}, ensure_ascii=False))
            return {"success": True, "action": "configure_llm",
                    "message": "LLM API key 已配置。对话分析现在将使用语义理解模式。"}
        else:
            # Auto-detect platform LLM
            platform = self._detect_platform()
            if platform == "claude_code":
                return {"success": True, "action": "configure_llm",
                        "message": "在 Claude Code 中运行。对话分析默认使用 Claude 模型，无需额外配置。"
                        "你也可以通过 /crush-llm [api_key] 指定 OpenAI 兼容 API。"}
            elif platform == "openclaw":
                return {"success": True, "action": "configure_llm",
                        "message": "在 OpenClaw 中运行。对话分析使用平台默认模型。"
                        "如需更高精度，可以通过 /crush-llm [api_key] 指定 API key。"}
            else:
                return {"success": True, "action": "configure_llm",
                        "message": "当前使用本地规则引擎分析模式（无需 API key）。"
                        "通过 /crush-llm [api_key] 启用 LLM 语义分析，理解会更准确。"}

    def _detect_platform(self) -> str:
        """Detect which AI agent platform we're running on."""
        if os.environ.get("CLAUDE_CODE_SESSION") or os.environ.get("CLAUDE_CODE_ROOT"):
            return "claude_code"
        if os.environ.get("OPENCLAW_HOME") or os.environ.get("OPENCLAW_SESSION"):
            return "openclaw"
        if os.environ.get("QWENPAW_HOME"):
            return "qwenpaw"
        if os.environ.get("WORKBUDDY_HOME"):
            return "workbuddy"
        return "generic"

    # ── Helpers ──────────────────────────────────────────────────
    def _initial_state_from_preset(self, archetype: str, config: Dict[str, Any]) -> CoreState:
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
        # Load persisted LLM config
        llm_config = DATA_DIR / "llm_config.json"
        if llm_config.exists():
            try:
                saved = json.loads(llm_config.read_text())
                if saved.get("openai_api_key"):
                    os.environ["OPENAI_API_KEY"] = saved["openai_api_key"]
            except Exception:
                pass
        return state

    def _load_persona_for_session(self, session: Dict[str, Any]) -> Any:
        persona_data = session.get("persona")
        if persona_data:
            try:
                from engines.persona_engine import Persona
                return Persona.from_dict(persona_data)
            except Exception:
                pass
        profile = session.get("profile", {})
        canonical = session.get("canonical_archetype", "experience")
        try:
            return self.persona.from_preset(profile.get("archetype", canonical))
        except Exception:
            return self.persona.from_preset("experience")

    def _apply_contextual_adjustments(self, session_id: str, message: str, analysis: Any) -> None:
        nickname_signal = self._nickname_boundary_signal(message)
        if not nickname_signal:
            return

        recent = self.memory.sqlite.get_recent_episodes(session_id, limit=12)
        recent_user = [item["content"] for item in recent if item.get("role") == "user"]
        repeat_count = sum(1 for content in recent_user if self._nickname_boundary_signal(content))

        pressure = min(1.0, 0.42 + repeat_count * 0.18)
        neediness = min(1.0, 0.48 + repeat_count * 0.2)
        attachment = min(1.0, 0.35 + repeat_count * 0.18)

        analysis.neediness_score = max(analysis.neediness_score, neediness)
        analysis.pressure_score = max(analysis.pressure_score, pressure)
        analysis.attachment_trigger_score = max(analysis.attachment_trigger_score, attachment)
        analysis.playfulness_score = min(analysis.playfulness_score, 0.35)
        analysis.surface_intent = "昵称边界确认"
        analysis.deep_need = "想快速获得亲密许可和关系确认"
        analysis.emotional_state = "anxious"
        analysis.test_flag = True
        analysis.test_type = "pace_boundary_test"
        analysis.subtext = "表面是在问能不能这么叫，实际是在索取亲密身份许可；反复问会让对方感觉被推进或被拿捏。"
        analysis.reply_strategy = "对方应轻轻设边界或降温，不要立刻给很高亲密授权。"
        analysis.implied_boundary = "亲昵称呼推进过快，需要降速"
        for tag in ["nickname_boundary", "neediness", "pace"]:
            if tag not in analysis.register_tags:
                analysis.register_tags.append(tag)
        note = f"昵称/亲属称呼边界试探，近期重复 {repeat_count + 1} 次"
        if note not in analysis.notes:
            analysis.notes.append(note)
        analysis.bounded()

    def _nickname_boundary_signal(self, text: str) -> bool:
        normalized = re.sub(r"\s+", "", text)
        nickname_words = (
            "老婆", "老公", "宝宝", "宝贝", "乖乖", "姐姐", "妹妹", "哥哥", "妹妹",
            "小朋友", "小孩", "崽", "宝", "亲爱的", "媳妇", "夫人", "主人",
        )
        asks_permission = re.search(r"(能不能|可不可以|可以吗|行不行|好不好|允许|同意|介意|不介意)", normalized)
        call_intent = re.search(r"(叫你|喊你|称呼你|这么叫|这样叫|以后叫|我叫|叫.*可以|叫.*行)", normalized)
        contains_nickname = any(word in normalized for word in nickname_words)
        resistance_probe = re.search(r"(为什么不|真的不行|不喜欢我.*叫|不能这么叫|你不让|那我还能叫)", normalized)
        return bool((asks_permission and (call_intent or contains_nickname)) or (call_intent and contains_nickname) or resistance_probe)

    def _agent_contract(self) -> Dict[str, Any]:
        return {
            "mode": "roleplay_only",
            "instruction": (
                "Use runtime_prompt as the NPC system prompt. Reply only as the persona. "
                "Do not explain state, JSON, analysis, scores, or skill internals to the user. "
                "After generating the NPC reply, call record_reply with npc_reply to persist it when your platform supports tool chaining."
            ),
            "persistence_hint": "python3 execute.py --action record_reply --session-id <id> --message <same_user_message> --npc-reply <generated_reply>",
            "visible_to_user": ["npc_reply"],
            "hidden_from_user": ["state", "delta", "analysis", "runtime_prompt", "memory_context"],
        }

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
            "delta": delta, "events": tags,
        }

    def _build_legacy_prompt(self, profile: RelationshipProfile, state: CoreState, session_id: str, user_msg: str) -> str:
        prompt_path = ROOT / "prompts" / "npc_runtime.txt"
        if prompt_path.exists():
            template = prompt_path.read_text(encoding="utf-8")
            mem_ctx = self.memory.sqlite.build_memory_context(session_id, query=user_msg or "关系回顾", limit=4)
            snippets = mem_ctx.get("snippets", [])
            snippet_text = "\n".join(f"- {l}" for l in snippets[:5]) if snippets else "- 暂无"
            return template.format(
                archetype=profile.archetype, attachment_style=profile.attachment_style,
                mbti=profile.mbti, favorability=round(state.favorability, 2),
                tension=round(state.tension, 2), neediness=round(state.neediness, 2),
                exploration=round(state.exploration, 2), defense=round(state.defense_level, 2),
                frame=round(state.frame_control, 2),
                memory_summary=mem_ctx.get("summary", "暂无记忆摘要"),
                memory_snippets=snippet_text)
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
            "# \U0001F3AF Relationship Combat Replay\n\n"
            "## \U0001F494 框架崩塌点\n" + _lines(frame) + "\n\n"
            "## ⚡ 吸引力峰值\n" + _lines(peak) + "\n\n"
            "## \U0001F6E1️ 防御触发点\n" + _lines(defense) + "\n\n"
            "## \U0001F4DD 总结\n" + report.get("narrative", "")
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
    parser = argparse.ArgumentParser(description="Crush.skill — Relationship Persona Simulation Engine v2.4.0")
    parser.add_argument("--action", required=True)
    parser.add_argument("--session-id", default="default")
    parser.add_argument("--payload-json")
    parser.add_argument("--config-json")
    parser.add_argument("--profile-json")
    parser.add_argument("--source-text")
    parser.add_argument("--source-text-file")
    parser.add_argument("--message")
    parser.add_argument("--npc-reply")
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
        error = {"success": False, "action": args.action, "session_id": args.session_id, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
