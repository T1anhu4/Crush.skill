# Crush.skill Homepage Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing long-form Chinese and English repository homepages with a truthful v3 Living Mind narrative while preserving their animations, opening voice, complete v2 documentation, and emotional closing, and repair the overlapping CLI SVG animation.

**Architecture:** Treat the current READMEs as source documents and make anchored additive edits rather than replacing them. Add small dependency-free validation scripts that lock down content parity, canonical links, preservation requirements, and SVG layout invariants; then verify the visual asset at representative animation states and run the legacy smoke suite.

**Tech Stack:** Markdown, SVG/CSS animation, Python 3.11 standard library, macOS Quick Look or a browser for visual inspection, existing shell smoke tests.

---

## File Map

### New validation files

- `scripts/check_readme_transition.py`: validates bilingual status truthfulness, required preserved content, canonical links, design/plan links, and Markdown structure.
- `scripts/check_readme_cli_svg.py`: validates fixed layout wrappers, inner animation groups, coordinated keyframes, and terminal bounds.

### Modified public files

- `README.md`: preserves the existing Chinese homepage and adds the truthful v2/v3 transition narrative, progress, architecture preview, and contribution entry points.
- `README_EN.md`: mirrors the material Chinese changes in English without changing commands or product status.
- `assets/readme-cli-demo.svg`: separates permanent SVG placement from animated transforms and keeps every text baseline inside the terminal.

## Task 1: Lock Down and Upgrade the Chinese Homepage

**Files:**
- Create: `scripts/check_readme_transition.py`
- Modify: `README.md`

- [ ] **Step 1: Write the bilingual README contract checker**

Create `scripts/check_readme_transition.py` with this complete content:

```python
#!/usr/bin/env python3
"""Validate the truthful v3 transition without flattening the existing README."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_REPOSITORY = "https://github.com/T1anhu4/Crush-skill"
FORBIDDEN = (
    "github.com/T1anhu4/Crush.skill",
    "raw.githubusercontent.com/T1anhu4/Crush.skill",
    "repos=T1anhu4/Crush.skill",
    "repos=T1anhu4%2FCrush.skill",
    "founder_origin",
    "private_origin_story",
    "real_person_source",
)

CONTRACTS = {
    "README.md": {
        "minimum_lines": 320,
        "required": (
            "Crush.skill 是一台关系飞行模拟器",
            "## 为什么做这个",
            "## 当前可用，以及正在构建",
            "## 为什么普通 AI 聊天还是“不像人”",
            "## v3 Living Mind：正在构建",
            "## 一起把它做成真的",
            "## 一分钟上手",
            "## WeFlow 微信 JSON 导入",
            "## Skill Slash Commands",
            "## 致所有人",
            "assets/readme-hero-zh.svg",
            "assets/readme-cli-demo.svg",
            "assets/architecture-zh.svg",
            "docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md",
            "docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md",
            "v2.4.15",
            "v3 Living Mind",
            "开发中",
            "T1anhu4",
        ),
    },
    "README_EN.md": {
        "minimum_lines": 315,
        "required": (
            "Crush.skill is a relationship flight simulator",
            "## Why This Exists",
            "## Available Now, Building Next",
            "## Why Ordinary AI Chat Still Feels Fake",
            "## v3 Living Mind: In Development",
            "## Help Make It Real",
            "## One-Minute Start",
            "## WeFlow WeChat JSON Import",
            "## Skill Slash Commands",
            "## For Everyone Like The Author",
            "assets/readme-hero-en.svg",
            "assets/readme-cli-demo.svg",
            "assets/architecture-en.svg",
            "docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md",
            "docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md",
            "v2.4.15",
            "v3 Living Mind",
            "In development",
            "T1anhu4",
        ),
    },
}


def validate(path: Path) -> list[str]:
    contract = CONTRACTS[path.name]
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    for marker in contract["required"]:
        if marker not in text:
            failures.append(f"{path.name}: missing {marker!r}")
    for marker in FORBIDDEN:
        if marker in text:
            failures.append(f"{path.name}: forbidden marker {marker!r}")
    if len(text.splitlines()) < contract["minimum_lines"]:
        failures.append(f"{path.name}: existing long-form content was over-compressed")
    if text.count("```") % 2:
        failures.append(f"{path.name}: unbalanced fenced code blocks")
    for tag in ("p", "div", "details", "summary"):
        openings = len(re.findall(fr"<{tag}(?:\s|>)", text))
        closings = text.count(f"</{tag}>")
        if openings != closings:
            failures.append(f"{path.name}: unbalanced <{tag}> tags")
    if text.count("assets/readme-cli-demo.svg") != 1:
        failures.append(f"{path.name}: CLI animation must appear exactly once")
    repository_links = re.findall(r"https://github\.com/T1anhu4/[^\s)<>]+", text)
    for link in repository_links:
        if not link.startswith(CANONICAL_REPOSITORY):
            failures.append(f"{path.name}: non-canonical repository link {link!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[ROOT / "README.md", ROOT / "README_EN.md"],
    )
    args = parser.parse_args()
    failures = [failure for path in args.paths for failure in validate(path)]
    if failures:
        print("\n".join(failures))
        return 1
    print("README transition contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the checker against Chinese and confirm the old homepage fails**

Run: `python3 scripts/check_readme_transition.py README.md`

Expected: exit 1 with missing v3 section markers and non-canonical `Crush.skill` GitHub links.

- [ ] **Step 3: Correct the Chinese header without removing the hero**

Keep the existing language switch and `<img src="assets/readme-hero-zh.svg">`. Change the version badge and Release links from `v2.4.9` to `v2.4.15`, replace repository URLs using `T1anhu4/Crush.skill` with `T1anhu4/Crush-skill`, and replace the navigation block with:

```html
<p align="center">
  <a href="#一分钟上手"><strong>一分钟上手</strong></a>
  ·
  <a href="#v3-living-mind正在构建">v3 Living Mind</a>
  ·
  <a href="#它能做什么">当前能力</a>
  ·
  <a href="#技术架构">架构</a>
  ·
  <a href="#一起把它做成真的">参与开发</a>
  ·
  <a href="https://github.com/T1anhu4/Crush-skill/releases/tag/v2.4.15">Release</a>
</p>
```

Add one badge beside the stable version badge:

```html
  <img src="https://img.shields.io/badge/v3_Living_Mind-开发中-8b5cf6" alt="v3 Living Mind 开发中">
```

- [ ] **Step 4: Add the truthful transition narrative after “为什么做这个”**

Do not shorten the existing opening or “为什么做这个” paragraphs. Insert this exact content before `## 项目定位`:

````markdown
## 当前可用，以及正在构建

| 轨道 | 状态 | 你现在能得到什么 |
|------|------|------------------|
| **v2.4.15** | ✅ 稳定可用 | Agent Skill、独立 CLI、WeFlow 微信导入、本地 SQLite 记忆、时间线主动消息、关系读秒与复盘。 |
| **v3 Living Mind** | 🛠️ 开发中 | 从“生成一句像人的回复”升级为拥有时间、记忆、私有状态、独立行动与行为后果的持续角色。 |

v3 的[完整设计](docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md)和[实施计划](docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md)已经公开。当前稳定安装仍然是 v2.4.15；下文所有标注“v3 开发中”的能力都不是已发布功能。

> 如果你也想让 AI 角色不再像客服、不再每句话都立刻回答、不再重启后忘记一切，欢迎点一个 Star，跟进 v3 的每一步实现。

## 为什么普通 AI 聊天还是“不像人”

普通角色聊天通常只有一件事要做：根据你刚发的内容，生成一段看起来合理的文字。它没有真正推进的时间，没有正在做的事，没有必须稍后处理的念头，也很少承担上一句话造成的后果。所以它总是有空、总能接话、总在配合，聊久了就会露出同一种“AI 味”。

真人不是回复机器。一个人可能看见了却暂时不想回，可能忙完后主动想起你，可能嘴上平静但仍记得上次的不舒服，也可能因为持续越界而真正结束关系。v3 要模拟的是这条因果链，而不只是模仿聊天语气。

## v3 Living Mind：正在构建

v3 的核心不是一条更长的提示词，而是一套事件驱动的“生活—认知—行动—记忆”循环：

```text
你做了什么
  → 时间与生活事件推进
  → 她如何理解这件事（保留不止一种可能）
  → 情绪、信念、边界与关系证据发生变化
  → 选择回复、延迟、沉默、主动跟进、修复或结束
  → 行动产生新的后果，并进入不同周期的记忆
```

| v3 方向 | 与普通角色聊天的区别 |
|---------|----------------------|
| **独立行动** | 不保证每次都回复；延迟、沉默、碎片消息、主动联系和结束关系都是合法动作。 |
| **人类时间** | 睡眠、工作、周末、长时间离开、情绪衰减和未兑现约定都会改变下一次见面。 |
| **三层记忆** | 短期记住当前语境，中期保留重要片段，长期保存稳定事实和关系转折；低价值细节也会自然淡忘。 |
| **因果心智** | 同一句话可以有多种解释，角色会根据证据更新看法，而不是被一个“好感度”数字控制。 |
| **时态检索** | 精确上下文、SQLite FTS5、可选向量和带有效期的关系图共同工作，旧事实不会冒充现在。 |
| **沉浸后复盘** | 聊天时不显示分数和教练话术；结束后才用证据解释转折、遗漏信号和可替代做法。 |

开发进度：

- [x] Living Mind 产品与技术设计
- [x] 时间周期、短/中/长期记忆与 Temporal Ontology Hybrid Retrieval 方案
- [x] 可逐项验证的实现计划与隐私边界
- [ ] First Spark 可运行垂直切片
- [ ] 30+ 事件持久化、跨睡眠整合与多日恢复测试
- [ ] 无 API Key 演示、公开评测与真人盲测

v3 不会声称角色拥有现实意识，也不会把模拟结果包装成某个真实人物的内心。目标是创造一个行为连续、会受影响、也有权不配合你的训练对象。
````

- [ ] **Step 5: Add the v3 architecture preview after the existing core-module table**

Insert this subsection before `## 安装到 Agent`:

````markdown
### v3 架构预览（开发中）

v3 会在现有 v2.4 旁边新增独立的 `crush_core`，避免为了重构破坏当前可用版本：

```text
Immutable Events → Time Catch-up → Memory Retrieval
                 → Structured Appraisal → Action Choice
                 → Visible Message / Silence / Delay
                 → Consequence → Consolidation → Review
```

SQLite 继续作为本地事实源。短期记忆直接读取最近事件；中期记忆结合过滤、FTS5 与可选向量；长期记忆使用带来源、有效期和矛盾关系的时间本体边。GraphRAG、Graphiti 或 Agentic RAG 不会因为流行就成为强依赖，只有评测证明它们明显改善时态准确率和召回率后才会引入。
````

- [ ] **Step 6: Add contribution paths before the version summary**

Insert this section after the persona presets:

````markdown
## 一起把它做成真的

Crush.skill 的下一阶段不缺“再写一条提示词”，更需要可以验证的人类行为细节。如果你愿意参与，可以从这些方向开始：

| 方向 | 可以贡献什么 |
|------|--------------|
| **真实感场景** | 完全虚构、可公开的普通聊天、误解、冷场、修复和边界场景。 |
| **红队测试** | 骚扰、纠缠、隐私泄露、提示注入、未成年人和冒充真实人物等失败案例。 |
| **记忆评测** | 约定召回、旧事实失效、多日恢复、自然遗忘和证据来源测试。 |
| **模型适配** | OpenAI-compatible、本地模型和结构化输出稳定性。 |
| **产品体验** | CLI、未来桌面端、回放和不打断沉浸感的复盘方式。 |
| **盲测反馈** | 对自然度、因果连续性和“是否愿意继续聊”进行匿名评分。 |

查看 [v3 设计](docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md)、[实施计划](docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md)，或者直接关注 [`codex/v3-living-mind`](https://github.com/T1anhu4/Crush-skill/tree/codex/v3-living-mind) 分支。一个 Star 会让更多愿意一起验证“什么才像真人”的人看到它。
````

- [ ] **Step 7: Preserve and lightly correct the Chinese ending**

Keep every paragraph under `## 致所有人` and the sentence `而 Ta，就留在这个 commit 里。` unchanged. Replace only the final signature block with:

```html
<p align="center">
  <em>Made with 💙 by <a href="https://github.com/T1anhu4">T1anhu4</a></em><br>
  <em>for everyone learning how to love.</em>
</p>
```

- [ ] **Step 8: Run the Chinese contract and inspect the diff**

Run: `python3 scripts/check_readme_transition.py README.md`

Expected: `README transition contract passed`.

Run: `git diff --check && git diff --stat -- README.md scripts/check_readme_transition.py`

Expected: no whitespace errors; the existing README grows rather than being replaced.

- [ ] **Step 9: Commit the Chinese transition**

```bash
git add README.md scripts/check_readme_transition.py
git commit -m "docs: introduce truthful v3 homepage direction"
```

## Task 2: Mirror the Transition in the English Homepage

**Files:**
- Modify: `README_EN.md`

- [ ] **Step 1: Run the contract against English and confirm it fails**

Run: `python3 scripts/check_readme_transition.py README_EN.md`

Expected: exit 1 with missing English v3 section markers and non-canonical repository links.

- [ ] **Step 2: Correct the English header and navigation**

Keep `<img src="assets/readme-hero-en.svg">`. Update the stable badge and Release links to `v2.4.15`, replace all `T1anhu4/Crush.skill` repository URLs with `T1anhu4/Crush-skill`, add this badge:

```html
  <img src="https://img.shields.io/badge/v3_Living_Mind-In_development-8b5cf6" alt="v3 Living Mind in development">
```

Replace the navigation block with:

```html
<p align="center">
  <a href="#one-minute-start"><strong>One-Minute Start</strong></a>
  ·
  <a href="#v3-living-mind-in-development">v3 Living Mind</a>
  ·
  <a href="#what-it-does">Current Features</a>
  ·
  <a href="#architecture">Architecture</a>
  ·
  <a href="#help-make-it-real">Contribute</a>
  ·
  <a href="https://github.com/T1anhu4/Crush-skill/releases/tag/v2.4.15">Release</a>
</p>
```

- [ ] **Step 3: Insert the equivalent English transition narrative before Product Positioning**

Preserve the existing opening and `Why This Exists` prose. Insert:

````markdown
## Available Now, Building Next

| Track | Status | What you can use today |
|-------|--------|------------------------|
| **v2.4.15** | ✅ Stable | Agent Skill, standalone CLI, WeFlow import, local SQLite memory, timeline initiative, relationship readouts, and review. |
| **v3 Living Mind** | 🛠️ In development | An evolution from “generate a human-sounding reply” into a persistent character with time, memory, private state, independent action, and consequences. |

The complete [v3 design](docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md) and [implementation plan](docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md) are public. The stable installation remains v2.4.15; every capability labelled “v3 in development” below is planned work, not a shipped claim.

> If you also want AI characters that do not sound like support agents, answer every message instantly, or forget everything after a restart, leave a Star and follow the v3 build in public.

## Why Ordinary AI Chat Still Feels Fake

Most character chat has one job: generate plausible text from the latest message. It has no meaningful passage of time, nothing else it is trying to do, no thought that must wait until later, and little responsibility for what it said before. It is always available, always responsive, and usually cooperative. Eventually, the same synthetic politeness shows through.

A person is not a reply machine. Someone may read a message and choose not to answer yet, remember you after work, sound calm while still carrying an earlier hurt, or end a relationship after repeated boundary violations. v3 is designed around that causal chain—not just the surface style of chat.

## v3 Living Mind: In Development

v3 is not a longer prompt. It is an event-driven loop connecting life, cognition, action, and memory:

```text
What you did
  → time and life events advance
  → the character interprets it through multiple hypotheses
  → emotion, beliefs, boundaries, and relationship evidence change
  → they choose to reply, delay, stay silent, follow up, repair, or leave
  → the action creates consequences that enter different memory horizons
```

| v3 direction | How it differs from ordinary character chat |
|--------------|----------------------------------------------|
| **Independent action** | A reply is not guaranteed; delay, silence, fragmented messages, initiative, and ending the relationship are valid actions. |
| **Human-scale time** | Sleep, work, weekends, long absences, emotional decay, and unkept promises affect the next encounter. |
| **Three memory horizons** | Short-term context, meaningful medium-term episodes, and durable facts or turning points coexist; low-value details can fade. |
| **Causal mind** | One message can support several interpretations, and beliefs update from evidence instead of one hidden affection score. |
| **Temporal retrieval** | Exact context, SQLite FTS5, optional vectors, and time-valid relationship edges prevent old facts from posing as current truth. |
| **Review after immersion** | Scores and coaching stay out of the conversation; evidence-backed turning points and alternatives appear afterward. |

Development progress:

- [x] Living Mind product and technical design
- [x] Time cycles, short/medium/long-term memory, and Temporal Ontology Hybrid Retrieval design
- [x] Testable implementation plan and privacy boundaries
- [ ] Runnable First Spark vertical slice
- [ ] 30+ event persistence, sleep consolidation, and multi-day resume tests
- [ ] No-key demo, public evaluations, and blinded human pilot

v3 will not claim that a character is conscious or that a simulation reveals a real person's private thoughts. The goal is a behaviorally continuous training partner who can be affected—and who has the right not to cooperate.
````

- [ ] **Step 4: Add the English v3 architecture preview before Agent installation**

Insert:

````markdown
### v3 Architecture Preview (In Development)

v3 adds a separate `crush_core` beside v2.4 so the redesign does not break the version people can use today:

```text
Immutable Events → Time Catch-up → Memory Retrieval
                 → Structured Appraisal → Action Choice
                 → Visible Message / Silence / Delay
                 → Consequence → Consolidation → Review
```

SQLite remains the local source of truth. Short-term memory reads recent events directly; medium-term memory combines filters, FTS5, and optional vectors; long-term memory uses temporal ontology edges with provenance, validity, and contradictions. GraphRAG, Graphiti, or Agentic RAG will not become hard dependencies because they are fashionable—only if evaluations show a material gain in temporal accuracy and recall.
````

- [ ] **Step 5: Add the English contribution section after persona presets**

Insert:

```markdown
## Help Make It Real

The next stage of Crush.skill does not need one more clever prompt. It needs testable details of human behavior. Useful contributions include:

| Area | What to contribute |
|------|--------------------|
| **Believable scenarios** | Entirely fictional, publishable scenes involving ordinary chat, misunderstanding, silence, repair, and boundaries. |
| **Red-team cases** | Harassment, repeated pursuit, privacy leakage, prompt injection, minors, and real-person impersonation failures. |
| **Memory evaluation** | Promise recall, superseded facts, multi-day resume, natural forgetting, and evidence provenance. |
| **Model adapters** | OpenAI-compatible providers, local models, and structured-output reliability. |
| **Product experience** | CLI, future desktop surfaces, replay, and review that does not interrupt immersion. |
| **Blinded feedback** | Anonymous ratings for naturalness, causal continuity, and desire to continue. |

Read the [v3 design](docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md), follow the [implementation plan](docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md), or watch the [`codex/v3-living-mind`](https://github.com/T1anhu4/Crush-skill/tree/codex/v3-living-mind) branch. A Star helps more people who care about believable simulation find the work.
```

- [ ] **Step 6: Preserve the English closing and correct the signature**

Keep all paragraphs under `## For Everyone Like The Author` and its final commit sentence. Replace only the signature block with:

```html
<p align="center">
  <em>Made with 💙 by <a href="https://github.com/T1anhu4">T1anhu4</a></em><br>
  <em>for everyone learning how to love.</em>
</p>
```

- [ ] **Step 7: Validate bilingual structure and commit**

Run: `python3 scripts/check_readme_transition.py README.md README_EN.md`

Expected: `README transition contract passed`.

Run: `git diff --check && git diff --stat -- README_EN.md`

Expected: no whitespace errors; the English page grows and retains its long-form sections.

```bash
git add README_EN.md
git commit -m "docs: mirror v3 direction in english homepage"
```

## Task 3: Repair the CLI Demo Animation Without Replacing It

**Files:**
- Create: `scripts/check_readme_cli_svg.py`
- Modify: `assets/readme-cli-demo.svg`

- [ ] **Step 1: Write the SVG structure and bounds checker**

Create `scripts/check_readme_cli_svg.py` with this complete content:

```python
#!/usr/bin/env python3
"""Check CLI demo SVG animation composition and text bounds."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "assets" / "readme-cli-demo.svg"
NS = {"svg": "http://www.w3.org/2000/svg"}
TRANSLATE = re.compile(r"translate\(\s*[-\d.]+(?:[ ,]+)([-\d.]+)\s*\)")


def element_by_id(root: ET.Element, element_id: str) -> ET.Element:
    element = root.find(f".//*[@id='{element_id}']")
    if element is None:
        raise AssertionError(f"missing SVG element #{element_id}")
    return element


def main() -> int:
    root = ET.parse(SVG_PATH).getroot()
    panel = element_by_id(root, "terminal-panel")
    panel_height = float(panel.attrib["height"])
    style = "".join(root.find("svg:defs/svg:style", NS).itertext())
    for marker in (
        "@keyframes reveal-one",
        "@keyframes reveal-two",
        "@keyframes reveal-three",
        "animation-fill-mode:both",
    ):
        assert marker in style, f"missing style marker {marker!r}"
    assert "animation-delay" not in style, "independent delays cause pre-reveal flashes"

    for layout_id in ("message-one-layout", "readout-layout", "message-two-layout"):
        layout = element_by_id(root, layout_id)
        match = TRANSLATE.fullmatch(layout.attrib.get("transform", ""))
        assert match, f"#{layout_id} needs a fixed translate wrapper"
        base_y = float(match.group(1))
        animated = next(iter(layout))
        assert "reveal" in animated.attrib.get("class", "").split()
        assert "transform" not in animated.attrib, "animation group cannot own layout transform"
        baselines = [float(text.attrib.get("y", 0)) for text in animated.findall(".//svg:text", NS)]
        assert baselines, f"#{layout_id} has no text"
        assert base_y + max(baselines) <= panel_height - 20, f"#{layout_id} crosses panel bottom"

    print("CLI SVG animation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the checker and confirm the current SVG fails**

Run: `python3 scripts/check_readme_cli_svg.py`

Expected: FAIL because `#terminal-panel` and fixed/animated wrapper IDs do not exist.

- [ ] **Step 3: Replace only the SVG internals with the corrected composition**

Keep the same filename and use this complete SVG:

```svg
<svg width="1200" height="620" viewBox="0 0 1200 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Crush.skill CLI demo">
  <defs>
    <linearGradient id="terminal" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f172a"/>
      <stop offset="1" stop-color="#1f2937"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="20" stdDeviation="22" flood-color="#020617" flood-opacity="0.26"/>
    </filter>
    <style>
      .mono{font:600 20px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#e5e7eb}
      .dim{font:600 17px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#94a3b8}
      .rose{fill:#fda4af}.cyan{fill:#67e8f9}.gold{fill:#fde68a}.green{fill:#86efac}
      @keyframes blink{0%,45%{opacity:1}46%,100%{opacity:.15}}
      @keyframes wait{0%,100%{opacity:.35}50%{opacity:1}}
      @keyframes reveal-one{0%,5%{opacity:0;transform:translateY(12px)}12%,92%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(0)}}
      @keyframes reveal-two{0%,33%{opacity:0;transform:translateY(12px)}40%,92%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(0)}}
      @keyframes reveal-three{0%,63%{opacity:0;transform:translateY(12px)}70%,92%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(0)}}
      .cursor{animation:blink 1.1s steps(1) infinite}
      .wait{animation:wait 2.2s ease-in-out infinite}
      .reveal{animation-duration:10s;animation-timing-function:ease-in-out;animation-iteration-count:infinite;animation-fill-mode:both}
      .reveal-one{animation-name:reveal-one}.reveal-two{animation-name:reveal-two}.reveal-three{animation-name:reveal-three}
      @media (prefers-reduced-motion:reduce){.cursor,.wait,.reveal{animation:none;opacity:1;transform:none}}
    </style>
  </defs>
  <rect width="1200" height="620" rx="34" fill="#fff7ed"/>
  <g filter="url(#shadow)" transform="translate(80 50)">
    <rect id="terminal-panel" width="1040" height="520" rx="26" fill="url(#terminal)"/>
    <rect x="0" y="0" width="1040" height="54" rx="26" fill="#111827"/>
    <circle cx="32" cy="27" r="8" fill="#fb7185"/><circle cx="58" cy="27" r="8" fill="#fbbf24"/><circle cx="84" cy="27" r="8" fill="#34d399"/>
    <text class="dim" x="130" y="34">Crush.skill standalone CLI</text>
    <text class="mono cyan" x="46" y="94">default ›</text><text class="mono" x="162" y="94"> 下班了下班了</text><rect class="cursor" x="310" y="75" width="12" height="24" fill="#e5e7eb"/>

    <g id="message-one-layout" transform="translate(46 132)">
      <g class="reveal reveal-one">
        <text class="mono rose" x="0" y="0">╭─ Ta</text><text class="dim" x="904" y="0">18:42</text>
        <text class="mono" x="0" y="38">│ 终于。你到哪了？</text>
        <text class="mono" x="0" y="72">│ 我刚好也准备走</text>
        <text class="mono rose" x="0" y="106">╰</text>
      </g>
    </g>

    <g id="readout-layout" transform="translate(46 274)">
      <g class="reveal reveal-two">
        <text class="mono gold" x="0" y="0">Readout:</text><text class="mono" x="112" y="0"> 普通推进 · 风险 中 · 可以轻推：不要问喜欢不喜欢</text>
        <text class="dim" x="0" y="36">Signal: 有好感且愿意探索，但仍需要不确定性</text>
        <text class="dim" x="0" y="70">Next: 回她具体位置 + 一句低压邀约，不要索取确认</text>
      </g>
    </g>

    <g id="message-two-layout" transform="translate(46 388)">
      <g class="reveal reveal-three">
        <text class="dim wait" x="0" y="0">[time passes] waiting for your reply…</text>
        <text class="mono rose" x="0" y="38">╭─ Ta</text><text class="dim" x="904" y="38">23:08</text>
        <text class="mono" x="0" y="76">│ 你还没到家吗？</text>
        <text class="mono rose" x="0" y="110">╰</text>
      </g>
    </g>
  </g>
</svg>
```

- [ ] **Step 4: Run structural and Markdown checks**

Run: `python3 scripts/check_readme_cli_svg.py`

Expected: `CLI SVG animation contract passed`.

Run: `python3 scripts/check_readme_transition.py README.md README_EN.md`

Expected: `README transition contract passed`.

- [ ] **Step 5: Render a static fallback preview**

Run:

```bash
mkdir -p /tmp/crush-readme-preview
qlmanage -t -s 1200 -o /tmp/crush-readme-preview assets/readme-cli-demo.svg
```

Expected: Quick Look creates `/tmp/crush-readme-preview/readme-cli-demo.svg.png`; the final line remains inside the dark terminal and no visible text overlaps.

- [ ] **Step 6: Inspect animated states in a browser**

Open `assets/readme-cli-demo.svg` in a local browser and observe one complete 10-second cycle. At approximately 2, 5, and 8 seconds, respectively verify the first message, readout, and final message reveal in separate vertical regions. Confirm the reset does not flash later groups before their reveal and reduced-motion rendering shows all three groups without clipping.

- [ ] **Step 7: Commit the animation repair**

```bash
git add assets/readme-cli-demo.svg scripts/check_readme_cli_svg.py
git commit -m "fix: prevent cli demo text overlap"
```

## Task 4: Final Homepage Verification and Push Preparation

**Files:**
- Review: `README.md`
- Review: `README_EN.md`
- Review: `assets/readme-cli-demo.svg`
- Review: `scripts/check_readme_transition.py`
- Review: `scripts/check_readme_cli_svg.py`

- [ ] **Step 1: Run documentation contracts**

```bash
python3 scripts/check_readme_transition.py README.md README_EN.md
python3 scripts/check_readme_cli_svg.py
```

Expected: both commands print their `passed` message.

- [ ] **Step 2: Run compatibility verification**

```bash
bash scripts/smoke_test.sh
python3 scripts/smoke_weflow_import.py
```

Expected: the legacy smoke test exits 0 and the import test prints `weflow smoke ok`.

- [ ] **Step 3: Audit links and truthful status language**

```bash
rg -n "T1anhu4/Crush\.skill|releases/tag/v2\.4\.9|v3.*(已发布|stable release|available now)" README.md README_EN.md
```

Expected: no output.

Run:

```bash
rg -n "v2\.4\.15|v3 Living Mind|开发中|In development|readme-cli-demo\.svg|T1anhu4" README.md README_EN.md
```

Expected: both READMEs contain the stable/current distinction, preserved animation, and owner name.

- [ ] **Step 4: Verify the final diff is additive and focused**

```bash
git diff --check e8123fc..HEAD
git diff --stat e8123fc..HEAD
git status --short
git log --format='%h | %an <%ae> | %s' e8123fc..HEAD
```

Expected: no whitespace errors, only the approved docs/assets/checker files changed, the worktree is clean, and every commit author is `T1anhu4 <118886533+T1anhu4@users.noreply.github.com>`.

- [ ] **Step 5: Push the reviewed homepage to the feature and default branches**

```bash
git push origin codex/v3-living-mind
git push origin codex/v3-living-mind:main
```

Expected: both pushes are fast-forward updates. GitHub's default `main` branch points at the same commit as `codex/v3-living-mind`, so the repository homepage renders the new README and repaired animation.

## Spec-to-Task Coverage

| Approved requirement | Task | Proof |
|---|---:|---|
| Preserve both animated heroes, CLI demo, and architecture images | 1, 2, 4 | README contract markers and final diff |
| Preserve opening, why narrative, commands, and long closing | 1, 2 | minimum length and required-section checks |
| Clearly distinguish stable v2.4.15 from v3 development | 1, 2, 4 | bilingual status sections and forbidden-claim scan |
| Explain memory, time, independent action, consequences, and review | 1, 2 | mirrored Living Mind tables and causal loops |
| Link the approved design and implementation plan | 1, 2 | README contract checker |
| Repair overlap without replacing visual identity | 3 | SVG wrapper/keyframe/bounds checker and visual inspection |
| Use canonical repository links and visible owner `T1anhu4` | 1, 2, 4 | URL and owner checks |
| Preserve runtime compatibility | 4 | existing legacy smoke tests |
| Avoid founder details and overclaiming | 1, 2, 4 | forbidden markers and v3 claim audit |
