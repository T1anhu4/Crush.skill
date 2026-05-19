from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


STOP_WORDS = {
    "的",
    "了",
    "吗",
    "我",
    "你",
    "他",
    "她",
    "它",
    "是",
    "在",
    "and",
    "the",
    "to",
    "a",
    "i",
    "you",
}


class MemoryEngine:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                state_json TEXT NOT NULL,
                canonical_archetype TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                meta_json TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS state_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                state_json TEXT NOT NULL,
                delta_json TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS summaries (
                session_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def _now(self) -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def close(self) -> None:
        self.conn.close()

    def upsert_session(
        self,
        session_id: str,
        profile: Dict[str, Any],
        state: Dict[str, Any],
        canonical_archetype: str,
    ) -> None:
        now = self._now()
        self.conn.execute(
            """
            INSERT INTO sessions(session_id, profile_json, state_json, canonical_archetype, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              profile_json=excluded.profile_json,
              state_json=excluded.state_json,
              canonical_archetype=excluded.canonical_archetype,
              updated_at=excluded.updated_at
            """,
            (
                session_id,
                json.dumps(profile, ensure_ascii=False),
                json.dumps(state, ensure_ascii=False),
                canonical_archetype,
                now,
                now,
            ),
        )
        self.conn.commit()

    def load_session(self, session_id: str) -> Dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT session_id, profile_json, state_json, canonical_archetype, created_at, updated_at FROM sessions WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "session_id": row["session_id"],
            "profile": json.loads(row["profile_json"]),
            "state": json.loads(row["state_json"]),
            "canonical_archetype": row["canonical_archetype"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def append_episode(
        self,
        session_id: str,
        role: str,
        content: str,
        tags: List[str] | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> None:
        tags = tags or []
        meta = meta or {}
        vector = self._text_to_vector(content)
        self.conn.execute(
            """
            INSERT INTO episodes(session_id, role, content, tags_json, meta_json, vector_json, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(meta, ensure_ascii=False),
                json.dumps(vector, ensure_ascii=False),
                self._now(),
            ),
        )
        self.conn.commit()

    def append_state_snapshot(
        self,
        session_id: str,
        state: Dict[str, Any],
        delta: Dict[str, Any],
        tags: List[str],
        note: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO state_history(session_id, state_json, delta_json, tags_json, note, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                json.dumps(state, ensure_ascii=False),
                json.dumps(delta, ensure_ascii=False),
                json.dumps(tags, ensure_ascii=False),
                note,
                self._now(),
            ),
        )
        self.conn.commit()

    def append_timeline_event(
        self,
        session_id: str,
        event_type: str,
        summary: str,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        payload = payload or {}
        self.conn.execute(
            """
            INSERT INTO timeline_events(session_id, event_type, summary, payload_json, created_at)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                session_id,
                event_type,
                summary,
                json.dumps(payload, ensure_ascii=False),
                self._now(),
            ),
        )
        self.conn.commit()

    def get_recent_episodes(self, session_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, role, content, tags_json, meta_json, created_at
            FROM episodes
            WHERE session_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "tags": json.loads(row["tags_json"]),
                "meta": json.loads(row["meta_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_timeline(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, event_type, summary, payload_json, created_at
            FROM timeline_events
            WHERE session_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "summary": row["summary"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_state_history(self, session_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, state_json, delta_json, tags_json, note, created_at
            FROM state_history
            WHERE session_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "state": json.loads(row["state_json"]),
                "delta": json.loads(row["delta_json"]),
                "tags": json.loads(row["tags_json"]),
                "note": row["note"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def retrieve_relevant(self, session_id: str, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        query_vec = self._text_to_vector(query)
        query_tokens = set(self._tokenize(query))
        rows = self.conn.execute(
            """
            SELECT id, role, content, tags_json, meta_json, vector_json, created_at
            FROM episodes
            WHERE session_id=?
            ORDER BY id DESC
            LIMIT 120
            """,
            (session_id,),
        ).fetchall()

        scored = []
        for row in rows:
            vector = json.loads(row["vector_json"])
            cosine = self._cosine(query_vec, vector)
            tokens = set(self._tokenize(row["content"]))
            overlap = len(tokens & query_tokens) / max(1, len(query_tokens))
            score = cosine * 0.65 + overlap * 0.35
            scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)

        result = []
        for score, row in scored[:limit]:
            result.append(
                {
                    "id": row["id"],
                    "score": round(score, 4),
                    "role": row["role"],
                    "content": row["content"],
                    "tags": json.loads(row["tags_json"]),
                    "meta": json.loads(row["meta_json"]),
                    "created_at": row["created_at"],
                }
            )
        return result

    def get_summary(self, session_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT summary FROM summaries WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return row["summary"]

    def update_summary(self, session_id: str) -> str:
        recent = self.get_recent_episodes(session_id, limit=40)
        history = self.get_state_history(session_id, limit=16)

        lines: List[str] = []

        if history:
            latest = history[0]["state"]
            favorability = latest.get("favorability", 0)
            defense_level = latest.get("defense_level", 0)
            exploration = latest.get("exploration", 0)
            lines.append(
                f"关系态势: favorability={favorability:.1f}, defense={defense_level:.1f}, exploration={exploration:.1f}"
            )

        snippets = []
        for item in reversed(recent[:8]):
            snippets.append(f"{item['role']}: {item['content'][:40]}")
        if snippets:
            lines.append("最近互动: " + " | ".join(snippets))

        token_counter: Counter[str] = Counter()
        for item in recent:
            for token in self._tokenize(item["content"]):
                if token not in STOP_WORDS and len(token) >= 2:
                    token_counter[token] += 1

        keywords = [word for word, _ in token_counter.most_common(8)]
        if keywords:
            lines.append("长期关键词: " + ", ".join(keywords))

        summary = "\n".join(lines) if lines else "尚无记忆摘要"

        self.conn.execute(
            """
            INSERT INTO summaries(session_id, summary, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET summary=excluded.summary, updated_at=excluded.updated_at
            """,
            (session_id, summary, self._now()),
        )
        self.conn.commit()
        return summary

    def build_memory_context(self, session_id: str, query: str, limit: int = 6) -> Dict[str, Any]:
        summary = self.get_summary(session_id)
        if summary is None:
            summary = self.update_summary(session_id)

        related = self.retrieve_relevant(session_id, query=query, limit=limit)
        snippets = [f"[{item['role']}] {item['content']}" for item in related]
        return {
            "summary": summary,
            "snippets": snippets,
            "items": related,
        }

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

    def _text_to_vector(self, text: str, dims: int = 256) -> Dict[str, float]:
        counts: Dict[int, float] = {}
        for token in self._tokenize(text):
            idx = hash(token) % dims
            counts[idx] = counts.get(idx, 0.0) + 1.0

        norm = math.sqrt(sum(v * v for v in counts.values()))
        if norm == 0:
            return {}
        return {str(k): v / norm for k, v in counts.items()}

    def _cosine(self, left: Dict[str, float], right: Dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        total = 0.0
        for key, value in left.items():
            total += value * right.get(key, 0.0)
        return total
