from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class NormalizedMessage:
    id: str
    import_id: str
    timestamp: int
    time: str
    speaker: str
    message_type: str
    content: str
    quoted_content: str | None = None
    quoted_speaker: str | None = None
    raw_type: str = ""
    source_local_id: int | str | None = None
    content_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Keep the JSON shape close to the product spec.
        data["messageType"] = data.pop("message_type")
        data["quotedContent"] = data.pop("quoted_content")
        data["quotedSpeaker"] = data.pop("quoted_speaker")
        data["rawType"] = data.pop("raw_type")
        data["sourceLocalId"] = data.pop("source_local_id")
        data["contentHash"] = data.pop("content_hash")
        return data


@dataclass
class WeFlowBundle:
    import_id: str
    file_hash: str
    session_hash: str
    session: Dict[str, Any]
    messages: List[NormalizedMessage]
    stats: Dict[str, Any]
    dialogue_chunks: List[Dict[str, Any]] = field(default_factory=list)
    target_reply_examples: List[Dict[str, Any]] = field(default_factory=list)
    target_reply_clusters: List[Dict[str, Any]] = field(default_factory=list)
    persona_profile: Dict[str, Any] = field(default_factory=dict)
    persona_profile_md: str = ""
    timeline_summary: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "import_id": self.import_id,
            "file_hash": self.file_hash,
            "session_hash": self.session_hash,
            "session": self.session,
            "messages": [m.to_dict() for m in self.messages],
            "stats": self.stats,
            "dialogue_chunks": self.dialogue_chunks,
            "target_reply_examples": self.target_reply_examples,
            "target_reply_clusters": self.target_reply_clusters,
            "persona_profile": self.persona_profile,
            "persona_profile_md": self.persona_profile_md,
            "timeline_summary": self.timeline_summary,
        }

