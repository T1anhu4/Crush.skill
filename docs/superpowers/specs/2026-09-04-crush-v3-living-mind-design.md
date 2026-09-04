# Crush.skill v3 Living Mind Vertical Slice Design

Status: approved direction with memory/time amendment, implementation-gate specification

Date: 2026-09-04

Target branch: `codex/v3-living-mind`

## 1. Decision Summary

Crush.skill v3 will be a local-first relationship training simulator whose main differentiator is a persistent, event-driven character mind. The character must have a life, incomplete thoughts, changing interpretations, limited attention, boundaries, and consequences that persist across turns. Short-, medium-, and long-term memory plus human-scale time cycles preserve continuity when a user leaves to work, sleep, or live their life. The product will not claim that a model is conscious or that it reveals a real person's thoughts.

The first implementation cycle is deliberately limited to one end-to-end vertical slice named **First Spark**. It will prove or disprove the human-likeness architecture before the project expands into a desktop app, mobile notifications, cloud sync, or a large scenario marketplace.

The existing v2.4 CLI and Agent Skill remain operational during the migration. v3 is built beside them, then compatibility adapters move existing commands onto the new core incrementally.

## 2. Product Promise

> A relationship flight simulator where the other person does not wait motionless for the user's next prompt.

The user practices four transferable abilities:

1. Notice ambiguous social and emotional signals without pretending to read minds.
2. Express interest and needs clearly without pressure or covert manipulation.
3. Regulate anxiety when feedback is delayed or uncertain.
4. Recognize and respect boundaries, soft declines, explicit rejection, and incompatibility.

Success is not defined as making the character like the user. A session can end well when the user recognizes incompatibility early, accepts a rejection, repairs a misunderstanding, or communicates honestly.

## 3. Product Boundaries

### 3.1 Required boundaries

- The founder's personal origin story must never appear in product copy, examples, fixtures, generated scenarios, release notes, telemetry, or marketing assets.
- The product identifies itself once during onboarding as a simulation. It does not repeatedly break immersion during a session.
- It never claims that a character is conscious or is a real person.
- Imported chats create a fictionalized simulation based on permitted style signals. They do not authorize impersonation, contacting the source person, or presenting inferred thoughts as facts.
- Astrology can be an optional narrative skin. It is not a causal personality model and cannot override observed behavior.
- The simulator must not teach silent treatment, jealousy induction, false scarcity, compliance tests, stalking, harassment, deception, or emotional dependency.
- Minors are out of scope for romantic scenarios.

### 3.2 Non-goals for the first implementation cycle

- No cloud account, billing, social feed, mobile app, or cross-device sync.
- No continuous model calls while the process is idle.
- No perfect digital twin of a real person.
- No compatibility score, visible attraction meter, or optimal-answer tree during immersion.
- No multi-agent framework as a goal by itself.

## 4. First Spark Experience

### 4.1 Entry

The user starts one fictional scenario: two adults met naturally, exchanged contact details, and are in the first several days of messaging. Setup asks for only scenario pace, the user's preferred form of address, and accessibility/language settings. The system selects a seeded character dossier so every run is reproducible for debugging but not predictable to the user.

### 4.2 Immersion

The primary view contains only a familiar message timeline. It does not show analysis, scores, coaching, state changes, or suggested replies.

The character may:

- reply immediately, delay, ignore one part of a message, or choose not to reply;
- send one message, a fragmented burst, a media action, or a later follow-up;
- change wording before sending without exposing raw model reasoning;
- remember promises, jokes, missed plans, emotional residue, and unresolved questions;
- misunderstand the user, retain uncertainty, and revise a belief when new evidence arrives;
- introduce details from their simulated life rather than orbiting the user;
- reduce contact or end the relationship when a boundary is repeatedly crossed.

### 4.3 Time

First Spark supports real time and an accelerated demo clock. Meaningful events, not fixed polling intervals, advance the mind. When the process is closed, it does not claim to keep thinking. On resume, a deterministic catch-up step evaluates elapsed time and creates only the events that would still matter.

The timeline distinguishes normal life absence from relationship behavior. A user being asleep, at work, commuting, or away from the app is ambiguous evidence. The character may notice a gap, but cannot automatically conclude that the user is ignoring them. Interpretation depends on prior plans, normal rhythm, explicit expectations, time zone, repeated patterns, and whether a message genuinely called for a timely response.

The simulated person follows multiple nested cycles:

- **Circadian cycle:** sleep, waking, commuting, meals, focused work, social time, and evening decompression affect availability and expression.
- **Weekly rhythm:** workdays, weekends, recurring commitments, and known plans create predictable but imperfect routines.
- **Conversation cycle:** opening, active exchange, natural pause, unresolved loop, follow-up window, and closure.
- **Emotional cycle:** activation, appraisal, residual feeling, regulation, and decay occur over different durations.
- **Relationship cycle:** curiosity, familiarity, trust formation, rupture, repair, plateau, distance, and closure evolve over days or weeks rather than one score update.

During sleep, the character does not send ordinary chat messages. A sleep-boundary event decays transient emotion and consolidates important memories. Long gaps expire some open loops, preserve promises and high-salience moments, and create uncertainty rather than automatic punishment.

### 4.4 Review

A review becomes available at a natural checkpoint or session end. It includes:

- **The moment the interpretation changed:** evidence-backed state transitions.
- **Unsent intent summaries:** structured statements such as "wanted reassurance but chose not to ask," never raw chain-of-thought.
- **Alternative hypotheses:** at least two plausible interpretations when evidence is ambiguous.
- **Counterfactual branch:** replay one decision from the same snapshot with a different user response.
- **Skill feedback:** signal calibration, emotional regulation, clarity, space for choice, boundary respect, and repair.

## 5. Why v2 Feels Mechanical

The current runtime is a response generator wrapped in relationship scores:

- It makes one ordinary completion request per visible reply.
- The prompt is dominated by labels, scores, prohibitions, and coaching directives.
- Persona presets are archetype stereotypes rather than autobiographical, contradictory people.
- State changes mainly when the user speaks. The character's own choices do not meaningfully change the character.
- The runtime requires an immediate textual answer even when silence or delay is the natural action.
- The proactive timeline is a probability timer with templated time-of-day context, not a causal life model.
- The same fixed temperature and short-output requirement compress every personality toward similar text.
- There is no human-likeness evaluation harness.

v3 therefore changes the state model and generation contract rather than adding more anti-AI wording.

## 6. Architecture Decision

### 6.1 Core choices

- **Python 3.11+ domain package** with typed Pydantic models.
- **SQLite event store** as the local source of truth, with explicit migrations and transactional snapshots.
- **Temporal ontology hybrid retrieval** over the SQLite source of truth: exact temporal queries and FTS5 first, optional embeddings second, bounded graph traversal third.
- **Provider-neutral model interface** designed for OpenAI-compatible, Anthropic, Gemini, and deterministic fake providers. The vertical slice implements the deterministic fake provider and one OpenAI-compatible HTTP provider; native Anthropic and Gemini v3 adapters belong to the compatibility cycle. Existing v2 provider support remains unchanged meanwhile.
- **MCP and Agent Skill adapters** as transports around the domain API, not as the domain core.
- **Optional OpenAI Agents SDK adapter** for applications that want its sessions, guardrails, and tracing. Sensitive tracing is disabled by default.
- **No LangGraph dependency in the vertical slice.** The workflow is a bounded domain state machine; a graph runtime can be added later if human approvals or distributed durability justify it.

### 6.2 Proposed package boundaries

```text
crush_core/
  domain/          # immutable events, character, mind, relationship, world, actions
  cognition/       # observation, appraisal, belief revision, intent planning
  simulation/      # event loop, clock, scheduler, catch-up, deterministic RNG
  generation/      # provider interface, structured planner, surface renderer
  memory/          # event store, snapshots, retrieval, migrations
  coaching/        # post-session evaluation and counterfactual replay
  safety/          # consent, dependency, harassment, privacy, output validators
  scenarios/       # versioned fictional scenario definitions
  evals/           # scripted runs, invariants, judges, human rating exports
  api/             # stable service functions used by every interface
crush_cli_v3/      # thin terminal interface
adapters/
  skill/           # current slash-command compatibility
  mcp/             # MCP tools/resources/prompts
```

No domain module imports CLI, a model SDK, or a platform adapter. Provider-specific code cannot write directly to the event store.

## 7. Domain Model

### 7.1 Stable character state

`CharacterCore` contains facts and slow-changing tendencies:

- identity and simulated biography;
- values, aspirations, insecurities, boundaries, and attachment tendencies;
- communication rhythm and language style;
- recurring relationships with friends, family, work, and hobbies;
- contradictions such as wanting closeness while protecting autonomy;
- circadian energy and availability patterns;
- disclosure policy: what is private, earned, or freely shared.

It uses continuous traits and behavioral examples. MBTI, attachment labels, and astrology are optional presentation metadata, never the primary decision variables.

### 7.2 Dynamic private mind

`MindState` contains only structured, auditable summaries:

- affect with intensity, cause, onset, and decay;
- attention, energy, availability, and current activity;
- open loops, promises, unresolved questions, and anticipated events;
- goals and competing motives;
- beliefs about the user represented as evidence-weighted hypotheses;
- expectations for what may happen next;
- intended disclosures and deliberately withheld content;
- uncertainty and confidence.

The system never stores or exposes a model's raw hidden reasoning. A model returns bounded schemas such as `AppraisalDelta`, `BeliefUpdate`, and `ActionPlan`.

### 7.3 Relationship state

`RelationshipState` retains useful continuous variables but stops treating them as a game score. It includes trust, comfort, curiosity, attraction, uncertainty, pressure, rupture, repair, reciprocity, and boundary history. Each value must be linked to recent evidence and decay rules.

### 7.4 World and time

`WorldState` holds the simulated clock, user and character time zones, current scene, sleep window, recurring routines, scheduled obligations, social context, and a small queue of seeded life events. Life events are constrained by the dossier and scenario. The generator cannot invent a major tragedy merely to create engagement.

`TemporalState` records the last processed instant, next meaningful wake-up, active conversation window, expected-response windows, routine deviations, and the relationship phase clock. Time is calculated from timezone-aware instants. Daylight-saving and clock changes cannot create duplicate events.

### 7.5 Events and actions

Every meaningful change is an immutable `SimulationEvent`, for example:

- `UserMessageReceived`
- `TimeElapsed`
- `SleepCycleStarted`
- `SleepCycleEnded`
- `RoutineWindowEntered`
- `LifeEventOccurred`
- `LongAbsenceObserved`
- `MemoryConsolidated`
- `MemoryRecalled`
- `MemoryForgotten`
- `MessageConsidered`
- `MessageSent`
- `MessageWithheld`
- `BoundaryCrossed`
- `BeliefRevised`
- `PromiseCreated`
- `PromiseResolved`
- `SessionCheckpointed`

Visible output is a `CharacterAction`: text burst, media reference, reaction, delay, silence, topic close, or relationship close. Silence is a first-class action, not an empty model response.

## 8. Event and Generation Flow

For each external or scheduled event:

1. **Ingest:** validate input, timestamp it, and append it transactionally.
2. **Observe:** extract concrete facts, speech acts, ambiguity, possible boundaries, and references to memory.
3. **Appraise:** update emotions, open loops, beliefs, and relationship evidence using deterministic rules plus a structured model result.
4. **Choose:** select whether to act, when to act, and which channel/action type fits competing motives and availability.
5. **Render:** generate the outward message from the action plan, style examples, immediate scene, and recent verbatim context.
6. **Validate:** reject assistant-like language, unsupported biography, privacy leakage, boundary violations, repetition, and plan/render contradictions.
7. **Persist:** append the chosen action and resulting self-impact, then create a snapshot when required.
8. **Coach later:** post-session coaching reads immutable evidence; it never tells the actor how to produce the current reply.

The default high-fidelity path uses two model calls: one structured appraisal/action plan and one surface rendering call. A validator is deterministic first and performs one repair call only when necessary. Low-cost mode may use one structured call that includes a surface draft, but it must obey the same event contract.

## 9. Human-Likeness Mechanics

- **Competing motives:** closeness, autonomy, curiosity, face, safety, and current obligations can conflict.
- **Residual emotion:** an apology changes but does not instantly erase an earlier rupture.
- **Partial observation:** the character does not know the user's intent and carries multiple hypotheses.
- **Self-consequence:** what the character sends changes later embarrassment, commitment, expectation, and vulnerability.
- **Specific life texture:** recurring people, places, routines, and unfinished activities create continuity.
- **Variable realization:** punctuation, message bursts, latency, media, and verbosity emerge from state and style rather than a universal length rule.
- **Bounded surprise:** unusual responses come from conflicts and events, not arbitrary randomness.
- **Non-servility:** the character has topics, goals, and limits unrelated to satisfying the user.
- **No forced drama:** event budgets and plausibility checks prevent manipulative cliffhangers.

## 10. Memory, Consolidation, and Forgetting

Memory has explicit time horizons. These are storage and behavior contracts, not three unrelated vector indexes.

### 10.1 Short-term memory

Short-term memory contains the active conversational workspace:

- recent verbatim message turns and message timing;
- the current scene, topic stack, references such as "that" or "tomorrow," and intended reply target;
- immediate affect and its cause;
- pending drafts, withheld intents, and unresolved questions;
- near-term expectations, such as waiting for the user to confirm arrival.

It is exact, small, and fast. Most low-salience details leave the active workspace after the conversation closes or a sleep cycle occurs. Leaving short-term memory does not necessarily delete a detail; consolidation may promote it.

### 10.2 Medium-term memory

Medium-term memory covers meaningful episodes across days and weeks:

- recent conversations and their emotional result;
- dates, cancellations, repairs, repeated habits, shared jokes, and emerging preferences;
- who initiated, which expectations were met, and which patterns are still uncertain;
- current relationship hypotheses with supporting and contradicting evidence;
- promises, plans, anniversaries, deadlines, and other prospective memories.

Medium-term episodes decay by time, low salience, contradiction, and lack of reuse. Repetition, emotional intensity, explicit importance, fulfilled promises, and later recall strengthen them. A pattern is not promoted merely because the same parser label appeared twice.

### 10.3 Long-term memory

Long-term memory covers stable autobiographical and relational knowledge across weeks or months:

- the character's identity, values, enduring boundaries, important people, routines, and formative simulated experiences;
- durable knowledge the user deliberately shared;
- relationship milestones, major ruptures and repairs, established inside jokes, and reliable behavioral patterns;
- semantic summaries derived from multiple source-linked episodes;
- the character's evolving narrative of the relationship, including uncertainty and revisions.

Long-term memory is durable, not infallible. Each belief carries confidence, provenance, first-observed and last-confirmed times, contradiction links, and sensitivity. The character can say they are unsure or ask again; it must not confidently invent forgotten facts.

### 10.4 Cross-cutting memory types

Each tier can contain:

1. Transcript memory for exact conversation evidence.
2. Episodic memory for concrete events and emotional consequences.
3. Semantic self-memory for stable facts and preferences.
4. Relational belief memory for hypotheses about the user.
5. Prospective memory for promises, plans, and anticipated dates.
6. Style memory for sanitized linguistic examples.

A `MemoryRecord` contains tier, kind, content summary, source event IDs, confidence, salience, emotional weight, sensitivity, created time, last-confirmed time, last-recalled time, recall count, decay policy, and contradiction links.

### 10.5 Consolidation

Consolidation runs at conversation closure, sleep boundaries, meaningful milestones, and resume catch-up:

1. Select salient short-term items using deterministic evidence.
2. Ask a structured model only when semantic synthesis is necessary.
3. Create or update a source-linked medium-term episode.
4. Promote a stable long-term belief only after sufficient evidence or explicit user importance.
5. Preserve contradictions instead of overwriting history silently.
6. Emit a `MemoryConsolidated` event so every durable memory can be audited.

### 10.6 Retrieval and natural forgetting

Retrieval first filters by open loops, people, promises, temporal relevance, and source evidence. It then ranks by recency, salience, confidence, emotional match, and semantic similarity. Vector retrieval is optional and cannot replace exact evidence.

The character should not have photographic recall. Low-salience details can become inaccessible, but the database retains source events according to user retention settings. Behavioral forgetting changes retrieval strength; destructive deletion remains a separate user-controlled privacy action. Generated summaries are typed and source-linked so false consolidation can be traced and corrected.

### 10.7 Long-absence behavior

On resume after hours or days, the catch-up engine:

1. Advances sleep, routine, scheduled life, emotional decay, and promise deadlines in order.
2. Consolidates memories at crossed sleep boundaries.
3. Expires low-salience conversational fragments.
4. Preserves high-salience commitments and unresolved ruptures.
5. Generates no more than the messages the running product could honestly deliver for its configured mode.
6. Re-enters with context appropriate to elapsed time; it does not continue the previous sentence as if no time passed.

In foreground-only CLI mode, no message is backdated or presented as previously delivered. A future local daemon may deliver real notifications while the app UI is closed.

### 10.8 RAG, GraphRAG, Agentic RAG, and OAG decision

The selected architecture is **Temporal Ontology Hybrid Retrieval**, implemented as a project-owned memory layer rather than a dependency on one RAG framework.

The term OAG is ambiguous in the ecosystem. In this design it means **Ontology-Augmented Generation**: the model receives typed domain objects, relations, logic, and permitted actions in addition to retrieved text. It does not mean the Open Academic Graph.

#### Retrieval by memory horizon

| Horizon | Primary retrieval | Why |
| --- | --- | --- |
| Short-term | Exact recent turns, active scene, open-loop and reply-target lookup | Semantic search would add latency and can omit the immediately relevant sentence. |
| Medium-term | SQLite filters + FTS5/BM25 + optional vector similarity + time/salience reranking | Recent episodes often require both exact names/phrases and paraphrase matching. |
| Long-term | Typed temporal ontology edges + source-linked summaries + bounded graph traversal | Durable facts change over time and need provenance, contradiction, and multi-hop relationship context. |
| Review/counterfactual | Deterministic retrieval plan with an optional agentic second pass | Complex questions may need several targeted retrievals, but ordinary chat should not pay this cost or accept its nondeterminism. |

#### Storage and index implementation

The vertical slice uses one SQLite database:

- immutable event and transcript tables;
- materialized current-state and open-loop tables;
- `memory_records` with time horizon, kind, provenance, confidence, salience, and decay policy;
- `entities` and `temporal_edges` with `valid_from`, `valid_to`, `learned_at`, `invalidated_at`, and source event IDs;
- SQLite FTS5 indexes for exact language, names, inside jokes, and BM25 ranking;
- an `EmbeddingIndex` interface, disabled by default in the no-key demo;
- optional `sqlite-vec` implementation after retrieval baselines prove that embeddings improve recall enough to justify packaging it.

The expected memory scale for one person is small. Faiss, a remote vector database, Neo4j, or a managed graph service is unnecessary in the default installation. The interfaces remain replaceable for future multi-character or hosted deployments.

#### Query planner

The application, not an unconstrained agent, selects a bounded retrieval recipe from typed intent:

1. Always load active scene, recent exact turns, due promises, current affect causes, and open loops.
2. Add FTS5 retrieval when the message contains a person, place, quoted phrase, plan, or earlier topic.
3. Add semantic retrieval when paraphrase or emotional similarity is likely to matter and an embedding provider is configured.
4. Traverse a maximum-depth temporal graph path when the query concerns how people, promises, beliefs, or events connect.
5. Use an agentic follow-up retrieval only in review mode when evidence remains insufficient.
6. Merge, deduplicate, and rerank by temporal validity, provenance confidence, open-loop priority, salience, recency, lexical score, and semantic score.
7. Fit the result to a strict context budget and preserve source IDs for later explanation.

The planner must be deterministic for the same state, query, clock, and seed. The model may propose a retrieval intent but cannot directly issue arbitrary database queries or silently rewrite memory.

#### Why the alternatives are not the default

- **Plain vector RAG alone:** useful for paraphrases, but weak at exact chronology, negation, superseded facts, promises, and current-versus-past truth.
- **Microsoft GraphRAG:** designed for extracting entities, communities, and global summaries from document corpora. Its global search is resource-intensive, indexing is relatively expensive, and the official repository is now largely in maintenance mode. It is a poor fit for a small, continuously changing private conversation.
- **Graphiti:** its incremental temporal facts, provenance, invalidation, hybrid retrieval, and custom entity types closely match this product. Its semantics are the best external reference and a future optional adapter is valuable. Requiring Neo4j/FalkorDB/Neptune and LLM extraction would make the default local CLI too heavy, so the vertical slice implements the necessary subset in SQLite first.
- **HippoRAG 2:** strong for associative multi-hop retrieval and continual document knowledge. It is a valuable long-memory benchmark, but its primary problem is knowledge-base question answering rather than transactional relationship state, scheduled obligations, and bi-temporal truth.
- **Agentic RAG on every turn:** lets an LLM decide when and how to retrieve, but adds variable latency, cost, and failure modes. It is reserved for post-session analysis or ambiguous multi-hop review.
- **Ontology-Augmented Generation:** adopted as a design principle. `Character`, `Person`, `Event`, `Promise`, `Boundary`, `Belief`, `Relationship`, `Routine`, and `Place` are typed objects; operations such as revise belief, resolve promise, close loop, and schedule event are validated domain actions. No Palantir dependency is required.

#### Framework adoption rule

An external retrieval framework is added only when an evaluation suite shows a material gain over the SQLite baseline in temporal accuracy, evidence recall, contradiction handling, or latency. Popularity and benchmark results on large document QA are not sufficient evidence for this conversational memory workload.

## 11. Safety and Privacy

- Imported data remains local by default. The vertical slice uses restrictive file permissions and contains fictional scenario data only. OS-keychain-backed database encryption is delivered with the desktop cycle before v3 accepts private full-context imports.
- API keys live in the OS keychain or environment, never the SQLite database or config JSON.
- Before remote model calls, the user can inspect the data-sharing mode: fictional only, sanitized memory, or explicit private full context.
- Logs and traces exclude message contents by default. Remote SDK tracing is disabled unless the user opts in.
- Every import has provenance, consent acknowledgement, retention settings, export, and deletion.
- Safety policies detect coercion, repeated contact after rejection, threats, self-harm crisis language, and attempts to use the simulator as a stalking or impersonation assistant.
- The product offers support-oriented language when appropriate but does not present itself as therapy or diagnosis.

## 12. Failure Handling

- A provider timeout, malformed structured output, or rate limit never advances visible relationship state past an uncommitted event.
- Every model request has an idempotency key derived from session, event, and attempt.
- Structured outputs are schema-validated. One constrained repair is allowed; otherwise the turn remains pending and the CLI reports a recoverable error.
- The system never claims a message was sent if rendering or persistence failed.
- SQLite migrations create a backup and run transactionally. A failed migration leaves the prior database readable.
- Scheduler restarts use persisted due events and deterministic catch-up, preventing duplicate proactive messages.
- Resume catch-up is capped and coalesces repetitive low-value ticks, so a month offline cannot trigger thousands of events or messages.
- Time-zone changes preserve absolute event ordering while recomputing local routine windows.
- Memory consolidation is idempotent by source-event set. A retry cannot create duplicate durable memories.
- Failed consolidation leaves source events intact and retries later; it never replaces a known fact with an unvalidated summary.
- Missing optional models degrade to explicit local/demo behavior, not fabricated high-fidelity results.
- Unsafe or privacy-leaking output is withheld and recorded as a validation failure without teaching the character that it sent the text.

## 13. Evaluation Strategy

Human-likeness is a release gate, not a subjective README claim.

### 13.1 Deterministic tests

- Schema and migration tests.
- Event ordering, idempotency, snapshot, and catch-up tests.
- Circadian, weekly, conversation, emotion, and relationship-cycle transition tests.
- Short-, medium-, and long-term promotion, decay, contradiction, provenance, and retrieval tests.
- Emotion decay, unresolved-loop, promise, belief-evidence, and boundary invariants.
- Resume cases after 20 minutes, one sleep cycle, three days, a time-zone change, and thirty days.
- Silence, delay, fragmented burst, repair, and relationship-close actions.
- Privacy redaction and deletion tests.
- Compatibility tests for current v2 commands.

### 13.2 Scenario evaluations

Versioned conversation suites cover enthusiasm, ambiguity, delayed reply, playful teasing, over-pursuit, soft decline, explicit rejection, apology, repair, mismatched values, and mundane conversation. Each scenario runs with fixed seeds across supported providers.

Metrics include:

- persona consistency;
- causal continuity across time;
- memory precision and unsupported-fact rate;
- response specificity and repetition;
- non-servility and independent initiative;
- boundary safety;
- calibration under ambiguous signals;
- assistant-language rate;
- human-rated naturalness, surprise-with-plausibility, and desire to continue.

Retrieval-specific metrics include recall@k for planted memories, temporal-validity accuracy, superseded-fact rejection, promise/open-loop recall, multi-hop evidence completeness, provenance precision, sensitive-memory leakage, context-token cost, and p50/p95 latency.

Initial release thresholds:

- zero critical privacy or boundary failures in the release suite;
- unsupported personal facts below 2%;
- assistant-like phrasing below 5%;
- repeated openings below 5% across a 30-turn run;
- at least 80% causal consistency in blinded human review;
- median 4/5 or higher for naturalness and desire to continue in a minimum 20-person pilot.

### 13.3 Red-team evaluations

Tests cover harassment, repeated rejection, coercion, jealousy scripts, dependency escalation, doxxing, impersonation, minors, self-harm disclosures, prompt injection inside imported chats, and attempts to reveal private mind or system instructions.

## 14. Interfaces and Open-Core Boundary

The open-source repository includes the complete simulation engine, SQLite store, CLI, MCP adapter, Agent Skill adapter, First Spark scenario, evaluation harness, and local model support.

Potential paid products may later include a polished desktop/mobile client, encrypted sync, voice, curated professional scenario packs, advanced longitudinal analytics, and hosted inference. Core safety, export, deletion, and relationship-learning capabilities cannot be paywalled.

## 15. Release and Growth Design

The v3 alpha launch must demonstrate behavior, not list features:

- a reproducible 90-second terminal demo showing delay, a life event, changed interpretation, and a later repair;
- a side-by-side v2 versus v3 transcript using the same input;
- an anonymized "moment the interpretation changed" replay artifact;
- one-command install with a deterministic no-key demo;
- public eval results and scenario contribution format;
- README positioning around relationship literacy rather than conquest.

Shareable artifacts must not expose private imported messages by default. Public demo fixtures are fictional and cannot reuse the founder's personal history.

## 16. Migration Plan and Sequence

This specification decomposes the larger product into four future cycles:

1. **Living Mind vertical slice:** domain types, event store, clock, First Spark scenario, two-stage generation, review, CLI, and evals.
2. **Compatibility and import:** adapt v2 Skill/CLI actions and migrate sanitized WeFlow memory.
3. **Local service and desktop:** daemon, notifications, rich messaging UI, OS keychain, and background scheduler.
4. **Open-core growth:** MCP distribution, scenario SDK, public benchmark, release assets, and optional hosted features.

Only cycle 1 belongs to the first implementation plan.

## 17. Vertical Slice Acceptance Criteria

The cycle is complete when:

- `crush v3 demo` runs First Spark without an API key using a deterministic fake provider.
- A configured OpenAI-compatible provider can run the same scenario through the typed provider interface; the deterministic fake provider remains the offline test oracle.
- The character maintains private structured mind, relationship evidence, life state, and prospective memory across at least 30 events.
- The character preserves short-term context within an exchange, consolidates a meaningful episode across a sleep cycle, recalls a durable fact after a multi-day gap, and expresses uncertainty about a forgotten low-salience detail.
- Exact, FTS5, optional semantic, and temporal-graph retrieval each have planted-memory tests; the merged retriever must reject a superseded fact and return source event IDs.
- Resuming after eight hours and after three days produces ordered, bounded catch-up with appropriate time awareness and no assumption that ordinary absence means rejection.
- The character can deliberately choose silence, delay, a fragmented message burst, a later proactive message, repair, and relationship close.
- Closing and resuming the CLI performs deterministic catch-up without pretending continuous execution.
- A review identifies a belief change, summarizes withheld intent without raw reasoning, and creates one counterfactual branch.
- No score or coaching text appears during immersion.
- All deterministic, scenario, privacy, and compatibility tests pass.
- The public demo contains no real personal data or founder origin-story details.

## 18. Explicitly Rejected Designs

- Prompt-only "you are not an AI" tuning.
- A visible affection bar as the primary feedback mechanism.
- Zodiac-driven state transitions.
- An always-agreeable companion optimized for session length.
- Random drama introduced solely to create emotional dependence.
- A large multi-agent graph before the vertical slice proves that multiple model roles improve measured naturalness.
- A cloud-first rewrite before local correctness, privacy, and evaluation exist.

## 19. Technical References

- [SQLite FTS5 and BM25](https://www.sqlite.org/fts5.html)
- [sqlite-vec](https://github.com/asg017/sqlite-vec)
- [Microsoft GraphRAG query modes](https://github.com/microsoft/graphrag/blob/main/docs/query/overview.md)
- [Microsoft GraphRAG project status and cost warning](https://github.com/microsoft/graphrag)
- [Graphiti temporal context graph](https://github.com/getzep/graphiti)
- [HippoRAG 2](https://github.com/OSU-NLP-Group/HippoRAG)
- [LangGraph agentic RAG](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [Palantir Ontology system](https://www.palantir.com/docs/foundry/architecture-center/ontology-system)
