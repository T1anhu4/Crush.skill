from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .weflow.builders import (
    build_dialogue_chunks,
    build_target_reply_clusters,
    build_target_reply_examples,
    count_days,
)
from .weflow.parser import detect_weflow_format, parse_weflow_export
from .weflow.profile import build_persona_profile
from .weflow.timeline import build_timeline_summary
from .weflow.types import WeFlowBundle


def detectWeFlowFormat(data: Any) -> bool:
    return detect_weflow_format(data)


def parseWeFlowExport(source: str | Path | Dict[str, Any]) -> Dict[str, Any]:
    parsed = parse_weflow_export(source)
    parsed["messages"] = [m.to_dict() for m in parsed["messages"]]
    return parsed


def normalizeWeFlowMessages(data: Dict[str, Any], import_id: str) -> list[Dict[str, Any]]:
    from .weflow.parser import normalize_weflow_messages

    messages, _stats = normalize_weflow_messages(data, import_id)
    return [m.to_dict() for m in messages]


def sanitizeWeFlowSession(session: Dict[str, Any]) -> Dict[str, Any]:
    from .weflow.privacy import sanitize_session

    safe, _count, _hash = sanitize_session(session)
    return safe


def importWeFlowJson(source: str | Path | Dict[str, Any]) -> Dict[str, Any]:
    return buildMemoryFromImportedChat(source).to_dict()


def buildMemoryFromImportedChat(source: str | Path | Dict[str, Any]) -> WeFlowBundle:
    parsed = parse_weflow_export(source)
    messages = parsed["messages"]
    chunks = build_dialogue_chunks(messages)
    examples = build_target_reply_examples(messages)
    clusters = build_target_reply_clusters(messages)
    persona_profile, persona_md = build_persona_profile(messages, clusters)
    timeline = build_timeline_summary(messages)

    timestamps = [m.timestamp for m in messages if m.timestamp]
    stats = dict(parsed["stats"])
    stats.update(
        {
            "normalized": len(messages),
            "dialogue_chunks": len(chunks),
            "target_reply_examples": len(examples),
            "target_reply_clusters": len(clusters),
            "timeline_periods": len(timeline),
            "date_range": [
                messages[0].time or str(min(timestamps or [0])),
                messages[-1].time or str(max(timestamps or [0])),
            ],
            "message_frequency": count_days(messages),
        }
    )
    return WeFlowBundle(
        import_id=parsed["import_id"],
        file_hash=parsed["file_hash"],
        session_hash=parsed["session_hash"],
        session=parsed["session"],
        messages=messages,
        stats=stats,
        dialogue_chunks=chunks,
        target_reply_examples=examples,
        target_reply_clusters=clusters,
        persona_profile=persona_profile,
        persona_profile_md=persona_md,
        timeline_summary=timeline,
    )


# PEP-8 aliases for internal callers.
detect_weflow_format = detectWeFlowFormat
parse_weflow_export_public = parseWeFlowExport
import_weflow_json = importWeFlowJson
build_memory_from_imported_chat = buildMemoryFromImportedChat

