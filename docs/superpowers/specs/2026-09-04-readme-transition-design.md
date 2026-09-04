# Crush.skill Homepage Transition Design

**Date:** 2026-09-04
**Status:** Approved direction; copy implementation pending
**Scope:** `README.md`, `README_EN.md`, and `assets/readme-cli-demo.svg`

## 1. Objective

Evolve the existing repository homepage around the approved v3 Living Mind direction without replacing its identity or presenting planned work as shipped. This is an additive editorial revision of the current 300-line READMEs, not a minimalist rewrite. The homepage must help a new visitor understand the product's difference quickly, run the stable version confidently, inspect the v3 work, and decide whether to Star or contribute.

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

## 4. Preservation Contract

The existing README is the source document. The rewrite must preserve its recognizable experience and substantive documentation:

- Keep the animated hero SVG at the top of both language versions.
- Keep the animated CLI demonstration and current architecture illustration.
- Keep “Crush.skill 是一台关系飞行模拟器” and its English equivalent as the defining opening line.
- Preserve the existing “为什么做这个 / Why This Exists” emotional framing. It may be tightened for clarity but must not be reduced to a product-spec paragraph.
- Preserve the one-minute start, WeFlow import, current capability table, current architecture, Agent installation, slash commands, runtime actions, persona presets, release history, Star History, ethics, and license sections.
- Preserve the closing letter's emotional arc: relationships are learnable, painful experiences can become growth, and the project is for people learning how to love. It may be lightly edited for privacy and universality, but it must not be deleted, flattened, or replaced by a short marketing slogan.
- Keep the final “Made with” signature treatment while ensuring the visible owner is `T1anhu4`, not an email address.

The final Chinese and English READMEs should remain rich, long-form project homepages. Their length should stay in the same general range as the current files; the v3 material is inserted and integrated rather than paid for by removing the project's existing voice.

## 5. Recommended Information Architecture

Both language versions use the same section order and equivalent claims:

1. Existing language switch and animated hero, corrected badges, and expanded navigation.
2. Existing “relationship flight simulator” opening and “why this exists” narrative.
3. “Available now / Building next” status panel with a clear Star/contribution invitation.
4. Existing product positioning table.
5. New “Why ordinary AI chat feels fake” bridge into the approved v3 direction.
6. New “Living Mind” section describing event-driven cognition, time, memory, consequences, and evidence-backed review.
7. Stable v2.4.15 one-minute start and WeFlow import guide.
8. Existing demo animation and current v2 capability table.
9. Existing architecture illustration and module reference, followed by a v3 architecture preview linked to the approved specification and implementation plan.
10. Development progress checklist that marks only committed design work complete.
11. Ways to contribute: scenarios, red-team cases, retrieval benchmarks, providers, CLI/desktop work, and human evaluation.
12. Existing Agent installation, command reference, runtime actions, and persona presets.
13. Version summary, Star History, ethics, license, and the existing long-form emotional closing.

The existing long command tables remain available but move below the product narrative so they do not dominate the first visit.

## 6. Message Design

### 6.1 What makes the project distinctive

The homepage explains the difference using observable product mechanics rather than adjectives:

- The simulated character may delay, stay silent, send fragmented messages, follow up later, repair, or close the relationship.
- State changes have explicit causes and persist across restarts.
- Short-, medium-, and long-term memory serve different purposes and may decay or be contradicted.
- Human-scale time advances through routines, sleep, absence, and unresolved promises.
- Retrieval combines exact context, SQLite FTS5, optional embeddings, and temporal ontology edges instead of relying on vector similarity alone.
- Coaching and evidence review stay outside the immersive conversation.

Every point in this list is labelled as a v3 target until implementation and release gates are complete.

### 6.2 Tone

The voice is direct, emotionally literate, technically credible, and restrained. Avoid exaggerated statements such as “真正拥有意识”, “100% 真人”, “拿捏任何人”, or guaranteed romantic outcomes. Prefer concrete contrast: “不是只生成下一句，而是先更新发生了什么、记住什么、现在是否愿意回应，再决定行动。”

### 6.3 Growth and Star conversion

The page earns a Star request by showing a meaningful open-source mission and visible work, not by repeatedly asking. Use one primary CTA near the status panel and one contribution CTA near the roadmap. The primary CTA should invite visitors who want believable, safe relationship simulation to Star and follow v3 progress.

## 7. Link, Version, and Naming Corrections

- Use the canonical repository URL `https://github.com/T1anhu4/Crush-skill` everywhere.
- Stable version badges and release links point to `v2.4.15` unless a newer tested release exists at edit time.
- Use `T1anhu4` as the visible project owner name; never use an email address as a display name.
- Keep installation commands pinned to the stable `2.4` branch until v3 is implemented.
- Preserve `Crush.skill` as the product name even though the repository slug is `Crush-skill`.

## 8. Visual Scope

This cycle preserves and reuses the existing hero, CLI demo, and architecture SVG assets in their current prominent positions. It does not remove, hide, regenerate, or replace the animations. Captions and surrounding text may clarify that the current CLI animation demonstrates stable v2 behavior. A future v3 launch cycle may evolve the artwork only after the vertical-slice demo exists and only through a separate approved design cycle.

### 8.1 CLI animation overlap repair

The second animation, `assets/readme-cli-demo.svg`, keeps its current terminal concept, copy, palette, 1200×620 canvas, and staged message sequence. Three implementation defects must be corrected:

1. The animated groups currently use SVG `transform` attributes for permanent layout while CSS keyframes animate the same `transform` property. Browser composition can replace the permanent translation and move several text groups into the same coordinate space.
2. Delayed animations do not establish an invisible pre-animation state, so later groups can render before their reveal begins.
3. The final group reaches y=528 inside a terminal panel only 500 units tall, placing its closing line below the panel.

The repair uses a fixed outer `<g transform="translate(x y)">` wrapper for each block and applies opacity/vertical-motion animation only to an inner group. All three reveals share one coordinated timeline instead of independent delayed loops. The hidden phase has explicit opacity zero and `animation-fill-mode: both`. Vertical positions and panel height are adjusted within the unchanged canvas so every text baseline stays inside the terminal with at least 20 units of bottom clearance.

The repaired SVG must be inspected at initial, middle, and fully revealed animation states. At each state, visible text blocks have distinct vertical bounds, no text crosses the terminal boundary, and the cursor/wait animations remain functional. The static fallback frame must remain readable when SVG animation is unavailable.

## 9. Privacy and Safety Boundaries

- Do not include the founder's story, real names, travel context, zodiac references, real messages, or reconstructable personal details.
- Do not imply that a simulation exposes a real person's hidden thoughts.
- Clearly describe imported data as local by default and subject to consent and retention controls.
- Do not frame delayed replies, uncertainty, or emotional dynamics as tactics for coercion.
- State that the product teaches signal recognition, emotional regulation, boundaries, repair, and acceptance of rejection.

## 10. Compatibility

The README and SVG rewrite changes documentation assets only. Existing v2 commands, install scripts, release artifacts, and runtime behavior remain untouched. Chinese and English pages must preserve equivalent commands, status labels, privacy promises, and links.

## 11. Acceptance Criteria

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
11. Both animated hero references, both CLI demo references, and both architecture illustration references remain present.
12. The defining opening line, full “why” section, and long-form closing letter remain recognizable in both languages.
13. Existing installation, import, capability, integration, command, persona, release, ethics, and license material remains available rather than being summarized away.
14. The CLI SVG has separate fixed-layout and animated groups, an explicit hidden pre-reveal state, one coordinated reveal timeline, and no baseline outside the terminal panel.
15. Raster or browser captures of the CLI SVG at representative animation states show no overlapping or clipped text.

## 12. Non-Goals

- Implementing v3 runtime code.
- Publishing a v3 release or changing package versions.
- Replacing the visual identity or content of the existing SVG assets.
- Converting the README into a short landing page or deleting its emotional voice.
- Adding analytics, badges that require secrets, or promotional tracking.
- Rewriting the project around astrology or manipulative dating tactics.
