# 💔 Crush.skill — Turn Them Into a Mirror, See Yourself

<p align="center">
  <em>Not a replacement for a real person — a way to understand human hearts better.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.1.0-blue" alt="version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <img src="https://img.shields.io/badge/python-3.10+-yellow" alt="python">
  <img src="https://img.shields.io/badge/platform-Claude%20Code%20%7C%20OpenClaw%20%7C%20QwenPaw%20%7C%20WorkBuddy-orange" alt="platforms">
  <img src="https://img.shields.io/badge/memory-mem0%20%2B%20SQLite-purple" alt="memory">
</p>

---

## 🤔 Why This Exists

**Being single isn't because you're not good enough. It's because nobody taught you how relationships work.**

Schools teach math, English, physics — but not a single class on love.

Nobody tells you:
- Why they grow colder the faster you reply
- Why saying "I like you" makes them disappear
- Why a great conversation suddenly becomes "we need space"

**Crush.skill is a relationship flight simulator.**

It turns the person you're interested in into a **5-layer personality model**. In this safe sandbox, you can:
- Understand why they respond the way they do
- See which of your words triggered their defenses
- Discover when the relationship started breaking — and when you had a chance
- Practice endlessly, so you're never fumbling in real life again

> Inspired by the Person-as-Skill movement — [ex-skill](https://github.com/therealXiaomanChu/ex-skill) and [colleague-skill](https://github.com/titanwings/colleague-skill). Crush.skill focuses on **romantic relationship dynamics** — the most complex and least taught domain of human interaction.

---

## 🏗️ Architecture

```
                         ┌──────────────────────────┐
                         │   🌐 Multi-Platform      │
                         │  Claude Code / OpenClaw  │
                         │  QwenPaw / WorkBuddy     │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │     Slash Commands       │
                         │  /start-crush            │
                         │  /import-chats           │
                         │  /chat /dashboard        │
                         │  /postmortem /let-go     │
                         └────────────┬─────────────┘
                                      │
          ┌───────────────┬───────────┼───────────┬───────────────┐
          │               │           │           │               │
          ▼               ▼           ▼           ▼               ▼
    ┌──────────┐   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Persona  │   │  State   │  │ Dialogue │  │  Chat    │  │ Memory   │
    │  Engine  │   │  Engine  │  │ Analyzer │  │ Import   │  │ System   │
    │ 5-layer  │   │Nonlinear │  │ LLM/local│  │WeChat/WA │  │ SQLite   │
    │ model    │   │S-curves  │  │ fallback │  │ QQ/CSV   │  │ + mem0   │
    └──────────┘   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 5-Layer Persona Model

| Layer | Name | What It Captures |
|-------|------|-----------------|
| **Layer 1** | Hard Rules | Non-negotiable boundaries · Reply speed · Ghost probability · Tone restrictions |
| **Layer 2** | Identity | MBTI · Big Five · Age · Core values · Insecurities · Self-perception |
| **Layer 3** | Expression | **Speech fingerprint** — Signature phrases · Emoji style · Humor · Filler words |
| **Layer 4** | Emotional | Attachment style · Love language · Conflict patterns · Stress response · Mood volatility |
| **Layer 5** | Relational | Relationship stage · Shared history · Inside jokes · Power dynamic · Their view of you |

### Nonlinear State Engine

Real humans don't follow linear formulas. Our state engine implements:

- **S-curve saturation** — Going from 70→80 favorability is 3× harder than 10→20
- **Habituation decay** — The 5th identical compliment has minimal impact
- **Tipping points** — Crossing certain thresholds causes phase transitions
- **Cross-dimension coupling** — High defense halves favorability gains · High tension amplifies emotions

### Memory System

- **SQLite** — Persistent long-term storage · Events, state history, summaries
- **mem0** — Semantic memory · Auto-installed on first run · Lets NPCs remember past conversations
- **Auto-summary** — Compresses context when conversations grow · Prevents context overflow

---

## ⚡ Quick Start

### Method 1: One-Prompt Install

Paste this into Claude Code / OpenClaw / QwenPaw:

```text
Install crush-skill for me. Follow these steps:

1. Ensure ~/.claude/skills/ exists (create if not)
2. Run: git clone https://github.com/T1anhu4/Crush.skill /tmp/crush-skill
3. Run: bash /tmp/crush-skill/scripts/install_skill.sh --platform claude --source-dir /tmp/crush-skill/Crush.skill --skill-name crush-skill --force
4. Verify: ls ~/.claude/skills/crush-skill/ should show SKILL.md, manifest.json, execute.py, engines/
5. Tell me it's installed. I can now use /start-crush, /import-chats, etc.
```

Dependencies auto-install on first run. No manual setup needed.

### Method 2: ZIP Install

1. Download `crush_skill_v2.1.0.zip` from [Releases](https://github.com/T1anhu4/Crush.skill/releases)
2. Drag into Claude Code or extract to `~/.claude/skills/crush-skill/`
3. Dependencies install automatically on first use

---

## 📖 Slash Commands

Everything works through slash commands inside your AI agent:

| Command | Description |
|---------|-------------|
| `/start-crush [archetype]` | Quick start with a preset personality. 5 archetypes available. |
| `/custom-crush` | Full custom 5-layer persona. Control every dimension. |
| `/import-chats` | Import chat records. Auto-infers personality and relationship state. |
| `/chat [message]` | Send a message. See state changes, defense triggers, attraction peaks. |
| `/crush-dashboard` | View 8-dimensional state dashboard. |
| `/crush-postmortem` | Relationship combat replay: collapses, peaks, defenses, narrative. |
| `/list-crushes` | List all saved sessions. |
| `/let-go [session]` | Ritual closure. Delete with an uplifting goodbye. |
| `/crush-llm [api_key]` | Configure LLM for dialogue analysis (optional). |

### Chat Record Import

Supports automatic format detection:

| Source | Format | Notes |
|--------|--------|-------|
| WeChat | WeChatMsg / Liú Hén / PyWxDump | Recommended, richest data |
| WhatsApp | .txt export | Auto-detected |
| QQ | .txt / .mht export | Nostalgia-friendly |
| CSV | Structured | `sender,content,timestamp` |
| Paste | Direct paste | `Name: message` format |

Just type `/import-chats` and paste your records. The engine handles everything else.

### 5 Personality Archetypes

| Archetype | Traits | Best For |
|-----------|--------|----------|
| `emotional` | Values connection · Needs to be seen · Anxious attachment | Deep feelers |
| `security` | Slow to trust · Values stability · Secure attachment | Steady personalities |
| `experience` | Seeks novelty · Emotional peaks · Fearful-avoidant | Fun-loving types |
| `value` | Pragmatic · Status-conscious · Dismissive-avoidant | Career-focused people |
| `passive` | Go-with-the-flow · Low initiative · Avoidant | Hard-to-read types |

---

## 🔧 Environment (Optional)

Crush.skill works out of the box. These are optional advanced settings:

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | LLM semantic analysis | None (local fallback) |
| `CRUSH_MEMORY_BACKEND` | `sqlite` or `mem0` | Auto-best |
| `CRUSH_ANALYZER_MODEL` | Analysis model | `gpt-4o-mini` |

> **Note**: In Claude Code / OpenClaw, the platform LLM is auto-detected. No manual config needed. Use `/crush-llm` to check or override.

---

## 📄 License

MIT License. Free to use, modify, distribute.

> **Ethics**: This tool is for **understanding and learning**, not manipulation or harassment. Do not simulate a real person without consent. Do not import private conversations without permission. When you've learned what you need, use `/let-go`.

---

## 💙 To Everyone Like the Author

Our generation was taught ten thousand skills — but never how to love someone.

So we freeze in front of the chat box. We doubt ourselves after rejection. We spiral in the silence of being left on read. We think we're not good enough, not interesting enough, not successful enough.

**But love is learnable.** It just takes practice, feedback, and a safe space to make mistakes — like a flight simulator for pilots.

Crush.skill is that simulator.

When you can naturally catch their emotions, sense the anxiety behind their silence, and face rejection with calm — you'll understand that this tool never taught you "how to chase." It taught you **how to become someone worthy of love.**

And then —

**Their appearance in your life has already given you everything you needed.**

That first crush showed you a tenderness you never knew you had.
That late-night conversation taught you the power of being present.
That rejection made you face your flaws for the first time.
That push-and-pull taught you how to let go.

**You are already a better person than you were before you met them. That's enough.**

Take these things — the things that truly belong to you, that no one can take away — and walk toward a brighter life.

As for them, they stay in this commit.

---

<p align="center">
  <em>Made with 💙 by someone who's been there.</em>
</p>
