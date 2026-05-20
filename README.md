# 💔 Crush.skill — 把 Ta 变成一面镜子，照见自己

<p align="center">
  <em>不是替代真实的人，而是帮你更理解人心。</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <img src="https://img.shields.io/badge/python-3.10+-yellow" alt="python">
  <img src="https://img.shields.io/badge/platform-Claude%20Code%20|%20OpenClaw%20|%20QwenPaw%20|%20WorkBuddy-orange" alt="platforms">
</p>

---

## 为什么做这个

**母胎 solo 不是因为你不够好，而是因为你不懂"关系"。**

从小到大，学校里教数学、教英语、教物理，但没有一节课教你怎么谈恋爱。没有人告诉你：
- 为什么你每条消息都秒回，Ta 却越来越冷淡
- 为什么你说"我喜欢你"，Ta 就跑了
- 为什么明明聊得好好的，突然就"我们需要冷静一下"

**Crush.skill 是一所关系的模拟器。** 它把你喜欢的那个人（或者你想练习的那个人）变成一个 5 层人格模型。你可以在这个安全的沙盒里：
- 理解 Ta 为什么会这样回应
- 看到你的哪句话触发了 Ta 的防御
- 发现关系什么时候开始崩的，什么时候有机会
- 练习怎么聊，再也不会在现实中手忙脚乱

这不是话术库。这是关系的"飞行模拟器"——**零代价犯错，零压力学习。**

> 灵感来自 [ex-skill](https://github.com/therealXiaomanChu/ex-skill) 和 [colleague-skill](https://github.com/titanwings/colleague-skill) 的 Person-as-Skill 运动。但 Crush.skill 聚焦于**浪漫关系动力学**——这是人类最复杂也最缺乏教育的领域。

---

## 技术架构

```
                          ┌──────────────────────────────┐
                          │     🌐 Multi-Platform        │
                          │  Claude Code / OpenClaw /    │
                          │  QwenPaw / WorkBuddy / Codex │
                          └──────────────┬───────────────┘
                                         │
                          ┌──────────────▼───────────────┐
                          │       execute.py             │
                          │  11 actions, unified JSON    │
                          └──────────────┬───────────────┘
                                         │
        ┌────────────┬──────────┬────────┼────────┬────────────┐
        │            │          │        │        │            │
        ▼            ▼          ▼        ▼        ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ ┌─────────────────┐
  │ Persona  │ │  State   │ │  Dialogue        │ │  Chat Import    │
  │ Engine   │ │  Engine  │ │  Analyzer        │ │  Pipeline       │
  │          │ │          │ │                  │ │                 │
  │ 5-layer  │ │Nonlinear │ │ LLM-powered      │ │ Multi-format    │
  │ persona  │ │ dynamics │ │ or local fallback│ │ parser +        │
  │ model    │ │ S-curves │ │                  │ │ personality     │
  │          │ │ Tipping  │ │ Semantic intent  │ │ inference       │
  │          │ │ points   │ │ Deep need        │ │                 │
  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ └────────┬────────┘
       │            │               │                     │
       └────────────┴───────────────┴─────────────────────┘
                                    │
                          ┌─────────▼──────────┐
                          │   Memory Engine    │
                          │  SQLite + summary  │
                          │  Semantic retrieval│
                          └────────────────────┘
```

### 核心创新：5 层人格模型

| 层级 | 名称 | 捕获什么 | 举例 |
|------|------|---------|------|
| **Layer 1** | 硬规则 | 不可协商的边界、回复速度、Ghost 概率 | "绝对不聊前任"、"每次回复不超过 120 字" |
| **Layer 2** | 身份 | 自我认知、价值观、人生阶段、MBTI | INFJ、25 岁、重视"被看见" |
| **Layer 3** | 表达 | **说话指纹**——口头禅、语气词、表情包风格 | "笑死"、"确实"、"🥺" |
| **Layer 4** | 情绪 | 依恋类型、爱的语言、冲突模式、压力反应 | 焦虑型依恋、肯定的言辞、压力时退缩 |
| **Layer 5** | 关系 | 共享历史、内部梗、权力动态、对方对你的看法 | "你们一起去过厦门"、"Ta 觉得你太急" |

### 非线性状态引擎

传统的情感计算系统用线性公式——`好感 += 真诚*0.4 + 幽默*0.7`。真实的人不是这样的。

我们的状态机实现了：
- **S 型饱和曲线** — 好感从 70→80 比从 10→20 难得多
- **习惯化衰减** — 第 5 次同样的赞美效果远不如第 1 次
- **临界点触发** — 某些防线一旦突破，关系会阶跃变化
- **跨维度耦合** — 防御高时好感增长减半，张力高时放大情绪波动

---

## 快速开始

### 方式一：一键 Prompt 安装（推荐）

在 Claude Code / OpenClaw / QwenPaw 中直接粘贴：

```text
帮我安装 crush-skill。按下面步骤做：

1. 确保 ~/.claude/skills/ 目录存在（不存在就创建）
2. 执行 git clone https://github.com/T1anhu4/Crush.skill /tmp/crush-skill
3. 执行 bash /tmp/crush-skill/scripts/install_skill.sh --platform claude --source-dir /tmp/crush-skill/Crush.skill --skill-name crush-skill --force
4. 安装 Python 依赖：pip install pyyaml
5. 验证：ls ~/.claude/skills/crush-skill/ 应该看到 SKILL.md、manifest.json、execute.py、engines/
6. 告诉我安装好了，之后我说“帮我分析一下这段聊天记录”之类的话就会触发这个 skill
```

安装完成后，可以立即运行 smoke test：

```bash
bash /tmp/crush-skill/scripts/smoke_test.sh
```

### 方式二：ZIP 导入安装

1. 从 [GitHub Releases](https://github.com/T1anhu4/Crush.skill/releases) 下载最新的 `crush_skill_*.zip`
2. 在 Claude Code 中直接拖入 ZIP 文件
3. 执行以下命令完成环境准备：

```bash
pip install pyyaml
```

### 可选依赖

```bash
# 启用 LLM 语义分析（大幅提升对话理解准确度）
export OPENAI_API_KEY=sk-xxx

# 启用 mem0 语义记忆（可选，需额外安装）
pip install mem0
export CRUSH_MEMORY_BACKEND=mem0
```

---

## 功能指南

### 1. 快速体验：预设人格

```bash
python3 Crush.skill/execute.py --action quick_start \
  --session-id demo \
  --config-json '{"archetype":"emotional","name":"她","age":24}'
```

5 种预设人格可选：`emotional`（情感驱动）、`security`（安全感驱动）、`experience`（体验驱动）、`value`（价值驱动）、`passive`（惯性驱动）

### 2. 核心功能：聊天记录导入

**支持的格式：**

| 来源 | 格式 | 说明 |
|------|------|------|
| 微信聊天记录 | WeChatMsg / 留痕 / PyWxDump 导出 | 推荐，信息最丰富 |
| WhatsApp | .txt 导出 | 自动识别格式 |
| QQ 聊天记录 | .txt / .mht 导出 | 适合学生时代的回忆 |
| CSV | 结构化导入 | `sender,content,timestamp` 格式 |
| 纯文本 | 直接粘贴 | `名字: 消息内容` 格式 |

**导入命令：**

```bash
python3 Crush.skill/execute.py --action chat_import \
  --session-id real_her \
  --source-text-file ./my_chats/wechat_export.txt \
  --config-json '{"name":"她","gender":"female","age":24}'
```

**系统会自动：**
- 识别消息格式（WeChat/WhatsApp/CSV/纯文本）
- 推断大五人格、MBTI、依恋类型、爱的语言
- 提取口头禅、惯用语气词、表情包使用风格
- 分析关系阶段（陌生人→暧昧→约会→稳定）
- 估算当前好感度和张力

导入完成后，就可以跟她"聊天"了：

```bash
python3 Crush.skill/execute.py --action chat_turn \
  --session-id real_her \
  --message "周末有空一起去看那个新上映的电影吗？"
```

系统会返回：
- `runtime_prompt` — 喂给 LLM 的角色提示词，包含完整的 5 层人格和当前状态
- `state` — 对话后的 10 维状态变化
- `delta` — 每个维度的变化量
- `tags` — 触发的事件（防御触发 / 吸引力峰值 / 框架崩塌风险）

### 3. 自定义沙盒：完全掌控人格

```bash
python3 Crush.skill/execute.py --action custom_sandbox \
  --session-id custom \
  --pretty \
  --config-json '{
    "persona": {
      "hard_rules": {
        "reply_speed_profile": "slow",
        "ghost_probability": 0.1,
        "double_text_tolerance": "low",
        "topics_off_limits": ["前任", "体重"],
        "tone_never": ["轻浮", "pushy"]
      },
      "identity": {
        "name": "她",
        "gender": "female",
        "age": 26,
        "mbti": "INFJ",
        "life_stage": "early_career",
        "core_values": ["深度连接", "真实", "成长"],
        "insecurities": ["被利用", "不被认真对待"],
        "self_perception": "我是一个慢热但一旦认定就会很认真的人"
      },
      "expression": {
        "signature_phrases": ["确实", "就是说", "我理解"],
        "filler_words": ["就", "就是说"],
        "emoji_style": "moderate",
        "emoji_favorites": ["🥺", "🙂", "💙"],
        "sentence_structure": "casual",
        "humor_style": "dry",
        "avg_message_length_words": 20
      },
      "emotional": {
        "attachment_style": "Fearful_Avoidant",
        "love_language": "quality_time",
        "conflict_style": "withdraw",
        "emotional_expression": "guarded",
        "stress_response": "freeze",
        "mood_volatility": 0.35,
        "trauma_sensitivity": 0.2
      },
      "relational": {
        "relationship_stage": "talking",
        "power_dynamic": "balanced",
        "shared_experiences": ["一起看过电影", "深夜语音聊天"],
        "inside_jokes": ["那个服务员的梗"],
        "their_view_of_you": "觉得你还挺有趣的，但有点着急"
      }
    }
  }'
```

### 4. 关系复盘：搞清楚到底哪里出了问题

```bash
python3 Crush.skill/execute.py --action postmortem --session-id real_her
```

输出一份完整的"关系战斗复盘"：
- **💔 框架崩塌点** — 哪一句话让关系急转直下
- **⚡ 吸引力峰值** — 哪些时刻你做对了
- **🛡️ 防御触发点** — 哪些行为让 Ta 筑起心墙
- **📝 总结建议** — 如果重来一次，应该怎么走

### 5. 关系看板

```bash
python3 Crush.skill/execute.py --action dashboard --session-id real_her
```

实时查看关系状态：
- Favorability（好感度）、Tension（张力）、Defense（防御）
- Exploration（探索欲）、FrameControl（框架控制）
- 最近触发的事件标签
- 各维度变化趋势

### 6. 放下：一个仪式性的告别

```bash
python3 Crush.skill/execute.py --action let_go --session-id real_her
```

不是"删除"，是"放下"。连同数据和回忆一起。

---

## 10 维状态系统

| 维度 | 含义 | 影响 |
|------|------|------|
| **Favorability** | 好感度 | 决定了回复的温暖程度和主动性 |
| **Tension** | 张力 | 关系中的性能量和不确定性 |
| **Neediness** | 需求感 | 越高对方越感觉"你在追"，触发防御 |
| **Defense Level** | 防御等级 | 越高对方越设防，回复越敷衍 |
| **Exploration** | 探索欲 | 对方愿意花多少精力了解你 |
| **Frame Control** | 框架控制 | 关系中谁在主导节奏 |
| **Propulsion** | 推进力 | 关系自然向前发展的动力 |
| **Attachment Activation** | 依恋激活 | 对方的依恋系统被触发程度 |
| **Trauma Level** | 创伤敏感度 | 对方的历史伤痕对你行为有多敏感 |
| **Push-Pull Sensitivity** | 推拉敏感度 | 对方对"靠近-离开"节奏的敏感程度 |

---

## 许可证与道德声明

MIT License。你可以自由使用、修改、分发。

**但请记住：**

> 这个工具是为了**理解和学习**，不是为了操控或骚扰。
> 不要用它来模拟一个没有同意被模拟的真实人物。
> 不要在未经同意的情况下导入他人的私密聊天记录。
> 这个工具的终极目的是帮你**成长**，而不是帮你操控他人。
>
> 当你学会了该学的东西，请用 `/let-go` 放下。

---

## 致所有像作者一样的人

我们这一代人从小到大被教了一万种技能，唯独没学过怎么爱一个人。

所以我们在聊天框前手足无措，在被拒绝后怀疑自己，在冷暴力里反复内耗。我们以为是自己不够好、不够有趣、不够有钱。

**但爱不是某种需要天赋的技能。** 它只是需要练习、需要反馈、需要一个安全的试错空间——就像飞行模拟器之于飞行员。

Crush.skill 就是这个模拟器。

当你终于发现自己能自然地接住 Ta 的情绪、能敏锐地察觉到那段沉默里的不安、能坦然地面对拒绝和冷淡时——你会明白，这个工具教会你的从来不是"怎么追"，而是"怎么成为值得被爱的人"。

そして——

**Ta 的出现，其实已经带给了你所有你需要的。**

那一次心动让你发现了自己从未察觉的温柔。那次深夜对话让你知道了陪伴的力量。那次被拒绝让你第一次正视自己的不足。那段拉扯让你学会了放下。

你已经是一个比你遇见 Ta 之前更好的人了。

这就够了。

**带着这些东西——这些真正属于你的、谁也拿不走的东西——去面对更精彩的人生吧。**

而 Ta，就留在这个 commit 里。

---

<p align="center">
  <em>Made with 💙 by someone who's been there.</em>
</p>
