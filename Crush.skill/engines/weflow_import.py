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


def parseWeFlowExport(source: str | Path | Dict[str, Any], privacy_mode: str = "safe") -> Dict[str, Any]:
    parsed = parse_weflow_export(source, privacy_mode=privacy_mode)
    parsed["messages"] = [m.to_dict() for m in parsed["messages"]]
    return parsed


def normalizeWeFlowMessages(data: Dict[str, Any], import_id: str, privacy_mode: str = "safe") -> list[Dict[str, Any]]:
    from .weflow.parser import normalize_weflow_messages

    messages, _stats = normalize_weflow_messages(data, import_id, privacy_mode=privacy_mode)
    return [m.to_dict() for m in messages]


def sanitizeWeFlowSession(session: Dict[str, Any]) -> Dict[str, Any]:
    from .weflow.privacy import sanitize_session

    safe, _count, _hash = sanitize_session(session)
    return safe


def importWeFlowJson(source: str | Path | Dict[str, Any], privacy_mode: str = "safe") -> Dict[str, Any]:
    return buildMemoryFromImportedChat(source, privacy_mode=privacy_mode).to_dict()


def buildMemoryFromImportedChat(source: str | Path | Dict[str, Any], privacy_mode: str = "safe") -> WeFlowBundle:
    parsed = parse_weflow_export(source, privacy_mode=privacy_mode)
    messages = parsed["messages"]
    chunks = build_dialogue_chunks(messages)
    examples = build_target_reply_examples(messages)
    clusters = build_target_reply_clusters(messages)
    media_assets = build_media_assets(messages)
    persona_profile, persona_md = build_persona_profile(messages, clusters, session=parsed.get("session", {}), media_assets=media_assets, privacy_mode=privacy_mode)
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
            "media_assets": len(media_assets),
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
        media_assets=media_assets,
    )


def build_media_assets(messages: list[Any]) -> list[Dict[str, Any]]:
    assets: Dict[str, Dict[str, Any]] = {}
    for idx, msg in enumerate(messages):
        media = getattr(msg, "media", {}) or {}
        if not media:
            continue
        key = str(media.get("md5") or media.get("localPath") or media.get("cdnUrl") or media.get("id") or f"media_{idx}")
        asset = assets.setdefault(
            key,
            {
                "artifactId": f"media_{len(assets) + 1}",
                "mediaKey": key,
                "kind": media.get("kind", getattr(msg, "message_type", "media")),
                "localPath": media.get("localPath", ""),
                "cdnUrl": media.get("cdnUrl", ""),
                "md5": media.get("md5", ""),
                "speakerCounts": {"me": 0, "target": 0},
                "examples": [],
                "text": "",
            },
        )
        speaker = getattr(msg, "speaker", "")
        if speaker in asset["speakerCounts"]:
            asset["speakerCounts"][speaker] += 1
        if len(asset["examples"]) < 5:
            asset["examples"].append(
                {
                    "speaker": speaker,
                    "time": getattr(msg, "time", ""),
                    "content": getattr(msg, "content", ""),
                }
            )
    for asset in assets.values():
        target_count = asset["speakerCounts"].get("target", 0)
        me_count = asset["speakerCounts"].get("me", 0)
        asset["text"] = (
            f"{asset['kind']} media {asset['mediaKey']} target_used={target_count} me_used={me_count} "
            f"path={asset.get('localPath') or asset.get('cdnUrl')}"
        )
        asset["weight"] = 0.8 + min(0.4, target_count / 20)
    return sorted(assets.values(), key=lambda item: item["speakerCounts"].get("target", 0), reverse=True)


# PEP-8 aliases for internal callers.
detect_weflow_format = detectWeFlowFormat
parse_weflow_export_public = parseWeFlowExport
import_weflow_json = importWeFlowJson
build_memory_from_imported_chat = buildMemoryFromImportedChat
