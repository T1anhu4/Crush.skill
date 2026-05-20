---
name: crush-skill
description: Relationship Persona Simulation Engine. Build a digital twin from chat history or custom 5-layer persona. Slash commands: /start-crush, /custom-crush, /import-chats, /chat, /crush-dashboard, /crush-postmortem, /let-go, /list-crushes, /crush-llm. For dating-coaching, relationship analysis, chat record import, personality simulation.
license: MIT
compatibility: python3.10+, auto-installs deps. Claude Code, OpenClaw, QwenPaw, WorkBuddy, Codex, Cursor.
metadata:
  version: "2.1.0"
  author: T1anhu4
  platforms: [claude_code, openclaw, qwenpaw, workbuddy, codex, cursor]
  tags: [relationship, persona, simulation, psychology, dating, coaching, chat-import]
allowed-tools: Bash(python3:*) Bash(pip:*) Bash(git:*) Read Write
---

# Crush.skill — Relationship Persona Simulation Engine

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/start-crush [archetype]` | Start a new session with a preset personality. Archetypes: `emotional`, `security`, `experience`, `value`, `passive`. |
| `/custom-crush` | Build a fully custom 5-layer persona. Complete control over every dimension. |
| `/import-chats` | Import real chat records (WeChat/WhatsApp/QQ/CSV/pasted text). Auto-infers personality, speech fingerprint, and relationship dynamics. |
| `/chat [message]` | Send a message to the persona. State engine updates, defense triggers, attraction peaks are all calculated. |
| `/crush-dashboard` | View the 8-dimensional relationship state dashboard. |
| `/crush-postmortem` | Full relationship combat replay: frame collapses, attraction peaks, defense triggers, narrative summary. |
| `/list-crushes` | List all saved sessions. |
| `/let-go [session]` | Ritual closure. Deletes the session with an uplifting goodbye message. |
| `/crush-llm [api_key]` | Configure LLM for semantic dialogue analysis. Optional — local analyzer works without it. |

## How to Use

### 1. Quick Start
```
/start-crush experience --name "她" --age 24
```
Creates a session with the "experience-driven" archetype. You'll see the full 5-layer persona, initial state, and a runtime prompt ready to feed into the LLM.

### 2. Import Real Chat Records
```
/import-chats
```
Then paste your chat history. The engine will:
- Auto-detect format (WeChat / WhatsApp / CSV / plain text)
- Parse all messages
- Infer personality traits (Big Five, MBTI, attachment style, love language)
- Extract speech fingerprint (signature phrases, emoji patterns, humor style)
- Estimate current favorability and tension baselines

You can also point to a file:
```
/import-chats --file ./chats/wechat_export.txt
```

### 3. Chat With the Persona
```
/chat "周末有空一起去看电影吗？"
```
Returns the updated state, delta changes, any triggered events (defense triggered, attraction peak, frame collapse risk), and a runtime prompt you can feed to the LLM to generate the NPC's response.

### 4. Check the Dashboard
```
/crush-dashboard
```
Shows all 8 state dimensions with current values and recent events.

### 5. Run a Postmortem
```
/crush-postmortem
```
Get a complete diagnostic report:
- Frame collapse points — where things went wrong
- Attraction peaks — what you did right
- Defense triggers — what made them put up walls
- Narrative summary with actionable insights

### 6. Let Go
```
/let-go demo
```
When you're ready. Deletes the session and gives you a closure message.

### 7. LLM Configuration
```
/crush-llm
```
Shows current LLM configuration. In Claude Code, it auto-detects the platform and uses Claude by default.

```
/crush-llm sk-your-api-key
```
Override with a custom OpenAI-compatible API key for dialogue analysis.

## The 5-Layer Persona

Every persona is built from five layers. You can configure any layer in `/custom-crush`:

| Layer | Field | Example |
|-------|-------|---------|
| **Hard Rules** | Topics off-limits, reply speed, ghost probability | `"topics_off_limits": ["前任", "体重"]` |
| **Identity** | MBTI, Big Five, age, values, insecurities | `"mbti": "INFJ", "core_values": ["真诚"]` |
| **Expression** | Signature phrases, emoji style, humor | `"signature_phrases": ["笑死", "确实"]` |
| **Emotional** | Attachment style, love language, conflict pattern | `"attachment_style": "Fearful_Avoidant"` |
| **Relational** | Stage, shared history, inside jokes, power dynamic | `"relationship_stage": "talking"` |

## Memory System

Crush.skill uses a **3-tier memory architecture**:

1. **SQLite long-term memory** — persistent, source-of-truth for all sessions
2. **mem0 semantic memory** — auto-installed, provides embedding-based retrieval for more human-like recall
3. **Summary compression** — automatic periodic summarization to keep context manageable

Memory auto-loads when you re-use a session ID. No manual save/load needed.

## Platform Detection

The engine auto-detects which platform it's running on:
- **Claude Code** — uses Claude's built-in LLM for dialogue analysis
- **OpenClaw** — uses platform default model
- **QwenPaw / WorkBuddy** — falls back to local analysis (or configure with `/crush-llm`)
- **Generic** — works anywhere with Python 3.10+

## Environment

No manual setup needed. On first run, the engine auto-installs `pyyaml` and `mem0`.
For LLM-powered analysis (higher accuracy), use `/crush-llm [api_key]`.
