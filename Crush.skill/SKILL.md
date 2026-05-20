---
name: crush-skill
description: Relationship Persona Simulation Engine. Build a digital twin of someone from chat history or custom configuration. 5-layer personality model (hard rules, identity, expression, emotional patterns, relational context), nonlinear state dynamics, LLM-powered dialogue analysis. Use when: (1) Importing chat records to reconstruct someone's personality, (2) Simulating romantic interactions for learning, (3) Analyzing relationship dynamics, (4) Running postmortem to understand what went wrong, (5) Custom sandbox with full persona configuration.
license: MIT
compatibility: Requires python3.10+, pyyaml. Optional: openai (for LLM dialogue analysis)
metadata:
  version: "2.0.0"
  author: Crush.skill contributors
  platforms:
    - claude_code
    - openclaw
    - qwenpaw
    - workbuddy
    - codex
    - cursor
  tags:
    - relationship
    - persona
    - simulation
    - psychology
    - dating
    - coaching
allowed-tools: Bash(python3:*) Bash(git:*) Read
---

# Crush.skill — Relationship Persona Simulation Engine

> 不是为了替代真实的人，而是为了帮你更理解人心。

## What it does

Build a realistic digital persona of someone — from chat history, from scratch, or from archetype presets. Interact with them. See how relationship dynamics change. Understand what works and what doesn't.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Start quickly with a preset personality | `python3 execute.py --action quick_start --session-id demo --config-json '{"archetype":"experience"}'` |
| Build fully custom persona | `python3 execute.py --action custom_sandbox --session-id custom --config-json '{"persona":{...}}'` |
| Import WeChat/WhatsApp chat records | `python3 execute.py --action chat_import --session-id real --source-text-file ./chats/wechat_export.txt` |
| Send a message and see state changes | `python3 execute.py --action chat_turn --session-id demo --message "你今天状态看起来不错"` |
| Run relationship diagnostics | `python3 execute.py --action postmortem --session-id demo` |
| View current relationship dashboard | `python3 execute.py --action dashboard --session-id demo` |
| List all sessions | `python3 execute.py --action list_sessions` |
| Ritual closure | `python3 execute.py --action let_go --session-id demo` |

## Architecture

```
┌────────────────────────────────────────────────────────┐
│ Layer 4: NPC Runtime (LLM — Claude/GPT)               │
│   Generates persona-consistent responses              │
│   Injected with: full persona + state + memory        │
├────────────────────────────────────────────────────────┤
│ Layer 3: Dialogue Analysis (LLM or local)              │
│   Semantic understanding of messages                  │
│   Outputs: valence, neediness, pressure, authenticity │
├────────────────────────────────────────────────────────┤
│ Layer 2: Nonlinear State Engine (Python)               │
│   S-curve saturation, habituation, tipping points     │
│   10-dimensional state vector with cross-coupling     │
├────────────────────────────────────────────────────────┤
│ Layer 1: 5-Layer Persona Model (Python + YAML)        │
│   Hard Rules → Identity → Expression → Emotional →   │
│   Relational Context                                  │
└────────────────────────────────────────────────────────┘
```

## The 5-Layer Persona

| Layer | What it captures |
|-------|-----------------|
| **Hard Rules** | Non-negotiable boundaries, reply speed, ghost probability, tone restrictions |
| **Identity** | MBTI, Big Five, age, gender, life stage, core values, insecurities, self-perception |
| **Expression** | Signature phrases, filler words, emoji style, sentence structure, humor style — the *speech fingerprint* |
| **Emotional** | Attachment style, love language, conflict style, stress response, mood volatility, trauma sensitivity |
| **Relational** | Relationship stage, shared history, inside jokes, power dynamic, their view of you |

## Chat Record Import

Supports automatic format detection for:
- **WeChat exports** (WeChatMsg / 留痕 / PyWxDump)
- **WhatsApp** .txt exports
- **QQ** chat exports
- **CSV** structured imports
- **Plain text** pasted conversations

The import pipeline extracts:
- Personality traits (Big Five, MBTI, attachment style, love language)
- Speech fingerprint (signature phrases, emoji patterns, sentence style)
- Relationship phase and dynamics
- Estimated favorability and tension baselines

## Custom Persona Sandbox

Full control over every dimension. Pass a complete 5-layer persona object:

```json
{
  "persona": {
    "identity": {"name": "她", "mbti": "INFJ", "age": 25, ...},
    "expression": {"signature_phrases": ["笑死", "确实"], "emoji_style": "heavy", ...},
    "emotional": {"attachment_style": "Anxious", "love_language": "words_of_affirmation", ...},
    "relational": {"relationship_stage": "dating", "power_dynamic": "balanced", ...}
  }
}
```

## Environment Variables

- `CRUSH_MEMORY_BACKEND=sqlite|mem0` (default: sqlite)
- `OPENAI_API_KEY` — enables LLM-powered dialogue analysis (much better accuracy)
- `CRUSH_ANALYZER_MODEL` — model for analysis (default: gpt-4o-mini)

## Output

All actions output JSON with `success: true/false`. Key fields:
- `state` — 10-dimensional relationship state vector
- `delta` — per-turn state changes
- `persona` — full 5-layer persona object
- `runtime_prompt` — LLM-ready persona prompt for NPC roleplay
- `dashboard` — human-readable state cards
- `markdown` — postmortem report (for postmortem action)
