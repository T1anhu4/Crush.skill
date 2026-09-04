# Crush.skill Homepage Transition Design

**Date:** 2026-09-04
**Status:** Approved direction; copy implementation pending
**Scope:** `README.md` and `README_EN.md`

## 1. Objective

Reposition the repository homepage around the approved v3 Living Mind direction without presenting planned work as shipped. The homepage must help a new visitor understand the product's difference quickly, run the stable version confidently, inspect the v3 work, and decide whether to Star or contribute.

The public copy must never reveal the founder's private origin story or reuse private chat content.

## 2. Audience and First-Screen Promise

The primary audience is developers and AI-agent users who are dissatisfied with generic role-play chatbots. The first screen should communicate one product idea:

> Crush.skill is an open-source relationship flight simulator evolving from scripted replies into a character with memory, time, private state, and consequences.

The promise is relationship literacy and communication practice, not conquest, manipulation, therapy, diagnosis, or impersonation.

## 3. Truthful Product Status

The homepage must distinguish two tracks visibly:

| Track | Status | Allowed claims |
|---|---|---|
| v2.4.15 | Stable and usable today | Existing Skill, CLI, WeFlow import, local SQLite memory, timeline actions, review, and current commands |
| v3 Living Mind | Design complete; implementation in progress | Approved architecture, target experience, implementation plan, development branch, and contribution opportunities |

No v3 behavior may appear in the stable feature table or quick-start instructions until its corresponding tests pass. Future capabilities use language such as “正在构建 / in development” and link to the committed design and implementation plan.

## 4. Recommended Information Architecture

Both language versions use the same section order and equivalent claims:

1. Language switch, hero, corrected badges, and compact navigation.
2. One-sentence positioning and a clear Star/contribution invitation.
3. “Available now / Building next” status panel.
4. “Why ordinary AI chat feels fake” problem statement.
5. “Living Mind direction” describing event-driven cognition, time, memory, consequences, and evidence-backed review.
6. Stable v2.4.15 one-minute start.
7. Current v2 capabilities and WeFlow import details.
8. v3 architecture preview and links to the approved specification and implementation plan.
9. Development progress checklist that marks only committed design work complete.
10. Ways to contribute: scenarios, red-team cases, retrieval benchmarks, providers, CLI/desktop work, and human evaluation.
11. Current technical architecture and developer integration reference.
12. Version summary, Star History, ethics, license, and a concise closing statement.

The existing long command tables remain available but move below the product narrative so they do not dominate the first visit.

## 5. Message Design

### 5.1 What makes the project distinctive

The homepage explains the difference using observable product mechanics rather than adjectives:

- The simulated character may delay, stay silent, send fragmented messages, follow up later, repair, or close the relationship.
- State changes have explicit causes and persist across restarts.
- Short-, medium-, and long-term memory serve different purposes and may decay or be contradicted.
- Human-scale time advances through routines, sleep, absence, and unresolved promises.
- Retrieval combines exact context, SQLite FTS5, optional embeddings, and temporal ontology edges instead of relying on vector similarity alone.
- Coaching and evidence review stay outside the immersive conversation.

Every point in this list is labelled as a v3 target until implementation and release gates are complete.

### 5.2 Tone

The voice is direct, emotionally literate, technically credible, and restrained. Avoid exaggerated statements such as “真正拥有意识”, “100% 真人”, “拿捏任何人”, or guaranteed romantic outcomes. Prefer concrete contrast: “不是只生成下一句，而是先更新发生了什么、记住什么、现在是否愿意回应，再决定行动。”

### 5.3 Growth and Star conversion

The page earns a Star request by showing a meaningful open-source mission and visible work, not by repeatedly asking. Use one primary CTA near the status panel and one contribution CTA near the roadmap. The primary CTA should invite visitors who want believable, safe relationship simulation to Star and follow v3 progress.

## 6. Link, Version, and Naming Corrections

- Use the canonical repository URL `https://github.com/T1anhu4/Crush-skill` everywhere.
- Stable version badges and release links point to `v2.4.15` unless a newer tested release exists at edit time.
- Use `T1anhu4` as the visible project owner name; never use an email address as a display name.
- Keep installation commands pinned to the stable `2.4` branch until v3 is implemented.
- Preserve `Crush.skill` as the product name even though the repository slug is `Crush-skill`.

## 7. Visual Scope

This cycle reuses the existing hero, CLI demo, and architecture SVG assets. It does not regenerate artwork. Captions and surrounding text may clarify that the current animation demonstrates v2 behavior. A future v3 launch cycle may replace the hero only after the vertical-slice demo exists.

## 8. Privacy and Safety Boundaries

- Do not include the founder's story, real names, travel context, zodiac references, real messages, or reconstructable personal details.
- Do not imply that a simulation exposes a real person's hidden thoughts.
- Clearly describe imported data as local by default and subject to consent and retention controls.
- Do not frame delayed replies, uncertainty, or emotional dynamics as tactics for coercion.
- State that the product teaches signal recognition, emotional regulation, boundaries, repair, and acceptance of rejection.

## 9. Compatibility

The README rewrite changes documentation only. Existing v2 commands, install scripts, release artifacts, and runtime behavior remain untouched. Chinese and English pages must preserve equivalent commands, status labels, privacy promises, and links.

## 10. Acceptance Criteria

The rewrite is complete when:

1. Both READMEs show v2.4.15 as stable and v3 as in development.
2. Neither README claims that v3 code is already available.
3. A new visitor can reach stable installation instructions within two section jumps.
4. The approved v3 design and implementation plan are linked from both pages.
5. The first half of each README explains memory, time, independent action, consequences, and post-session review in plain language.
6. All repository and release links use the canonical `Crush-skill` slug and valid targets.
7. Chinese and English headings and material claims remain structurally aligned.
8. No founder-origin markers, private transcript fragments, or email-as-author wording appears.
9. Markdown has balanced HTML tags and code fences, and contains no placeholder copy.
10. Existing legacy smoke tests still pass because runtime files remain unchanged.

## 11. Non-Goals

- Implementing v3 runtime code.
- Publishing a v3 release or changing package versions.
- Replacing SVG assets.
- Adding analytics, badges that require secrets, or promotional tracking.
- Rewriting the project around astrology or manipulative dating tactics.
