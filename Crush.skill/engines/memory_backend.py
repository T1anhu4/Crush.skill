from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .memory_engine import MemoryEngine


@dataclass
class BackendStatus:
    name: str
    enabled: bool
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "enabled": self.enabled, "detail": self.detail}


class Mem0Bridge:
    def __init__(self, api_key: str | None = None) -> None:
        self.client = None
        self.error: str | None = None
        try:
            module = importlib.import_module("mem0")
            memory_cls = getattr(module, "Memory", None)
            if memory_cls is None:
                raise RuntimeError("mem0.Memory not found")
            if hasattr(memory_cls, "from_config"):
                config = {}
                if api_key:
                    config = {"llm": {"provider": "openai", "config": {"api_key": api_key}}}
                self.client = memory_cls.from_config(config)
            else:
                self.client = memory_cls()
        except Exception as exc:  # pragma: no cover
            self.error = str(exc)

    @property
    def available(self) -> bool:
        return self.client is not None

    def add(self, session_id: str, content: str, metadata: Dict[str, Any]) -> None:
        if not self.client:
            return
        try:
            if hasattr(self.client, "add"):
                self.client.add(content, user_id=session_id, metadata=metadata)
        except Exception:
            return

    def search(self, session_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            if hasattr(self.client, "search"):
                result = self.client.search(query, user_id=session_id, limit=limit)
                if isinstance(result, list):
                    return result
                return result.get("results", []) if isinstance(result, dict) else []
        except Exception:
            return []
        return []


class HybridMemoryBackend:
    def __init__(self, data_dir: Path) -> None:
        self.sqlite = MemoryEngine(data_dir / "relationship_memory.sqlite3")
        backend = os.getenv("CRUSH_MEMORY_BACKEND", "sqlite").strip().lower()
        self.mem0 = None
        self.status = BackendStatus(name="sqlite", enabled=True, detail="SQLite persistent memory enabled")

        if backend == "mem0":
            self.mem0 = Mem0Bridge(api_key=os.getenv("OPENAI_API_KEY"))
            if self.mem0.available:
                self.status = BackendStatus(
                    name="mem0+sqlite",
                    enabled=True,
                    detail="mem0 semantic memory enabled; sqlite remains source-of-truth",
                )
            else:
                self.status = BackendStatus(
                    name="sqlite",
                    enabled=True,
                    detail=f"mem0 requested but unavailable, fallback to sqlite ({self.mem0.error})",
                )

    def append_episode(
        self,
        session_id: str,
        role: str,
        content: str,
        tags: list[str] | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> None:
        tags = tags or []
        meta = meta or {}
        self.sqlite.append_episode(session_id=session_id, role=role, content=content, tags=tags, meta=meta)
        if self.mem0 and self.mem0.available:
            self.mem0.add(session_id=session_id, content=f"{role}: {content}", metadata=meta)

    def retrieve_relevant(self, session_id: str, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        local = self.sqlite.retrieve_relevant(session_id=session_id, query=query, limit=limit)
        if not self.mem0 or not self.mem0.available:
            return local

        semantic = self.mem0.search(session_id=session_id, query=query, limit=limit)
        semantic_rows = []
        for idx, item in enumerate(semantic):
            text = item.get("memory") if isinstance(item, dict) else str(item)
            semantic_rows.append(
                {
                    "id": f"mem0-{idx}",
                    "score": round(float(item.get("score", 0.0)), 4) if isinstance(item, dict) else 0.0,
                    "role": "memory",
                    "content": text,
                    "tags": ["mem0"],
                    "meta": item if isinstance(item, dict) else {},
                    "created_at": "",
                }
            )
        return local + semantic_rows
