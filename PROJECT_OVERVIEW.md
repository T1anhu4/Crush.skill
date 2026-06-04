# Crush.skill Project Overview

这份文档是给项目作者和维护者看的。README 负责让开源用户快速理解和安装；这份文档负责解释现在 Crush.skill 到底有哪些能力、技术框架怎么分层、每个文件负责什么，以及后续改项目时应该从哪里下手。

---

## 1. 项目定位

Crush.skill 现在有两种产品形态：

| 形态 | 面向谁 | 入口 | 说明 |
|------|--------|------|------|
| Agent Skill | Claude Code、OpenClaw、QwenPaw、Codex、Cursor 等 Agent 用户 | `Crush.skill/execute.py` | 宿主 Agent 调用 action，拿到 JSON 和隐藏 runtime prompt，再生成自然角色回复。 |
| Standalone CLI | 不想折腾 Agent、想本地直接聊天的用户 | `crush_cli/app.py` | 用户运行 `crush`，在终端里导入聊天、配置模型、聊天、看报告。 |

核心目标不是“AI 陪聊”，而是关系训练：帮助用户识别好感、边界、需求感、推进时机、关系阶段和对方可能的性格/互动模式。

---

## 2. 当前核心能力

### 2.1 聊天记录导入

入口：`chat_import` action 或 CLI `/import`。

支持格式：微信、WhatsApp、QQ、CSV、粘贴文本。

导入后会生成三类东西：

1. **Persona**：说话指纹、口头禅、梗、emoji、边界、共同经历。
2. **Initial State**：初始好感、张力、防御、探索欲等关系状态。
3. **Episodes**：最多 300 条原始聊天片段写入 SQLite，后续可召回。

相关文件：

| 文件 | 作用 |
|------|------|
| `Crush.skill/engines/chat_import.py` | 解析聊天格式，提取人格和关系信号。 |
| `Crush.skill/execute.py` | `chat_import_mode()` 把解析结果写入 persona、state、memory。 |
| `Crush.skill/engines/memory_engine.py` | 保存导入消息、状态历史和摘要。 |

---

### 2.2 5 层人格模型

入口：`quick_start`、`custom_sandbox`、`chat_import`。

5 层结构：

| 层 | 含义 | 例子 |
|----|------|------|
| Hard Rules | 硬边界和回复规则 | 话题禁区、double text 容忍度、消息长度。 |
| Identity | 身份和人格底色 | MBTI、大五、年龄、价值观、自我认知。 |
| Expression | 表达 DNA | 口头禅、语气词、表情包、幽默类型。 |
| Emotional | 情绪系统 | 依恋类型、爱的语言、压力反应、情绪波动。 |
| Relational | 关系上下文 | 关系阶段、共同经历、内部梗、Ta 对你的看法。 |

相关文件：

| 文件 | 作用 |
|------|------|
| `Crush.skill/engines/persona_engine.py` | Persona dataclass、preset/custom 构建、runtime prompt 生成。 |
| `Crush.skill/presets/*.yaml` | 5 种预设人格原型。 |
| `Crush.skill/prompts/npc_runtime.txt` | 角色回复时的核心提示结构。 |

---

### 2.3 对话语义和关系读秒

入口：`chat_turn` action 或 CLI 普通输入。

每轮用户发话后，会先做语义识别，再更新关系状态，最后给出 coach readout。

识别内容包括：

- 表层意图：普通聊天、邀约、确认关系、开玩笑、拒绝等。
- 潜台词：索取确认、默认同意、边界试探、伤害性拉扯。
- 梗和网络语：笑死、抽象、地铁老人看手机、我真的会谢等。
- 风险：需求感、压力、真实性、好感、暧昧窗口。
- 下一句建议：该推进、降速、换话题、回应具体信息，还是停止追问。

相关文件：

| 文件 | 作用 |
|------|------|
| `Crush.skill/engines/dialogue_analyzer.py` | 本地规则/LLM 对话分析入口。 |
| `Crush.skill/engines/pragmatics_engine.py` | 中文梗、潜台词、软拒绝、关系测试识别。 |
| `Crush.skill/engines/coach_engine.py` | 输出风险等级、关系读秒、下一句建议。 |
| `Crush.skill/execute.py` | `_apply_contextual_adjustments()` 对亲昵称呼、喜欢确认、伤害性拉扯做二次校正。 |

---

### 2.4 非线性关系状态机

入口：`StateEngine.apply_turn()`。

当前状态维度包括：

| 状态 | 含义 |
|------|------|
| favorability | 好感 |
| tension | 张力/暧昧拉扯感 |
| neediness | 用户需求感暴露程度 |
| frame_control | 用户是否稳住自身框架 |
| exploration | 对方愿意继续探索你的程度 |
| defense_level | 防御/抵触程度 |
| propulsion | 关系推进动能 |
| attachment_activation | 依恋触发程度 |
| trauma_level | 创伤/敏感负载 |
| push_pull_sensitivity | 对拉扯的敏感度 |

设计原则：

- 不是线性加减分。高分区增长更难，防御高时好感增长会被压制。
- 重复同一种动作会边际递减。
- 过快亲密称呼、逼问喜欢、伤害性拒绝会触发防御。
- 好感、张力、防御、需求感互相耦合，不是彼此独立。

相关文件：

| 文件 | 作用 |
|------|------|
| `Crush.skill/engines/state_engine.py` | 关系状态主更新逻辑。 |
| `Crush.skill/engines/defense_engine.py` | 防御触发和原因解释。 |
| `Crush.skill/engines/types.py` | CoreState、RelationshipProfile 等基础类型。 |

---

### 2.5 时间线主动性

入口：CLI 后台线程，不是 Agent Skill 的默认行为。

CLI 会维护一个本地时间线状态：

| 字段 | 含义 |
|------|------|
| `last_user_at` | 用户上次发消息时间 |
| `last_npc_at` | Ta 上次发消息时间 |
| `next_proactive_at` | 下一次可能主动发消息的时间 |
| `initiative` | Ta 当前主动性 |
| `warmth` | Ta 当前热情 |
| `ignored_streak` | 连续被忽略次数 |
| `low_priority_replies` | 用户低优先级回复次数 |
| `pending` | Ta 主动发了一条后，正在等用户回复 |

核心逻辑：

- Ta 主动发完后进入 pending，不会一直刷屏。
- 如果用户很久不回，会根据时间段和人格生成一次追问。
- 如果用户长期不回或总是“我刚打游戏”，主动性和热情会下降。
- 如果用户解释“加班刚下班，不是故意不回”，热情会保留或回升。
- `/stop` 暂停时间线，`/continue` 继续。

相关文件：

| 文件 | 作用 |
|------|------|
| `crush_cli/app.py` | `timeline_loop()`、`maybe_proactive_message()`、`resolve_pending_proactive()`。 |
| `Crush.skill/execute.py` | `proactive_prompt()` 生成主动消息的隐藏 prompt。 |

---

### 2.6 关系蒸馏报告

入口：`distillation_report` action 或 CLI `/distill`。

这是 v2.4.7 新增能力。它的作用不是继续聊天，而是把导入记录或当前会话变成“证据优先”的训练报告。

报告包括：

| 模块 | 说明 |
|------|------|
| Evidence Map | 每个判断尽量给出对应聊天证据。 |
| Persona DNA | 口头禅、梗、emoji、平均消息长度、问题比例。 |
| Relationship Radar | 主动/被动、I/E 倾向、热情/防备、朋友/暧昧、慢热/养鱼风险、物质/互惠风险。 |
| Coaching Playbook | 下一步建议、不要做什么、练习题。 |
| Validation Limits | 样本太少、无时间戳、证据不足时降低置信度。 |

重要边界：它不会因为一句“请我喝奶茶”就判定对方拜金，也不会因为一句玩笑就判定对方喜欢你。敏感标签必须以概率和证据形式出现。

相关文件：

| 文件 | 作用 |
|------|------|
| `Crush.skill/engines/distillation_engine.py` | 蒸馏报告核心逻辑。 |
| `Crush.skill/execute.py` | `distillation_report()` action。 |
| `crush_cli/app.py` | CLI `/distill` 命令和 `/import` 后 preview。 |

---

## 3. 数据流：一次聊天怎么发生

用户在 CLI 或 Agent 输入一句话：

```text
你喜欢我吗
```

内部流程：

1. `execute.py` 收到 `chat_turn`。
2. `dialogue_analyzer.py` 和 `pragmatics_engine.py` 分析语义，识别为“索取喜欢/关系确认”。
3. `execute.py` 的 contextual adjustments 再判断这是否属于直接验证压力。
4. `state_engine.py` 根据当前状态、人格、语义信号更新好感、张力、防御、需求感。
5. `coach_engine.py` 生成读秒：这是索取确认，风险较高，不建议继续逼问。
6. `memory_engine.py` 写入用户消息、状态快照、事件。
7. `persona_engine.py` 生成隐藏 runtime prompt。
8. Agent 或 CLI 模型用 runtime prompt 生成 Ta 的自然回复。
9. `record_reply` 把 Ta 的回复写回长期记忆。

---

## 4. 记忆系统为什么这样设计

默认使用 SQLite，而不是强制 mem0 或外部向量数据库。

原因：

- 开源项目必须先保证单机可运行。
- 用户导入的聊天记录很敏感，默认不应该发送到外部服务。
- 大多数场景下，persona memory + episode memory + summary + 本地检索已经够用。
- mem0 是可选增强，不是主记忆源。

SQLite 中保存：

| 表 | 保存内容 |
|----|----------|
| `sessions` | 当前 persona、profile、state、archetype。 |
| `episodes` | 用户消息、NPC 回复、导入聊天片段。 |
| `timeline_events` | 导入、触发、主动消息等事件。 |
| `state_history` | 每轮状态变化和 tags。 |
| `summaries` | 自动摘要，减少上下文爆炸。 |

---

## 5. Agent Skill 和 CLI 的区别

| 维度 | Agent Skill | Standalone CLI |
|------|-------------|----------------|
| 谁生成回复 | 宿主 Agent 模型 | CLI 配置的模型 |
| 用户看到什么 | 通常只看 NPC 回复 | NPC 回复 + 关系读秒 + 时间线 |
| 是否有主动消息 | 由宿主 Agent 决定 | CLI 内置后台时间线 |
| 配置方式 | skill 安装后由平台/环境决定 | `/model` 交互式配置 |
| 记忆目录 | `CRUSH_DATA_DIR` 或 skill data | 默认 `~/.crush/data` |

两者共用同一个 `Crush.skill/execute.py` runtime，所以核心状态和记忆逻辑一致。

---

## 6. 主要 action 一览

| action | 用途 |
|--------|------|
| `quick_start` | 用预设人格启动会话。 |
| `custom_sandbox` | 创建完整自定义人格。 |
| `chat_import` | 导入聊天记录并重建人格/状态/记忆。 |
| `distillation_report` | 输出关系蒸馏报告。 |
| `chat_turn` | 处理用户一句话，更新状态，返回 runtime prompt。 |
| `record_reply` | 保存模型生成的 NPC 回复。 |
| `proactive_prompt` | 为 CLI 时间线主动消息生成 prompt。 |
| `dashboard` | 返回关系状态看板。 |
| `postmortem` | 生成关系复盘报告。 |
| `list_sessions` | 列出本地会话。 |
| `delete_session` | 删除会话。 |
| `let_go` | 删除会话并返回放下文案。 |
| `configure_llm` | 配置或检测 LLM 分析能力。 |

---

## 7. 如果你要继续开发，应该从哪里改

| 想改什么 | 优先看哪里 |
|----------|------------|
| 角色不像真人 | `prompts/npc_runtime.txt`、`persona_engine.py`、`pragmatics_engine.py`。 |
| 关系分数不合理 | `state_engine.py`、`coach_engine.py`、`execute.py` contextual adjustments。 |
| 不懂梗/潜台词 | `pragmatics_engine.py` 和 `dialogue_analyzer.py`。 |
| 导入记录不准 | `chat_import.py`。 |
| `/distill` 报告不准 | `distillation_engine.py`。 |
| 时间线太频繁/太死板 | `crush_cli/app.py` 的 timeline 相关函数。 |
| README/安装体验 | `README.md`、`README_EN.md`、`scripts/install_cli.sh`、`scripts/install_skill.sh`。 |
| 打包发布 | `scripts/package_skill.py`、`scripts/package_cli.py`、`scripts/publish_release.sh`。 |

---

## 8. 测试和发布流程

本地检查：

```bash
python3 -m py_compile crush_cli/*.py Crush.skill/*.py Crush.skill/engines/*.py
bash scripts/smoke_test.sh
python3 scripts/package_skill.py && python3 scripts/package_cli.py
```

本地安装 CLI：

```bash
bash scripts/install_cli.sh --force
~/.crush/bin/crush
```

当前维护规则：

- `2.4` 是当前维护分支。
- 小版本用 `v2.4.x` 发布。
- 除非明确要求，不推 `main`。

---

## 9. 产品边界

这个项目要持续守住一条线：训练用户识别关系信号和尊重边界，而不是训练操控。

所以未来新增功能时需要注意：

- 不要把“技巧”写成让别人焦虑或上头的操控脚本。
- 对“拜金、养鱼、喜欢我、慢热”等判断保持证据和概率表达。
- 对私密聊天记录保持本地优先、最小外发。
- 对用户的错误聊天方式要指出来，但语气要像教练，不要羞辱。
