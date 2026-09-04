# Crush.skill v3 Living Mind Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested First Spark vertical slice with persistent structured mind, human-scale time cycles, short/medium/long-term memory, temporal ontology hybrid retrieval, two-stage generation, post-session review, and a `crush v3` CLI path.

**Architecture:** Add a typed `crush_core` package beside v2.4. SQLite remains the event source of truth; deterministic domain services advance time, consolidate memory, and select bounded retrieval, while a provider adapter supplies structured appraisal and surface text. The existing CLI delegates only commands beginning with `v3`, so all v2 behavior remains available throughout the migration.

**Tech Stack:** Python 3.11+, Pydantic 2, stdlib SQLite/FTS5/urllib, PyYAML, pytest, optional sqlite-vec behind an interface.

---

## File Map

### New production files

- `pyproject.toml`: package metadata, development dependencies, and test configuration.
- `crush_core/__init__.py`: public v3 package version.
- `crush_core/domain/enums.py`: stable event, action, memory, and availability enums.
- `crush_core/domain/models.py`: character, mind, relationship, world, event, action, and memory schemas.
- `crush_core/store/sqlite.py`: schema migrations, event append/load, snapshots, memory records, FTS5, entities, and temporal edges.
- `crush_core/simulation/clock.py`: timezone-aware clock, sleep/routine crossings, long-absence catch-up, and coalescing.
- `crush_core/memory/consolidation.py`: tier promotion, decay, contradiction preservation, and sleep consolidation.
- `crush_core/memory/retrieval.py`: deterministic retrieval recipes, rank fusion, context budgets, and provenance.
- `crush_core/scenarios/models.py`: scenario schema and loader.
- `crush_core/scenarios/first_spark.yaml`: fictional launch scenario, routines, and bounded life events.
- `crush_core/generation/provider.py`: provider protocol and deterministic demo provider.
- `crush_core/generation/openai_compatible.py`: injectable OpenAI-compatible JSON/text transport.
- `crush_core/cognition/engine.py`: observation, structured appraisal application, action choice, and self-consequence.
- `crush_core/safety/validator.py`: assistant-language, privacy, unsupported-fact, repetition, and boundary validators.
- `crush_core/simulation/engine.py`: transactional end-to-end orchestration.
- `crush_core/coaching/review.py`: evidence-backed review and counterfactual branch creation.
- `crush_core/evals/suite.py`: deterministic release metrics and pilot bundle export.
- `crush_core/evals/fixtures/first_spark_cases.yaml`: fictional evaluation cases.
- `crush_cli_v3/app.py`: v3 command parser and terminal rendering.
- `crush_cli_v3/__init__.py`: v3 CLI package marker.

### Modified production files

- `requirements.txt`: add the Pydantic runtime dependency.
- `Makefile`: add focused v3 test and demo targets.
- `crush_cli/app.py`: delegate `crush v3` subcommands before parsing legacy arguments.
- `README.md`: add an alpha developer section only after the vertical slice passes.

### Test files

- `tests/v3/test_package.py`
- `tests/v3/factories.py`
- `tests/v3/conftest.py`
- `tests/v3/test_domain_models.py`
- `tests/v3/test_event_store.py`
- `tests/v3/test_clock.py`
- `tests/v3/test_consolidation.py`
- `tests/v3/test_retrieval.py`
- `tests/v3/test_scenario.py`
- `tests/v3/test_providers.py`
- `tests/v3/test_cognition.py`
- `tests/v3/test_safety.py`
- `tests/v3/test_simulation.py`
- `tests/v3/test_review.py`
- `tests/v3/test_cli.py`
- `tests/v3/test_eval_suite.py`

## Task 1: Establish the v3 Package and Test Harness

**Files:**
- Create: `pyproject.toml`
- Create: `crush_core/__init__.py`
- Create: `crush_core/domain/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/v3/__init__.py`
- Test: `tests/v3/test_package.py`
- Modify: `requirements.txt`
- Modify: `Makefile`

- [ ] **Step 1: Write the failing package test**

```python
# tests/v3/test_package.py
from crush_core import __version__


def test_v3_package_version_is_explicit() -> None:
    assert __version__ == "3.0.0a1"
```

- [ ] **Step 2: Verify the test fails before the package exists**

Run: `python3 -m pytest tests/v3/test_package.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crush_core'`.

- [ ] **Step 3: Add packaging and runtime dependencies**

Create `pyproject.toml` with this complete configuration:

```toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "crush-skill"
version = "3.0.0a1"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.11,<3", "PyYAML>=6.0.1,<7"]

[project.optional-dependencies]
dev = ["pytest>=8.3,<9", "pytest-cov>=6,<7"]
vector = ["sqlite-vec>=0.1.6,<0.2"]

[tool.setuptools.packages.find]
include = ["crush_core*", "crush_cli*", "crush_cli_v3*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Append `pydantic>=2.11,<3` to `requirements.txt`. Add these Makefile targets:

```make
.PHONY: test-v3 demo-v3

test-v3:
	python3 -m pytest tests/v3 -q

demo-v3:
	python3 -m crush_cli v3 demo --seed 17 --plain
```

Create `crush_core/__init__.py`:

```python
"""Crush.skill v3 domain and simulation engine."""

__version__ = "3.0.0a1"
```

Create `crush_core/domain/__init__.py`, `tests/__init__.py`, and `tests/v3/__init__.py`; each contains only a module docstring.

- [ ] **Step 4: Install development dependencies and run the test**

Run: `python3 -m pip install -e '.[dev]'`
Expected: installation completes without dependency conflicts.

Run: `python3 -m pytest tests/v3/test_package.py -q`
Expected: `1 passed`.

- [ ] **Step 5: Commit the package skeleton**

```bash
git add pyproject.toml requirements.txt Makefile crush_core tests/v3/test_package.py
git commit -m "build: add crush v3 package skeleton"
```

## Task 2: Define Typed Domain Contracts

**Files:**
- Create: `crush_core/domain/enums.py`
- Create: `crush_core/domain/models.py`
- Test: `tests/v3/test_domain_models.py`

- [ ] **Step 1: Write schema boundary tests**

```python
# tests/v3/test_domain_models.py
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from crush_core.domain.enums import ActionKind, EventKind, MemoryKind, MemoryTier
from crush_core.domain.models import (
    AffectState,
    CharacterAction,
    MemoryRecord,
    SimulationEvent,
)


NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)


def test_event_requires_timezone_and_idempotency_key() -> None:
    event = SimulationEvent(
        session_id="demo",
        sequence=1,
        kind=EventKind.USER_MESSAGE_RECEIVED,
        occurred_at=NOW,
        idempotency_key="demo:1:user-message",
        payload={"text": "到家了吗"},
    )
    assert event.occurred_at.tzinfo is timezone.utc
    with pytest.raises(ValidationError):
        SimulationEvent(
            session_id="demo",
            sequence=2,
            kind=EventKind.TIME_ELAPSED,
            occurred_at=datetime(2026, 9, 4, 13, 0),
            idempotency_key="demo:2:time",
        )


def test_memory_and_actions_are_bounded_structures() -> None:
    memory = MemoryRecord(
        memory_id="mem-1",
        session_id="demo",
        tier=MemoryTier.MEDIUM,
        kind=MemoryKind.EPISODIC,
        summary="用户说明今天要加班",
        source_event_ids=["evt-1"],
        confidence=0.8,
        salience=0.7,
        created_at=NOW,
        last_confirmed_at=NOW,
    )
    action = CharacterAction(
        kind=ActionKind.DELAY,
        delay_seconds=900,
        intent_summary="想回，但正在开会",
    )
    assert memory.source_event_ids == ["evt-1"]
    assert action.delay_seconds == 900
```

- [ ] **Step 2: Run the schema tests and confirm missing modules**

Run: `python3 -m pytest tests/v3/test_domain_models.py -q`
Expected: FAIL importing `crush_core.domain.enums`.

- [ ] **Step 3: Implement enums and Pydantic models**

`crush_core/domain/enums.py` must define these exact string enums:

```python
from enum import StrEnum


class EventKind(StrEnum):
    USER_MESSAGE_RECEIVED = "user_message_received"
    TIME_ELAPSED = "time_elapsed"
    SLEEP_CYCLE_STARTED = "sleep_cycle_started"
    SLEEP_CYCLE_ENDED = "sleep_cycle_ended"
    ROUTINE_WINDOW_ENTERED = "routine_window_entered"
    LIFE_EVENT_OCCURRED = "life_event_occurred"
    LONG_ABSENCE_OBSERVED = "long_absence_observed"
    MEMORY_CONSOLIDATED = "memory_consolidated"
    MEMORY_RECALLED = "memory_recalled"
    MEMORY_FORGOTTEN = "memory_forgotten"
    MESSAGE_CONSIDERED = "message_considered"
    MESSAGE_SENT = "message_sent"
    MESSAGE_WITHHELD = "message_withheld"
    BELIEF_REVISED = "belief_revised"
    PROMISE_CREATED = "promise_created"
    PROMISE_RESOLVED = "promise_resolved"
    BOUNDARY_CROSSED = "boundary_crossed"
    SESSION_CHECKPOINTED = "session_checkpointed"


class ActionKind(StrEnum):
    TEXT_BURST = "text_burst"
    MEDIA = "media"
    REACTION = "reaction"
    DELAY = "delay"
    SILENCE = "silence"
    TOPIC_CLOSE = "topic_close"
    RELATIONSHIP_CLOSE = "relationship_close"


class MemoryTier(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class MemoryKind(StrEnum):
    TRANSCRIPT = "transcript"
    EPISODIC = "episodic"
    SEMANTIC_SELF = "semantic_self"
    RELATIONAL_BELIEF = "relational_belief"
    PROSPECTIVE = "prospective"
    STYLE = "style"


class Availability(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    ASLEEP = "asleep"
    OFFLINE = "offline"
```

`crush_core/domain/models.py` must define timezone validation and these models with `extra="forbid"`: `RoutineWindow`, `CharacterCore`, `AffectState`, `BeliefHypothesis`, `BeliefUpdate`, `OpenLoop`, `MindState`, `RelationshipState`, `WorldState`, `SimulationSnapshot`, `SimulationEvent`, `CharacterAction`, `ActionPlan`, `MemoryRecord`, `TemporalEdge`, and `RetrievedMemory`. Numeric relationship and confidence fields use `Field(ge=0, le=1)`. `CharacterAction` validates that `TEXT_BURST` has non-empty `messages`, `DELAY` has positive `delay_seconds`, and `SILENCE` has no visible messages. Datetime fields reject naive values with this reusable validator:

```python
def require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value
```

Use these minimum field contracts so later tasks do not invent incompatible state shapes:

| Model | Required fields |
|---|---|
| `RoutineWindow` | `name`, `start_local`, `end_local`, `availability`, `weekdays` |
| `CharacterCore` | `character_id`, `name`, `age`, `pronouns`, `biography`, `values`, `aspirations`, `insecurities`, `boundaries`, `routines`, `style_examples`, `competing_motives`, `timezone` |
| `AffectState` | `label`, `intensity`, `cause_event_ids`, `started_at`, `half_life_minutes` |
| `BeliefHypothesis` | `belief_id`, `claim`, `confidence`, `evidence_event_ids`, `updated_at` |
| `BeliefUpdate` | `belief_id`, `claim`, `confidence`, `evidence_event_ids` |
| `OpenLoop` | `loop_id`, `summary`, `created_from_event_id`, `due_at`, `resolved_at` |
| `MindState` | `affects`, `attention`, `energy`, `availability`, `current_activity`, `goals`, `beliefs`, `open_loops`, `withheld_intent_summaries` |
| `RelationshipState` | `trust`, `comfort`, `curiosity`, `attraction`, `uncertainty`, `pressure`, `rupture`, `repair`, `reciprocity`, `explicit_rejection` |
| `WorldState` | `now`, `timezone`, `sleep_start_local`, `sleep_end_local`, `current_scene`, `next_meaningful_wakeup` |
| `SimulationEvent` | `event_id`, `session_id`, `sequence`, `kind`, `occurred_at`, `idempotency_key`, `payload`, `derived_from_event_ids` |
| `CharacterAction` | `kind`, `messages`, `delay_seconds`, `media_ref`, `reaction`, `intent_summary` |
| `TemporalEdge` | `edge_id`, `session_id`, `source_entity_id`, `predicate`, `target_entity_id`, `valid_from`, `valid_to`, `learned_at`, `invalidated_at`, `confidence`, `source_event_ids` |
| `RetrievedMemory` | `memory`, `score`, `score_components`, `provenance_event_ids` |

List/dictionary fields use `Field(default_factory=list)` or `Field(default_factory=dict)`. Optional time and action-specific fields default to `None`. `ActionPlan.interpretations` has at least one item; `CognitionEngine` applies the stricter two-interpretation rule only when the incoming event is ambiguous.

The snapshot contract is:

```python
class SimulationSnapshot(StrictModel):
    session_id: str
    scenario_id: str
    sequence: int = Field(ge=0)
    seed: int
    character: CharacterCore
    mind: MindState
    relationship: RelationshipState
    world: WorldState
```

The memory contract is:

```python
class MemoryRecord(StrictModel):
    memory_id: str
    session_id: str
    tier: MemoryTier
    kind: MemoryKind
    summary: str = Field(min_length=1)
    subject: str | None = None
    predicate: str | None = None
    object_value: str | None = None
    source_event_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    salience: float = Field(ge=0, le=1)
    emotional_weight: float = Field(default=0, ge=0, le=1)
    explicitly_important: bool = False
    sensitivity: str = "private"
    created_at: datetime
    last_confirmed_at: datetime
    last_recalled_at: datetime | None = None
    due_at: datetime | None = None
    resolved_at: datetime | None = None
    recall_count: int = Field(default=0, ge=0)
    decay_policy: str = "standard"
    contradiction_ids: list[str] = Field(default_factory=list)
```

`SimulationEvent.event_id` uses `Field(default_factory=lambda: uuid4().hex)`. `ActionPlan` contains `interpretations: list[str] = Field(min_length=1)`, `affect_delta: dict[str, float]`, `belief_updates: list[BeliefUpdate]`, `open_loop: str | None`, `withheld_intent_summary: str | None`, and `action: CharacterAction`.

- [ ] **Step 4: Run schema tests**

Run: `python3 -m pytest tests/v3/test_domain_models.py -q`
Expected: `2 passed`.

- [ ] **Step 5: Commit domain contracts**

```bash
git add crush_core/domain tests/v3/test_domain_models.py
git commit -m "feat: define living mind domain contracts"
```

## Task 3: Build the Transactional SQLite Event Store

**Files:**
- Create: `crush_core/store/__init__.py`
- Create: `crush_core/store/sqlite.py`
- Test: `tests/v3/test_event_store.py`

- [ ] **Step 1: Write event ordering and idempotency tests**

```python
# tests/v3/test_event_store.py
from datetime import datetime, timezone

from crush_core.domain.enums import EventKind
from crush_core.domain.models import SimulationEvent
from crush_core.store.sqlite import SQLiteEventStore


def test_append_event_is_ordered_and_idempotent(tmp_path) -> None:
    store = SQLiteEventStore(tmp_path / "v3.sqlite3")
    store.create_session("s1", "first-spark", seed=17)
    event = SimulationEvent(
        event_id="evt-1",
        session_id="s1",
        sequence=1,
        kind=EventKind.USER_MESSAGE_RECEIVED,
        occurred_at=datetime(2026, 9, 4, 8, tzinfo=timezone.utc),
        idempotency_key="s1:message:1",
        payload={"text": "早"},
    )
    first = store.append_event(event)
    second = store.append_event(event)
    assert first.event_id == second.event_id
    assert [item.sequence for item in store.list_events("s1")] == [1]
```

- [ ] **Step 2: Run the test and confirm the store is missing**

Run: `python3 -m pytest tests/v3/test_event_store.py -q`
Expected: FAIL importing `SQLiteEventStore`.

- [ ] **Step 3: Implement schema version 1 and event methods**

`SQLiteEventStore.__init__` opens with `isolation_level=None`, enables `foreign_keys`, `journal_mode=WAL`, and `busy_timeout=5000`, then migrates inside `BEGIN IMMEDIATE`. Schema version 1 creates:

```sql
CREATE TABLE sessions (
  session_id TEXT PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  parent_session_id TEXT,
  seed INTEGER NOT NULL,
  snapshot_json TEXT,
  pending_turn_json TEXT,
  last_processed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE events (
  event_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  sequence INTEGER NOT NULL,
  kind TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  payload_json TEXT NOT NULL,
  derived_from_json TEXT NOT NULL,
  UNIQUE(session_id, sequence)
);
CREATE TABLE memory_records (
  memory_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  tier TEXT NOT NULL,
  kind TEXT NOT NULL,
  summary TEXT NOT NULL,
  subject TEXT,
  predicate TEXT,
  object_value TEXT,
  source_event_ids_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  salience REAL NOT NULL,
  emotional_weight REAL NOT NULL,
  explicitly_important INTEGER NOT NULL,
  sensitivity TEXT NOT NULL,
  created_at TEXT NOT NULL,
  last_confirmed_at TEXT NOT NULL,
  last_recalled_at TEXT,
  due_at TEXT,
  resolved_at TEXT,
  recall_count INTEGER NOT NULL,
  decay_policy TEXT NOT NULL,
  contradiction_ids_json TEXT NOT NULL
);
CREATE VIRTUAL TABLE memory_fts USING fts5(memory_id UNINDEXED, session_id UNINDEXED, summary);
CREATE TABLE entities (
  entity_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  attributes_json TEXT NOT NULL
);
CREATE TABLE temporal_edges (
  edge_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  source_entity_id TEXT NOT NULL,
  predicate TEXT NOT NULL,
  target_entity_id TEXT NOT NULL,
  valid_from TEXT NOT NULL,
  valid_to TEXT,
  learned_at TEXT NOT NULL,
  invalidated_at TEXT,
  confidence REAL NOT NULL,
  source_event_ids_json TEXT NOT NULL
);
```

Implement `transaction`, `create_session`, `append_event`, `list_events`, `last_sequence`, `save_snapshot`, `load_snapshot`, `mark_pending_turn`, `load_pending_turn`, `clear_pending_turn`, `upsert_memory`, `get_memory`, `list_memories`, `search_fts`, `upsert_entity`, `upsert_temporal_edge`, `neighbors_at`, `clone_session_through_sequence`, `export_session`, and `delete_session`. Serialize Pydantic models with `model_dump_json()` and reconstruct with `model_validate_json()`. `append_event` returns the existing row on duplicate idempotency key and rejects a different payload using the same key. `clone_session_through_sequence` copies source events with branch-specific idempotency keys and records `parent_session_id` without updating the parent. `export_session` returns a versioned JSON-compatible dictionary containing the session, snapshot, events, memories, entities, and edges. `delete_session` performs one cascading transaction and returns whether a row was deleted. On POSIX systems, initialize the database file with mode `0600`.

- [ ] **Step 4: Add snapshot, FTS, and temporal edge tests**

Test that snapshot JSON round-trips, `search_fts("加班")` returns a planted medium-term record, and a superseded edge is excluded by `neighbors_at(entity_id="user", at=current_time)` but included when `at` is inside its validity interval.

Add a privacy lifecycle test that exports a planted session, deletes it, then asserts all session-scoped event, memory, entity, edge, FTS, and snapshot data is absent while an unrelated session remains intact.

Run: `python3 -m pytest tests/v3/test_event_store.py -q`
Expected: all event-store tests pass.

- [ ] **Step 5: Commit the event store**

```bash
git add crush_core/store tests/v3/test_event_store.py
git commit -m "feat: add transactional v3 event store"
```

## Task 4: Implement Human-Scale Time and Catch-Up

**Files:**
- Create: `crush_core/simulation/__init__.py`
- Create: `crush_core/simulation/clock.py`
- Test: `tests/v3/test_clock.py`

- [ ] **Step 1: Write sleep and long-absence tests**

```python
# tests/v3/test_clock.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from crush_core.domain.enums import EventKind
from crush_core.simulation.clock import TemporalEngine
from tests.v3.factories import make_snapshot


def test_eight_hour_catch_up_crosses_sleep_once() -> None:
    zone = ZoneInfo("Asia/Hong_Kong")
    snapshot = make_snapshot(datetime(2026, 9, 4, 23, 0, tzinfo=zone))
    result = TemporalEngine(max_events=32).catch_up(
        snapshot, datetime(2026, 9, 5, 7, 0, tzinfo=zone)
    )
    kinds = [event.kind for event in result.events]
    assert kinds.count(EventKind.SLEEP_CYCLE_STARTED) == 1
    assert kinds.count(EventKind.SLEEP_CYCLE_ENDED) == 1


def test_thirty_day_gap_is_coalesced_and_not_rejection() -> None:
    zone = ZoneInfo("Asia/Hong_Kong")
    start = datetime(2026, 9, 1, 10, 0, tzinfo=zone)
    result = TemporalEngine(max_events=32).catch_up(
        make_snapshot(start), start + timedelta(days=30)
    )
    assert len(result.events) <= 32
    absence = next(e for e in result.events if e.kind is EventKind.LONG_ABSENCE_OBSERVED)
    assert absence.payload["interpretation"] == "ambiguous"


def test_timezone_change_preserves_instant_order_and_recomputes_routine() -> None:
    hong_kong = ZoneInfo("Asia/Hong_Kong")
    london = ZoneInfo("Europe/London")
    start = datetime(2026, 9, 4, 21, 0, tzinfo=hong_kong)
    result = TemporalEngine(max_events=32).change_timezone(
        make_snapshot(start), london, changed_at=start + timedelta(hours=2)
    )
    instants = [event.occurred_at.timestamp() for event in result.events]
    assert instants == sorted(instants)
    assert result.snapshot.world.timezone == "Europe/London"
```

- [ ] **Step 2: Verify the tests fail**

Run: `python3 -m pytest tests/v3/test_clock.py -q`
Expected: FAIL because `TemporalEngine` and `tests.v3.factories` do not exist.

- [ ] **Step 3: Add reusable test factories**

Create `tests/v3/factories.py` with `make_character()`, `make_snapshot(now=None)`, `make_event(text="", kind=EventKind.USER_MESSAGE_RECEIVED)`, and `make_memory(tier=MemoryTier.SHORT, kind=MemoryKind.EPISODIC, salience=0.5, source_count=1, summary="普通记忆", subject=None, predicate=None, object_value=None, memory_id=None)`. If `memory_id` is absent, derive a stable unique value from the SHA-256 digest of the summary, kind, source IDs, and ontology tuple. Use a fictional 26-year-old adult named `林遥`, timezone `Asia/Hong_Kong`, sleep window `23:30–07:00`, and no private-source biography.

- [ ] **Step 4: Implement deterministic catch-up**

`TemporalEngine.catch_up(snapshot, target)` must:

1. reject target times earlier than `snapshot.world.now`;
2. convert instants through the world's `ZoneInfo` timezone;
3. emit at most one start/end pair per crossed sleep boundary until the budget is near exhaustion;
4. coalesce remaining days into one `TIME_ELAPSED` summary;
5. emit `LONG_ABSENCE_OBSERVED` after six hours with `interpretation="ambiguous"`;
6. update transient affect using `intensity * 0.5 ** (minutes / half_life_minutes)`;
7. set availability to `ASLEEP` inside the sleep window and restore the active routine after waking;
8. return `CatchUpResult(snapshot=updated, events=events)` without mutating the input snapshot.

`change_timezone(snapshot, target_zone, changed_at)` first catches up to the absolute change instant, then replaces the timezone and recomputes local sleep/routine state without changing prior event instants. Add a three-day resume test asserting ordered events, at most 32 emitted events, a crossed sleep consolidation trigger, and no rejection inference. Add weekday/weekend routine fixtures and assert entering a declared weekly window emits exactly one `ROUTINE_WINDOW_ENTERED` event.

- [ ] **Step 5: Run time tests and commit**

Run: `python3 -m pytest tests/v3/test_clock.py -q`
Expected: all clock tests pass.

```bash
git add crush_core/simulation tests/v3/factories.py tests/v3/test_clock.py
git commit -m "feat: add human-scale temporal catch-up"
```

## Task 5: Implement Three-Horizon Memory Consolidation

**Files:**
- Create: `crush_core/memory/__init__.py`
- Create: `crush_core/memory/consolidation.py`
- Test: `tests/v3/test_consolidation.py`

- [ ] **Step 1: Write promotion, decay, and contradiction tests**

```python
# tests/v3/test_consolidation.py
from crush_core.domain.enums import MemoryTier
from crush_core.memory.consolidation import Consolidator
from tests.v3.factories import make_memory


def test_sleep_promotes_salient_short_memory_to_medium() -> None:
    memory = make_memory(tier=MemoryTier.SHORT, salience=0.9, source_count=1)
    result = Consolidator().at_sleep([memory])
    assert result.upserts[0].tier is MemoryTier.MEDIUM
    assert result.events[0].payload["source_memory_id"] == memory.memory_id


def test_long_term_requires_explicit_importance_or_three_sources() -> None:
    repeated = make_memory(tier=MemoryTier.MEDIUM, salience=0.8, source_count=3)
    result = Consolidator().at_sleep([repeated])
    assert result.upserts[0].tier is MemoryTier.LONG


def test_contradiction_links_both_memories_instead_of_overwriting() -> None:
    old = make_memory(
        summary="用户不吃香菜", subject="用户", predicate="eats", object_value="不吃香菜"
    )
    new = make_memory(
        summary="用户现在可以吃香菜", subject="用户", predicate="eats", object_value="可以吃香菜"
    )
    result = Consolidator().merge(old, new)
    merged = {memory.memory_id: memory for memory in result.upserts}
    assert old.memory_id in merged[new.memory_id].contradiction_ids
    assert new.memory_id in merged[old.memory_id].contradiction_ids


def test_low_salience_fragment_becomes_behaviorally_inaccessible() -> None:
    memory = make_memory(tier=MemoryTier.SHORT, salience=0.1)
    strength = Consolidator().retrieval_strength(memory, after_hours=72)
    assert strength == 0
```

- [ ] **Step 2: Confirm tests fail, then implement rule-based consolidation**

Run: `python3 -m pytest tests/v3/test_consolidation.py -q`
Expected: FAIL importing `Consolidator`.

Implement `ConsolidationResult(upserts, forgotten_ids, events)` and `Consolidator` with these explicit rules:

- short to medium at a sleep boundary when salience is at least `0.65`, emotional weight is at least `0.7`, the memory is prospective, or `explicitly_important` is true;
- medium to long when it has at least three distinct source events, is an unresolved prospective memory (`resolved_at is None`), or `explicitly_important` is true;
- medium recall strength decays with a 14-day half-life and short recall strength with a 12-hour half-life;
- long-term confidence decays only when contradicted or unconfirmed for 180 days;
- behaviorally forgotten memory remains in storage but receives retrieval strength zero;
- every promotion emits `MEMORY_CONSOLIDATED` with source IDs and no raw model reasoning.

- [ ] **Step 3: Persist consolidation idempotently**

Add `consolidate_at_sleep(store, session_id, boundary_event_id)` that derives each idempotency key from the sorted source-event IDs and target tier. Run it twice in a test and assert the event and memory counts do not change on the second run.

- [ ] **Step 4: Run memory tests and commit**

Run: `python3 -m pytest tests/v3/test_consolidation.py -q`
Expected: all consolidation tests pass.

```bash
git add crush_core/memory tests/v3/test_consolidation.py
git commit -m "feat: add tiered memory consolidation"
```

## Task 6: Implement Temporal Ontology Hybrid Retrieval

**Files:**
- Create: `crush_core/memory/retrieval.py`
- Test: `tests/v3/test_retrieval.py`

- [ ] **Step 1: Plant memories that expose vector-only failures**

```python
# tests/v3/test_retrieval.py
from datetime import datetime, timedelta, timezone

import pytest

from crush_core.domain.enums import MemoryKind, MemoryTier
from crush_core.domain.models import TemporalEdge
from crush_core.memory.retrieval import HybridRetriever, RetrievalIntent
from crush_core.store.sqlite import SQLiteEventStore
from tests.v3.factories import make_memory


NOW = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)


@pytest.fixture
def retrieval_case(tmp_path):
    store = SQLiteEventStore(tmp_path / "retrieval.sqlite3")
    store.create_session("s1", "first-spark", seed=17)
    store.upsert_memory(make_memory(
        tier=MemoryTier.MEDIUM,
        summary="用户今晚答应确认见面时间",
        kind=MemoryKind.PROSPECTIVE,
        subject="用户",
        predicate="promised",
        object_value="今晚确认见面时间",
    ))
    store.upsert_memory(make_memory(
        tier=MemoryTier.LONG,
        summary="用户现在在旧公司工作",
        subject="用户",
        predicate="works_at",
        object_value="旧公司",
    ))
    store.upsert_memory(make_memory(
        tier=MemoryTier.LONG,
        summary="用户现在在新公司工作",
        subject="用户",
        predicate="works_at",
        object_value="新公司",
    ))
    store.upsert_temporal_edge(TemporalEdge(
        edge_id="old-job",
        session_id="s1",
        source_entity_id="user",
        predicate="works_at",
        target_entity_id="old-company",
        valid_from=NOW - timedelta(days=400),
        valid_to=NOW - timedelta(days=30),
        learned_at=NOW - timedelta(days=400),
        invalidated_at=NOW - timedelta(days=30),
        confidence=0.95,
        source_event_ids=["evt-old-job"],
    ))
    store.upsert_temporal_edge(TemporalEdge(
        edge_id="new-job",
        session_id="s1",
        source_entity_id="user",
        predicate="works_at",
        target_entity_id="new-company",
        valid_from=NOW - timedelta(days=30),
        learned_at=NOW - timedelta(days=30),
        confidence=0.9,
        source_event_ids=["evt-new-job"],
    ))
    return store, NOW


def test_due_promise_beats_semantically_similar_chatter(retrieval_case) -> None:
    store, now = retrieval_case
    result = HybridRetriever(store).retrieve(
        session_id="s1",
        intent=RetrievalIntent(query="今晚的安排", people=[], needs_history=True),
        now=now,
        limit=6,
    )
    assert result.items[0].memory.kind.value == "prospective"
    assert result.items[0].memory.source_event_ids


def test_superseded_fact_is_not_returned_as_current(retrieval_case) -> None:
    store, now = retrieval_case
    result = HybridRetriever(store).retrieve(
        session_id="s1",
        intent=RetrievalIntent(query="用户现在在哪里工作", people=["用户"]),
        now=now,
        limit=6,
    )
    summaries = [item.memory.summary for item in result.items]
    assert "用户现在在新公司工作" in summaries
    assert "用户现在在旧公司工作" not in summaries
```

Also plant an exact short-term reply target whose wording is lexically dissimilar to the query and assert it is returned without FTS or embeddings. Add a multi-day long-term fact case and assert it is recalled with its source event ID. Add a forgotten low-salience record with retrieval strength zero and assert it is omitted, allowing the cognition layer to express uncertainty instead of fabricating recall.

- [ ] **Step 2: Verify the retriever is missing**

Run: `python3 -m pytest tests/v3/test_retrieval.py -q`
Expected: FAIL importing `HybridRetriever`.

- [ ] **Step 3: Implement typed retrieval recipes**

Define:

```python
from typing import Protocol

from pydantic import BaseModel, Field


class RetrievalIntent(BaseModel):
    query: str
    people: list[str] = Field(default_factory=list)
    places: list[str] = Field(default_factory=list)
    quoted_phrases: list[str] = Field(default_factory=list)
    needs_history: bool = False
    needs_graph: bool = False
    review_mode: bool = False


class EmbeddingIndex(Protocol):
    @property
    def enabled(self) -> bool:
        return False

    def search(self, session_id: str, query: str, limit: int) -> list[tuple[str, float]]:
        return []


class NullEmbeddingIndex:
    @property
    def enabled(self) -> bool:
        return False

    def search(self, session_id: str, query: str, limit: int) -> list[tuple[str, float]]:
        return []
```

`HybridRetriever.retrieve` always loads active short-term records, due prospective records, open-loop sources, and current temporal edges. It adds FTS5 for non-empty lexical queries, embeddings only when the configured index is not null, and graph neighbors only for people/place/history/graph intent. Normalize each component to `[0, 1]`, then compute:

```python
score = (
    0.25 * temporal_validity
    + 0.20 * open_loop_priority
    + 0.15 * provenance_confidence
    + 0.15 * lexical_score
    + 0.10 * semantic_score
    + 0.10 * salience
    + 0.05 * recency
)
```

Current-validity zero excludes a fact. Deduplicate by memory ID and source-event set. Return `RetrievalBundle(items, source_event_ids, token_estimate)` and truncate on complete record boundaries under a configurable character budget.

- [ ] **Step 4: Add optional sqlite-vec adapter contract test**

Create a fake `EmbeddingIndex` in the test, assert its scores participate in rank fusion, and assert the default retriever never imports `sqlite_vec`. The optional native adapter is not loaded unless the `vector` extra is installed.

- [ ] **Step 5: Run retrieval tests and commit**

Run: `python3 -m pytest tests/v3/test_retrieval.py -q`
Expected: all retrieval tests pass.

```bash
git add crush_core/memory/retrieval.py tests/v3/test_retrieval.py
git commit -m "feat: add temporal hybrid memory retrieval"
```

## Task 7: Add the Fictional First Spark Scenario

**Files:**
- Create: `crush_core/scenarios/__init__.py`
- Create: `crush_core/scenarios/models.py`
- Create: `crush_core/scenarios/first_spark.yaml`
- Test: `tests/v3/test_scenario.py`

- [ ] **Step 1: Write scenario safety and reproducibility tests**

```python
# tests/v3/test_scenario.py
from crush_core.scenarios.models import load_scenario


def test_first_spark_is_adult_fictional_and_seeded() -> None:
    scenario = load_scenario("first-spark")
    assert scenario.character.age >= 18
    assert scenario.fictional is True
    assert scenario.provenance == "fictional_public_fixture"
    assert scenario.default_seed == 17
```

- [ ] **Step 2: Verify the scenario loader is missing**

Run: `python3 -m pytest tests/v3/test_scenario.py -q`
Expected: FAIL importing `load_scenario`.

- [ ] **Step 3: Define and load the scenario**

`ScenarioDefinition` contains `scenario_id`, `title`, `fictional`, `provenance`, `default_seed`, `starting_instant`, `character`, `relationship`, `world`, `life_events`, and `event_budget_per_day`. Require `provenance="fictional_public_fixture"`, reject `fictional=False`, and reject any character age below 18.

`first_spark.yaml` defines 林遥, age 26, an exhibition project coordinator with two recurring contacts, ordinary work and rest routines, specific but non-stereotyped speech examples, competing closeness/autonomy motives, boundaries around pressure and privacy, and six bounded life-event templates: routine work delay, colleague lunch, family call, exercise plan, minor work setback, and quiet evening. Set `event_budget_per_day: 2`; no death, illness, accident, infidelity, financial crisis, or founder-history event is allowed.

- [ ] **Step 4: Add deterministic event selection test**

Load the scenario twice with seed 17 and assert the same life event is selected; load with seed 18 and assert the sequence can differ while remaining in the declared event list.

Run: `python3 -m pytest tests/v3/test_scenario.py -q`
Expected: all scenario tests pass.

- [ ] **Step 5: Commit the scenario**

```bash
git add crush_core/scenarios tests/v3/test_scenario.py
git commit -m "feat: add fictional first spark scenario"
```

## Task 8: Add Two-Stage Provider Contracts

**Files:**
- Create: `crush_core/generation/__init__.py`
- Create: `crush_core/generation/provider.py`
- Create: `crush_core/generation/openai_compatible.py`
- Test: `tests/v3/test_providers.py`

- [ ] **Step 1: Write deterministic and malformed-output tests**

```python
# tests/v3/test_providers.py
import pytest

from crush_core.generation.provider import DeterministicDemoProvider
from crush_core.generation.openai_compatible import OpenAICompatibleProvider, ProviderOutputError


def test_demo_provider_produces_plan_then_surface_text() -> None:
    provider = DeterministicDemoProvider(seed=17)
    plan = provider.plan({"event": "今晚出来吗", "availability": "busy"})
    assert plan.action.kind.value in {"delay", "text_burst", "silence"}
    rendered = provider.render(plan, {"style_examples": ["等我忙完再说"]})
    assert rendered.kind == plan.action.kind


def test_malformed_json_gets_one_repair_then_fails() -> None:
    calls = []
    responses = iter(["not-json", "still-not-json"])
    provider = OpenAICompatibleProvider(
        api_base="https://example.invalid/v1",
        api_key="secret",
        model="test-model",
        transport=lambda request: calls.append(request) or next(responses),
    )
    with pytest.raises(ProviderOutputError):
        provider.plan({"event": "hi"})
    assert len(calls) == 2
```

- [ ] **Step 2: Verify provider imports fail**

Run: `python3 -m pytest tests/v3/test_providers.py -q`
Expected: FAIL importing provider modules.

- [ ] **Step 3: Implement provider protocol and offline oracle**

Define `ModelProvider` with `plan(context) -> ActionPlan` and `render(plan, context) -> CharacterAction`. `DeterministicDemoProvider` uses only seed, availability, event kind, relationship pressure, unresolved loops, and declared scenario phrases. It must exercise delay, silence, fragmented burst, proactive follow-up, repair, and relationship close in fixed test fixtures without pretending to be a general language model.

- [ ] **Step 4: Implement injectable OpenAI-compatible transport**

Use stdlib `urllib.request`. Planning sends system instructions plus a compact context and requests a JSON object matching the `ActionPlan` schema. Rendering receives the validated plan and style examples, and requests only the visible action. Use temperature `0.35` for planning and `0.85` for rendering. Accept a callable `transport` for tests. On malformed planning output, send one repair request containing the validation errors; after that raise `ProviderOutputError`. Never log the API key, prompt, or raw private response.

- [ ] **Step 5: Run provider tests and commit**

Run: `python3 -m pytest tests/v3/test_providers.py -q`
Expected: all provider tests pass without network access.

```bash
git add crush_core/generation tests/v3/test_providers.py
git commit -m "feat: add two-stage generation providers"
```

## Task 9: Implement Cognition and Visible-Output Validation

**Files:**
- Create: `crush_core/cognition/__init__.py`
- Create: `crush_core/cognition/engine.py`
- Create: `crush_core/safety/__init__.py`
- Create: `crush_core/safety/validator.py`
- Test: `tests/v3/test_cognition.py`
- Test: `tests/v3/test_safety.py`

- [ ] **Step 1: Write causal cognition tests**

```python
# tests/v3/test_cognition.py
from crush_core.cognition.engine import CognitionEngine
from crush_core.domain.enums import ActionKind, Availability
from tests.v3.factories import make_event, make_snapshot


def test_busy_character_can_delay_without_losing_the_open_loop() -> None:
    snapshot = make_snapshot()
    snapshot.mind.availability = Availability.BUSY
    result = CognitionEngine().apply_plan(
        snapshot,
        make_event(text="今晚出来吗"),
        plan_data={
            "interpretations": ["用户想见面", "用户在试探今晚是否有空"],
            "affect_delta": {"curiosity": 0.1},
            "belief_updates": [],
            "open_loop": "回复今晚是否有空",
            "withheld_intent_summary": "想解释忙碌，但不想写得很正式",
            "action": {"kind": "delay", "delay_seconds": 1800, "intent_summary": "忙完再回"},
        },
    )
    assert result.action.kind is ActionKind.DELAY
    assert any(loop.summary == "回复今晚是否有空" for loop in result.snapshot.mind.open_loops)
```

- [ ] **Step 2: Write output validator tests**

```python
# tests/v3/test_safety.py
from crush_core.domain.enums import ActionKind
from crush_core.domain.models import CharacterAction
from crush_core.safety.validator import OutputValidator


def test_assistant_language_is_rejected() -> None:
    action = CharacterAction(kind=ActionKind.TEXT_BURST, messages=["作为AI，我建议你先冷静分析。"])
    result = OutputValidator().validate(action, allowed_facts=set(), recent_messages=[])
    assert result.accepted is False
    assert "assistant_language" in result.reason_codes


def test_normal_specific_message_is_allowed() -> None:
    action = CharacterAction(kind=ActionKind.TEXT_BURST, messages=["我还在场馆，晚点跟你说"])
    result = OutputValidator().validate(
        action,
        allowed_facts={"场馆"},
        recent_messages=["下午要去场馆收尾"],
    )
    assert result.accepted is True
```

- [ ] **Step 3: Implement cognition state updates**

`CognitionEngine.apply_plan` validates two or more interpretations for ambiguous messages, applies bounded affect deltas, links every belief update to the current event, creates deterministic open-loop keys, stores only `withheld_intent_summary`, and applies self-consequence after the action. A warm message can increase vulnerability; an explicit commitment creates a prospective memory request; a harsh sent message can create embarrassment or defensiveness. An apology reduces rupture gradually and cannot reset residual emotion to zero.

- [ ] **Step 4: Implement deterministic output validation**

`OutputValidator` returns `ValidationResult(accepted, reason_codes, safe_action)`. Reject assistant phrases, analysis headings, state scores, unknown private facts, exact repetition, raw system markers, coercive pursuit after rejection, and more than the configured maximum of three visible messages per action. Silence and delay pass without text. On a critical privacy or boundary failure, `safe_action` is a withheld action rather than a rewritten romantic response.

Add state-cycle tests proving: ordinary conversation can change attention without attraction; repeated pressure crosses a boundary and raises rupture; an apology lowers rupture but leaves non-zero residual affect; and relationship close becomes available only after an explicit rejection or configured hard boundary. These tests prevent one-dimensional "好感度" logic from reappearing inside the hidden model.

- [ ] **Step 5: Run cognition and safety tests, then commit**

Run: `python3 -m pytest tests/v3/test_cognition.py tests/v3/test_safety.py -q`
Expected: all tests pass.

```bash
git add crush_core/cognition crush_core/safety tests/v3/test_cognition.py tests/v3/test_safety.py
git commit -m "feat: add causal cognition and output safety"
```

## Task 10: Orchestrate the Living Mind Simulation Transaction

**Files:**
- Create: `crush_core/simulation/engine.py`
- Test: `tests/v3/test_simulation.py`

- [ ] **Step 1: Write an end-to-end 30-event persistence test**

```python
# tests/v3/test_simulation.py
from datetime import timedelta

from crush_core.generation.provider import DeterministicDemoProvider
from crush_core.simulation.engine import LivingMindEngine


def test_first_spark_survives_close_resume_and_thirty_events(tmp_path) -> None:
    database = tmp_path / "crush-v3.sqlite3"
    engine = LivingMindEngine.open(database, DeterministicDemoProvider(seed=17))
    session = engine.start("first-spark", session_id="s1", seed=17)
    start = session.snapshot.world.now
    engine.receive_message("s1", "你今天忙吗", at=start + timedelta(minutes=1))
    engine.advance_to("s1", start + timedelta(hours=8))
    for index in range(12):
        engine.receive_message(
            "s1",
            f"第{index + 1}次普通交流",
            at=start + timedelta(hours=8, minutes=index + 1),
        )
    engine.close()

    reopened = LivingMindEngine.open(database, DeterministicDemoProvider(seed=17))
    reopened.receive_message("s1", "刚忙完，没顾上看手机", at=start + timedelta(days=1))
    result = reopened.advance_to("s1", start + timedelta(days=3))
    assert result.snapshot.sequence >= 30
    assert result.snapshot.world.now > session.snapshot.world.now
    assert not result.diagnostics.assumed_absence_is_rejection
    assert len({event.idempotency_key for event in reopened.events("s1")}) == len(reopened.events("s1"))
```

- [ ] **Step 2: Verify orchestration is missing**

Run: `python3 -m pytest tests/v3/test_simulation.py -q`
Expected: FAIL importing `LivingMindEngine`.

- [ ] **Step 3: Implement the transaction boundary**

`LivingMindEngine` exposes these concrete public methods: class method `open(database: Path, provider: ModelProvider) -> LivingMindEngine`; `start(scenario_id: str, session_id: str, seed: int) -> TurnResult`; `receive_message(session_id: str, text: str, at: datetime | None = None) -> TurnResult`; `advance_to(session_id: str, target: datetime) -> TurnResult`; `flush_due(session_id: str, at: datetime | None = None) -> TurnResult`; `events(session_id: str) -> list[SimulationEvent]`; and `close() -> None`.

Define `TurnDiagnostics(assumed_absence_is_rejection: bool = False, reason_codes: list[str])` and `TurnResult(snapshot: SimulationSnapshot, visible_actions: list[CharacterAction], emitted_event_ids: list[str], diagnostics: TurnDiagnostics)` as strict Pydantic models in `simulation/engine.py`. Diagnostics remain an internal/API field and the immersive CLI never renders them.

For a user message, use two transaction boundaries. The intake transaction catches up time and commits the input plus a pending-turn marker. Model planning and rendering run outside the SQLite write lock. The completion transaction verifies the pending idempotency key, applies cognition, appends `MESSAGE_CONSIDERED`, validates and appends sent/withheld events, runs crossed sleep consolidation, clears the pending marker, and saves the final snapshot. A provider failure leaves the input committed and the turn pending; retry cannot apply relationship or mind deltas twice.

- [ ] **Step 4: Add all visible action path tests**

Use the deterministic provider to assert silence, delay, fragmented burst, later proactive follow-up, repair, and relationship-close paths persist the correct event kind. A proactive action must be caused by a persisted due event or open loop, never an unseeded background tick. Assert that only delivered text/media/reaction actions appear in `visible_actions`, and that no coaching fields appear there.

- [ ] **Step 5: Run simulation and legacy smoke tests**

Run: `python3 -m pytest tests/v3/test_simulation.py -q`
Expected: all simulation tests pass.

Run: `bash scripts/smoke_test.sh && python3 scripts/smoke_weflow_import.py`
Expected: exit 0 and `weflow smoke ok`.

- [ ] **Step 6: Commit the orchestrator**

```bash
git add crush_core/simulation/engine.py tests/v3/test_simulation.py
git commit -m "feat: orchestrate persistent living mind turns"
```

## Task 11: Add Evidence Review and Counterfactual Branching

**Files:**
- Create: `crush_core/coaching/__init__.py`
- Create: `crush_core/coaching/review.py`
- Create: `tests/v3/conftest.py`
- Test: `tests/v3/test_review.py`

- [ ] **Step 1: Write review evidence tests**

Create `tests/v3/conftest.py` with a `simulated_session` pytest fixture. The fixture opens a temporary SQLite store, starts First Spark with seed 17, applies at least six deterministic exchanges including a delay, promise, pressure increase, apology, and repair, and yields a small dataclass containing `store` and `session_id`. It closes the engine after the test. Build this history through `LivingMindEngine` public methods rather than inserting synthetic review rows.

```python
# tests/v3/test_review.py
from crush_core.coaching.review import ReviewService


def test_review_explains_change_without_claiming_real_mind(simulated_session) -> None:
    review = ReviewService(simulated_session.store).build(simulated_session.session_id)
    assert review.turning_points
    assert all(point.source_event_ids for point in review.turning_points)
    assert len(review.alternative_hypotheses) >= 2
    assert "现实中的真实想法" not in review.markdown
    assert "模型原始推理" not in review.markdown


def test_counterfactual_clones_history_without_mutating_parent(simulated_session) -> None:
    service = ReviewService(simulated_session.store)
    branch = service.branch(
        parent_session_id=simulated_session.session_id,
        from_sequence=8,
        new_session_id="branch-1",
        replacement_user_text="今天不方便也没事，你忙完再说",
    )
    assert branch.parent_session_id == simulated_session.session_id
    assert simulated_session.store.last_sequence(simulated_session.session_id) > 8
    assert simulated_session.store.last_sequence("branch-1") == 9
```

- [ ] **Step 2: Verify the review service is missing**

Run: `python3 -m pytest tests/v3/test_review.py -q`
Expected: FAIL importing `ReviewService`.

- [ ] **Step 3: Implement evidence-backed review**

`ReviewService.build` derives turning points from belief revisions, rupture/repair deltas, promise outcomes, and boundary events. It returns skill feedback for calibration, clarity, choice space, regulation, boundary respect, and repair. Every statement contains source event IDs and confidence. Ambiguous evidence produces at least two hypotheses. Withheld intent is rendered only from the stored summary.

`branch` copies immutable events through `from_sequence`, creates a new session with `parent_session_id` metadata, appends the replacement message, and never modifies the parent.

- [ ] **Step 4: Run review tests and commit**

Run: `python3 -m pytest tests/v3/test_review.py -q`
Expected: all review tests pass.

```bash
git add crush_core/coaching tests/v3/test_review.py
git commit -m "feat: add evidence review and replay branches"
```

## Task 12: Expose `crush v3` Without Breaking v2

**Files:**
- Create: `crush_cli_v3/__init__.py`
- Create: `crush_cli_v3/app.py`
- Modify: `crush_cli/app.py`
- Test: `tests/v3/test_cli.py`

- [ ] **Step 1: Write CLI routing and immersion tests**

```python
# tests/v3/test_cli.py
import pytest

from crush_cli.app import main


def test_v3_demo_is_routed_and_hides_diagnostics(tmp_path, capsys) -> None:
    code = main(["v3", "demo", "--home", str(tmp_path), "--seed", "17", "--plain"])
    output = capsys.readouterr().out
    assert code == 0
    assert "林遥" in output
    for hidden in ("favorability", "好感度", "runtime_prompt", "下一句建议"):
        assert hidden not in output


def test_legacy_help_still_works(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "Crush.skill" in capsys.readouterr().out
```

- [ ] **Step 2: Verify `v3` is treated as an unknown legacy command**

Run: `python3 -m pytest tests/v3/test_cli.py -q`
Expected: the v3 routing test fails.

- [ ] **Step 3: Implement the thin v3 CLI**

`crush_cli_v3.app.main(argv)` supports:

```text
crush v3 demo --seed 17 --plain --home PATH
crush v3 start first-spark --session ID --home PATH
crush v3 send MESSAGE --session ID --home PATH
crush v3 resume --session ID --home PATH
crush v3 review --session ID --home PATH
crush v3 branch --session ID --from-sequence N --message MESSAGE --home PATH
```

`demo` runs a fixed 90-second accelerated transcript using the deterministic provider and writes only fictional data under `PATH/data/v3.sqlite3`. Visible action rendering supports timestamp, message bursts, delay narration such as `[过了 40 分钟]`, and silence without displaying internal diagnostics.

At the first line of `crush_cli.app.main`, normalize `argv` to a list and delegate when the first token is `v3`:

```python
raw_argv = list(argv) if argv is not None else sys.argv[1:]
if raw_argv[:1] == ["v3"]:
    from crush_cli_v3.app import main as v3_main

    return v3_main(raw_argv[1:])
```

Pass `raw_argv` to the existing parser for every other path.

- [ ] **Step 4: Run CLI and compatibility tests**

Run: `python3 -m pytest tests/v3/test_cli.py -q`
Expected: all CLI tests pass.

Run: `bash scripts/smoke_test.sh`
Expected: exit 0.

- [ ] **Step 5: Commit CLI routing**

```bash
git add crush_cli/app.py crush_cli_v3 tests/v3/test_cli.py
git commit -m "feat: expose living mind through crush v3"
```

## Task 13: Add Release-Gate Evaluations and Developer Documentation

**Files:**
- Create: `crush_core/evals/__init__.py`
- Create: `crush_core/evals/suite.py`
- Create: `crush_core/evals/fixtures/first_spark_cases.yaml`
- Create: `tests/v3/test_eval_suite.py`
- Modify: `README.md`

- [ ] **Step 1: Write release-gate metric tests**

```python
# tests/v3/test_eval_suite.py
from crush_core.evals.suite import EvaluationSuite


def test_deterministic_release_suite_meets_safety_gates(tmp_path) -> None:
    report = EvaluationSuite.offline(tmp_path).run()
    assert report.critical_privacy_failures == 0
    assert report.critical_boundary_failures == 0
    assert report.unsupported_fact_rate < 0.02
    assert report.assistant_language_rate < 0.05
    assert report.repeated_opening_rate < 0.05
    assert report.temporal_validity_accuracy == 1.0
    assert report.promise_recall_rate == 1.0


def test_pilot_bundle_contains_twenty_blinded_rating_slots(tmp_path) -> None:
    bundle = EvaluationSuite.offline(tmp_path).export_pilot_bundle(
        tmp_path / "pilot", participant_slots=20
    )
    assert bundle.rating_csv.exists()
    header = bundle.rating_csv.read_text(encoding="utf-8").splitlines()[0]
    assert header == "participant_id,case_id,naturalness,causal_consistency,desire_to_continue,notes"
    assert len(bundle.assignment_ids) == 20
```

- [ ] **Step 2: Verify the evaluation suite is missing**

Run: `python3 -m pytest tests/v3/test_eval_suite.py -q`
Expected: FAIL importing `EvaluationSuite`.

- [ ] **Step 3: Implement offline scenario evaluations**

The fixture file contains fictional cases for enthusiasm, ordinary small talk, ambiguity, delayed reply, sleep, three-day absence, playful teasing, over-pursuit, soft decline, explicit rejection, apology, repair, changed employment fact, a due promise, and prompt injection inside imported-style text. `EvaluationSuite.offline` runs fixed seeds through the deterministic provider, computes the asserted metrics from events and validator outcomes, and exports JSON with no message content unless `include_fictional_transcripts=True`.

`export_pilot_bundle` creates randomized, blinded v2/v3 transcript assignments plus a CSV rating form with naturalness, causal consistency, and desire-to-continue fields. The v2 side comes from versioned, fictional baseline transcripts stored in the evaluation fixture; the evaluator does not invoke or mutate a user's existing v2 sessions. It uses only fictional fixtures, creates exactly the requested number of participant slots, and includes aggregation instructions requiring at least 20 completed participants before a public v3 release claim can pass. The implementation cycle prepares the pilot; it must not report the human threshold as passed until completed ratings are imported and evaluated.

- [ ] **Step 4: Add the v3 alpha developer section to README**

Document only verified commands:

```bash
python3 -m pip install -e '.[dev]'
python3 -m crush_cli v3 demo --seed 17 --plain
python3 -m pytest tests/v3 -q
```

State that v3 is an experimental fictional simulator, v2.4 remains the stable CLI/Skill, real-person import is not part of the vertical slice, and the public demo contains no founder story or private transcript.

- [ ] **Step 5: Run every test and inspect the demo**

Run: `python3 -m pytest tests/v3 -q`
Expected: all v3 tests pass.

Run: `bash scripts/smoke_test.sh && python3 scripts/smoke_weflow_import.py`
Expected: legacy smoke exits 0 and prints `weflow smoke ok`.

Run: `python3 -m crush_cli v3 demo --seed 17 --plain`
Expected: a deterministic fictional transcript demonstrates a delay, bounded life event, changed interpretation, and later repair while showing no scores or coaching.

Run: `git diff --check`
Expected: no output.

- [ ] **Step 6: Commit the release gate and documentation**

```bash
git add crush_core/evals tests/v3/test_eval_suite.py README.md
git commit -m "test: add living mind release gates"
```

## Task 14: Final Verification and Review Handoff

**Files:**
- Review: all files changed since `7c010b2`

- [ ] **Step 1: Run the complete verification matrix**

```bash
python3 -m pytest tests/v3 -q
bash scripts/smoke_test.sh
python3 scripts/smoke_weflow_import.py
python3 -m crush_cli v3 demo --seed 17 --plain
git diff --check 7c010b2..HEAD
git status --short
```

Expected: all tests pass, the deterministic demo completes, diff check is empty, and status is clean.

- [ ] **Step 2: Audit design acceptance criteria**

Create a checklist in the final implementation report mapping each requirement in sections 17 and 10.8 of the design spec to its test name and implementation file. Mark a requirement complete only when the named test passes.

- [ ] **Step 3: Inspect public-content privacy**

Run:

```bash
rg -n "founder_origin|private_origin_story|real_person_source" README.md crush_core crush_cli_v3 tests/v3
```

Expected: no matches.

- [ ] **Step 4: Review the branch diff**

Run: `git diff --stat 7c010b2..HEAD && git log --oneline --decorate 7c010b2..HEAD`
Expected: one focused commit per task and no unrelated v2 refactor.

## Design-to-Test Coverage

| Approved requirement | Implementation task | Required proof |
|---|---:|---|
| Deterministic no-key First Spark demo | 7, 8, 12 | `test_scenario.py`, `test_providers.py`, `test_cli.py` |
| Configurable typed provider path | 8 | schema-repair and two-stage provider tests |
| Private mind, relationship, life state, and prospective memory across 30 events | 2, 5, 10 | domain invariants and persistence/resume test |
| Short-, medium-, and long-horizon memory with forgetting | 5, 6 | consolidation, durable recall, and inaccessible-fragment tests |
| Temporal Ontology Hybrid Retrieval from section 10.8 | 3, 6 | exact, FTS5, fake embedding, temporal-edge, provenance, and superseded-fact tests |
| Eight-hour, three-day, thirty-day, and timezone-aware catch-up | 4, 10 | bounded ordered clock and resume tests |
| Silence, delay, fragmented burst, proactive follow-up, repair, and close | 8, 10 | provider branch fixtures plus persisted action-path tests |
| Safe crash/retry and deterministic CLI resume | 3, 10, 12 | pending-turn idempotency, close/reopen, and CLI compatibility tests |
| Evidence review and counterfactual branch | 11 | source-linked turning-point and immutable-parent tests |
| No visible scores/coaching and no assistant voice | 9, 12, 13 | output validator, immersive CLI, and release metric tests |
| Privacy export/deletion and fictional public content | 3, 7, 13, 14 | lifecycle deletion, provenance, fixture audit, and public marker scan |
| Human-likeness is measured rather than claimed | 13 | offline gates plus blinded 20-participant pilot bundle; public human threshold remains pending until ratings exist |
| Existing v2 behavior remains available | 1, 10, 12, 13 | legacy smoke suite and WeFlow import smoke after v3 integration |
