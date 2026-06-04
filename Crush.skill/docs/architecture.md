# Crush.skill Architecture

## 1. Core Principle

Crush.skill separates deterministic relationship mechanics from natural language generation:

- Rule engines calculate state, evidence, boundaries, defense, and relationship inertia.
- Import and distillation engines turn chat records into persona memory and explainable reports.
- The host LLM or CLI model performs natural persona expression.
- Tool JSON, scores, and runtime prompts should stay hidden unless the user asks for diagnostics.

## 2. Product Surfaces

- Agent Skill: `Crush.skill/execute.py` exposes actions for Claude Code, OpenClaw, QwenPaw, WorkBuddy, Codex, and Cursor.
- Standalone CLI: `crush_cli/app.py` provides local terminal chat, model wizard, multilingual UI, proactive timeline, and local memory.

Both surfaces share the same runtime and memory system.

## 3. Core Modules

- `engines/persona_engine.py`: 5-layer persona model and hidden runtime prompt construction.
- `engines/chat_import.py`: WeChat / WhatsApp / QQ / CSV / pasted transcript parsing and initial persona inference.
- `engines/pragmatics_engine.py`: slang, memes, soft declines, tests, subtext, boundaries, and neediness signals.
- `engines/dialogue_analyzer.py`: local/LLM dialogue analysis entrypoint.
- `engines/state_engine.py`: nonlinear relationship state update.
- `engines/defense_engine.py`: defense trigger logic and reasons.
- `engines/coach_engine.py`: relationship readout, risk level, and next-move coaching.
- `engines/distillation_engine.py`: evidence map, relationship radar, training playbook, and validation limits.
- `engines/memory_engine.py`: SQLite sessions, episodes, state history, timeline events, summaries, and local retrieval.
- `engines/memory_backend.py`: SQLite source-of-truth plus optional mem0 bridge.
- `engines/replay_engine.py`: postmortem / relationship replay report.
- `engines/reality_import_engine.py`: legacy relationship-text import.

## 4. Memory Design

Default memory is local-first:

1. Persona Memory: imported 5-layer persona, speech fingerprints, inside jokes, boundaries, shared context.
2. Episode Memory: imported chat records, user turns, NPC replies.
3. State Memory: snapshots, deltas, tags, timeline events.
4. Summary Memory: compressed local summary for context-limit safety.

Retrieval uses local keyword overlap plus lightweight vector scoring. Optional mem0 can be enabled with `CRUSH_MEMORY_BACKEND=mem0`, but SQLite remains the source-of-truth.

## 5. Why Not Force External Vector DB

- External vector databases increase setup friction for an open-source skill.
- Imported relationship chats are sensitive; local-first is safer by default.
- Persona memory + episode memory + summaries handle most context-limit issues.
- Teams needing large-scale retrieval can later add Chroma, PGVector, Milvus, or mem0 as an optional backend.

## 6. Runtime Actions

`execute.py` supports:

- `quick_start`
- `custom_sandbox`
- `reality_import`
- `chat_import`
- `distillation_report`
- `chat_turn`
- `record_reply`
- `proactive_prompt`
- `postmortem`
- `timeline_append`
- `dashboard`
- `list_sessions`
- `delete_session`
- `let_go`
- `configure_llm`

## 7. Runtime Contract

For `/chat`:

1. Run `chat_turn` and receive `runtime_prompt`, state, delta, analysis, coach, and memory context.
2. Treat `runtime_prompt` as a hidden system prompt.
3. Generate exactly one natural NPC reply in persona voice.
4. Show only the NPC reply to the user unless diagnostics were requested.
5. Save the NPC reply with `record_reply`; do not call `chat_turn` again just to persist the reply.

For `/import-chats`:

1. Run `chat_import`.
2. Show persona summary, speech fingerprint, relationship state, and distillation preview.
3. Tell the user they can now chat or run `/crush-distill`.

For `/crush-distill`:

1. Run `distillation_report`.
2. Show the Markdown report.
3. Keep sensitive labels probabilistic and evidence-based.

## 8. CLI Timeline

The CLI adds a local proactive timeline:

- Ta can send a proactive message based on time, archetype, warmth, initiative, defense, and recent memory.
- After Ta sends a proactive message, the timeline enters pending wait state.
- Follow-ups happen only after a natural patience window.
- Long ignored streaks and low-priority replies reduce initiative and warmth.
- `/stop` pauses the timeline; `/continue` resumes it.
