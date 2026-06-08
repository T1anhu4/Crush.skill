from __future__ import annotations

import hashlib
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
        self.conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        try:
            self.conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            # Another running CLI may already hold the database. Keep startup
            # usable; busy_timeout still makes ordinary writes wait politely.
            pass
        self._init_db()

    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                state_json TEXT NOT NULL,
                persona_json TEXT,
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

            CREATE TABLE IF NOT EXISTS import_records (
                import_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                session_hash TEXT NOT NULL,
                source_type TEXT NOT NULL,
                stats_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(session_id, file_hash)
            );

            CREATE TABLE IF NOT EXISTS import_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                import_id TEXT NOT NULL,
                message_hash TEXT NOT NULL,
                speaker TEXT NOT NULL,
                content TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(session_id, message_hash)
            );

            CREATE TABLE IF NOT EXISTS memory_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                import_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                text TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                weight REAL NOT NULL,
                vector_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(session_id, import_id, artifact_type, artifact_id)
            );
            """
        )
        self._ensure_column("sessions", "persona_json", "TEXT")
        self.conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {
            row["name"]
            for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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
        persona: Dict[str, Any] | None = None,
    ) -> None:
        now = self._now()
        current = self.load_session(session_id)
        persona_json = (
            json.dumps(persona, ensure_ascii=False)
            if persona is not None
            else json.dumps(current.get("persona"), ensure_ascii=False)
            if current and current.get("persona")
            else None
        )
        self.conn.execute(
            """
            INSERT INTO sessions(session_id, profile_json, state_json, persona_json, canonical_archetype, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              profile_json=excluded.profile_json,
              state_json=excluded.state_json,
              persona_json=COALESCE(excluded.persona_json, sessions.persona_json),
              canonical_archetype=excluded.canonical_archetype,
              updated_at=excluded.updated_at
            """,
            (
                session_id,
                json.dumps(profile, ensure_ascii=False),
                json.dumps(state, ensure_ascii=False),
                persona_json,
                canonical_archetype,
                now,
                now,
            ),
        )
        self.conn.commit()

    def load_session(self, session_id: str) -> Dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT session_id, profile_json, state_json, persona_json, canonical_archetype, created_at, updated_at FROM sessions WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "session_id": row["session_id"],
            "profile": json.loads(row["profile_json"]),
            "state": json.loads(row["state_json"]),
            "persona": json.loads(row["persona_json"]) if row["persona_json"] else None,
            "canonical_archetype": row["canonical_archetype"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def save_persona(self, session_id: str, persona: Dict[str, Any]) -> None:
        self.conn.execute(
            "UPDATE sessions SET persona_json=?, updated_at=? WHERE session_id=?",
            (json.dumps(persona, ensure_ascii=False), self._now(), session_id),
        )
        self.conn.commit()

    def load_persona(self, session_id: str) -> Dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT persona_json FROM sessions WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if not row or not row["persona_json"]:
            return None
        return json.loads(row["persona_json"])

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
        weflow = self.build_weflow_context(session_id, query=query)
        return {
            "summary": summary,
            "snippets": snippets,
            "items": related,
            **weflow,
        }

    def save_weflow_bundle(self, session_id: str, bundle: Any) -> Dict[str, Any]:
        data = bundle.to_dict() if hasattr(bundle, "to_dict") else dict(bundle)
        existing = self.conn.execute(
            "SELECT import_id, stats_json FROM import_records WHERE session_id=? AND file_hash=?",
            (session_id, data["file_hash"]),
        ).fetchone()
        if existing:
            existing_stats = json.loads(existing["stats_json"])
            existing_privacy = existing_stats.get("privacy_mode", "safe")
            new_privacy = data.get("stats", {}).get("privacy_mode", "safe")
            if existing_privacy != new_privacy:
                self.delete_import(session_id, existing["import_id"])
                existing = None
            else:
                return {
                    "already_imported": True,
                    "import_id": existing["import_id"],
                    "stats": existing_stats,
                }
        base_import_id = data["import_id"]
        import_id = self._session_import_id(session_id, data["file_hash"], base_import_id)
        now = self._now()
        self.conn.execute(
            """
            INSERT INTO import_records(import_id, session_id, file_hash, session_hash, source_type, stats_json, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                import_id,
                session_id,
                data["file_hash"],
                data["session_hash"],
                "weflow",
                json.dumps(data["stats"], ensure_ascii=False),
                now,
            ),
        )
        inserted_messages = 0
        for msg in data.get("messages", []):
            try:
                cursor = self.conn.execute(
                    """
                    INSERT OR IGNORE INTO import_messages(session_id, import_id, message_hash, speaker, content, payload_json, created_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        import_id,
                        msg["contentHash"],
                        msg["speaker"],
                        msg["content"],
                        json.dumps(msg, ensure_ascii=False),
                        now,
                    ),
                )
                inserted_messages += max(0, cursor.rowcount)
            except Exception:
                continue
        artifact_count = 0
        artifact_count += self._save_artifact_many(session_id, import_id, "target_reply_example", data.get("target_reply_examples", []), "embeddingText", 1.0)
        artifact_count += self._save_artifact_many(session_id, import_id, "target_reply_cluster", data.get("target_reply_clusters", []), "embeddingText", 0.95)
        artifact_count += self._save_artifact_many(session_id, import_id, "dialogue_chunk", data.get("dialogue_chunks", []), "text", 0.62)
        artifact_count += self._save_artifact_many(session_id, import_id, "timeline_summary", data.get("timeline_summary", []), "summary", 0.35)
        artifact_count += self._save_artifact_many(session_id, import_id, "media_asset", data.get("media_assets", []), "text", 0.75)
        profile_text = data.get("persona_profile_md", "")
        if profile_text:
            artifact_count += self._save_artifact_many(
                session_id,
                import_id,
                "persona_profile",
                [{"artifactId": "persona_profile", "text": profile_text, **data.get("persona_profile", {})}],
                "text",
                0.8,
            )
        self.conn.commit()
        return {
            "already_imported": False,
            "import_id": import_id,
            "source_import_id": base_import_id,
            "stats": data["stats"],
            "inserted_messages": inserted_messages,
            "artifact_count": artifact_count,
        }

    def _session_import_id(self, session_id: str, file_hash: str, base_import_id: str) -> str:
        existing = self.conn.execute(
            "SELECT session_id FROM import_records WHERE import_id=?",
            (base_import_id,),
        ).fetchone()
        if not existing or existing["session_id"] == session_id:
            return base_import_id
        digest = hashlib.sha256(f"{session_id}|{file_hash}".encode("utf-8")).hexdigest()[:16]
        return f"wf_{digest}"

    def _save_artifact_many(self, session_id: str, import_id: str, artifact_type: str, items: List[Dict[str, Any]], text_key: str, weight: float) -> int:
        count = 0
        for idx, item in enumerate(items, start=1):
            artifact_id = str(item.get("exampleId") or item.get("clusterId") or item.get("chunkId") or item.get("artifactId") or f"{artifact_type}_{idx}")
            text = str(item.get(text_key) or item.get("text") or item.get("summary") or "")
            if not text:
                continue
            item_weight = float(item.get("weight", weight))
            self.conn.execute(
                """
                INSERT OR REPLACE INTO memory_artifacts(session_id, import_id, artifact_type, artifact_id, text, payload_json, weight, vector_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    import_id,
                    artifact_type,
                    artifact_id,
                    text,
                    json.dumps(item, ensure_ascii=False),
                    item_weight,
                    json.dumps(self._text_to_vector(text), ensure_ascii=False),
                    self._now(),
                ),
            )
            count += 1
        return count

    def retrieve_artifacts(self, session_id: str, query: str, artifact_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_vec = self._text_to_vector(query)
        query_tokens = set(self._tokenize(query))
        rows = self.conn.execute(
            """
            SELECT artifact_type, artifact_id, text, payload_json, weight, vector_json, created_at
            FROM memory_artifacts
            WHERE session_id=? AND artifact_type=?
            ORDER BY id DESC
            LIMIT 400
            """,
            (session_id, artifact_type),
        ).fetchall()
        scored = []
        for row in rows:
            vector = json.loads(row["vector_json"])
            cosine = self._cosine(query_vec, vector)
            tokens = set(self._tokenize(row["text"]))
            overlap = len(tokens & query_tokens) / max(1, len(query_tokens))
            score = (cosine * 0.58 + overlap * 0.42) * float(row["weight"])
            scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "score": round(score, 4),
                "artifact_type": row["artifact_type"],
                "artifact_id": row["artifact_id"],
                "text": row["text"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for score, row in scored[:limit]
        ]

    def build_weflow_context(self, session_id: str, query: str) -> Dict[str, Any]:
        profile = self.retrieve_artifacts(session_id, query or "persona profile", "persona_profile", limit=1)
        return {
            "persona_profile": profile[0]["payload"] if profile else {},
            "persona_profile_text": profile[0]["text"] if profile else "",
            "target_reply_examples": self.retrieve_artifacts(session_id, query, "target_reply_example", limit=8),
            "target_reply_clusters": self.retrieve_artifacts(session_id, query, "target_reply_cluster", limit=5),
            "dialogue_chunks": self.retrieve_artifacts(session_id, query, "dialogue_chunk", limit=4),
            "timeline_summary": self.retrieve_artifacts(session_id, query, "timeline_summary", limit=3),
            "media_assets": self.get_media_assets(session_id, limit=8),
        }

    def get_media_assets(self, session_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT artifact_type, artifact_id, text, payload_json, created_at
            FROM memory_artifacts
            WHERE session_id=? AND artifact_type='media_asset'
            ORDER BY id DESC
            LIMIT 800
            """,
            (session_id,),
        ).fetchall()
        items = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            target_count = int((payload.get("speakerCounts") or {}).get("target", 0))
            me_count = int((payload.get("speakerCounts") or {}).get("me", 0))
            items.append(
                {
                    "score": target_count,
                    "artifact_type": row["artifact_type"],
                    "artifact_id": row["artifact_id"],
                    "text": row["text"],
                    "payload": payload,
                    "created_at": row["created_at"],
                }
            )
        items.sort(key=lambda item: (item["score"], item["payload"].get("speakerCounts", {}).get("me", 0), item["payload"].get("kind", "")), reverse=True)
        return items[:limit]

    def get_import_status(self, session_id: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT import_id, source_type, stats_json, created_at FROM import_records WHERE session_id=? ORDER BY created_at DESC",
            (session_id,),
        ).fetchall()
        return [
            {"import_id": row["import_id"], "source_type": row["source_type"], "stats": json.loads(row["stats_json"]), "created_at": row["created_at"]}
            for row in rows
        ]

    def delete_import(self, session_id: str, import_id: str) -> None:
        for table in ["memory_artifacts", "import_messages", "import_records"]:
            self.conn.execute(f"DELETE FROM {table} WHERE session_id=? AND import_id=?", (session_id, import_id))
        self.conn.commit()

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

    def _list_sessions(self) -> list:
        rows = self.conn.execute(
            "SELECT session_id, canonical_archetype, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        return [{"session_id": r["session_id"], "canonical_archetype": r["canonical_archetype"],
                 "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]

    def _delete_session(self, session_id: str) -> None:
        for table in ["episodes", "timeline_events", "state_history", "summaries", "memory_artifacts", "import_messages", "import_records", "sessions"]:
            self.conn.execute(f"DELETE FROM {table} WHERE session_id=?", (session_id,))
        self.conn.commit()

    def _cosine(self, left: Dict[str, float], right: Dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        total = 0.0
        for key, value in left.items():
            total += value * right.get(key, 0.0)
        return total
