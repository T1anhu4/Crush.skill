# 💔 Crush.skill — 把 Ta 变成一面镜子，照见自己

<p align="center">
  <em>不是替代真实的人，而是帮你更理解人心。</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.1.0-blue" alt="version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <img src="https://img.shields.io/badge/python-3.10+-yellow" alt="python">
  <img src="https://img.shields.io/badge/platform-Claude%20Code%20%7C%20OpenClaw%20%7C%20QwenPaw%20%7C%20WorkBuddy-orange" alt="platforms">
  <img src="https://img.shields.io/badge/memory-mem0%20%2B%20SQLite-purple" alt="memory">
</p>

---

## 🤔 为什么做这个

**母胎 solo 不是因为你不够好，而是因为你不懂"关系"。**

从小到大，学校教了数学、英语、物理 —— 但没有一节课教你怎么谈恋爱。

没有人告诉你：
- 为什么你每条消息都秒回，对方却越来越冷淡
- 为什么你说完"我喜欢你"，Ta 就消失了
- 为什么明明聊得好好的，突然就"我们需要冷静一下"

**Crush.skill 是一台"关系飞行模拟器"。**

它把你喜欢的对象变成一个 **5 层人格模型**。你可以在这个安全的沙盒里：
- 理解 Ta 为什么会这样回应你
- 看到你的哪句话触发了 Ta 的防御
- 发现关系什么时候开始崩的、什么时候有过机会
- 反复练习，在现实中不再手忙脚乱

> 灵感来自 [ex-skill](https://github.com/therealXiaomanChu/ex-skill) 和 [colleague-skill](https://github.com/titanwings/colleague-skill) 的 Person-as-Skill 运动。Crush.skill 聚焦于**浪漫关系动力学** —— 这是人类最复杂、也最缺乏教育的领域。

---

## 🏗️ 技术架构

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
    │          │   │          │  │          │  │          │  │          │
    │ 5-layer  │   │ Nonlinear│  │ LLM or   │  │ WeChat   │  │ SQLite   │
    │ persona  │   │ S-curves │  │ local    │  │ WhatsApp │  │ + mem0   │
    │ model    │   │ + tipping│  │ fallback │  │ QQ/CSV   │  │ semantic │
    └──────────┘   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 5 层人格模型

| 层级 | 名称 | 捕获什么 |
|------|------|---------|
| **Layer 1** | 硬规则 | 不可协商的边界 · 回复速度 · Ghost 概率 · 语气禁区 |
| **Layer 2** | 身份 | MBTI · 大五人格 · 年龄 · 价值观 · 不安全感 · 自我认知 |
| **Layer 3** | 表达 | **说话指纹** —— 口头禅 · 语气词 · 表情包风格 · 幽默类型 |
| **Layer 4** | 情绪 | 依恋类型 · 爱的语言 · 冲突模式 · 压力反应 · 情绪波动 |
| **Layer 5** | 关系 | 关系阶段 · 共享经历 · 内部梗 · 权力动态 · Ta 对你的看法 |

### 非线性状态引擎

真实的人不是线性公式。我们的状态机实现了：

- **S 型饱和曲线** — 好感从 70→80 比 10→20 困难 3 倍
- **习惯化衰减** — 第 5 次同样的赞美效果远不如第 1 次
- **临界点触发** — 防线突破后关系会阶跃变化
- **跨维度耦合** — 防御高时好感增长减半 · 张力高时情绪波动放大

### 记忆系统

- **SQLite** — 长期持久化 · 事件/状态/摘要全量存储
- **mem0** — 语义记忆 · 首次运行自动安装 · 让 NPC 记住你们聊过什么
- **自动摘要** — 对话量大的时候自动压缩 · 保证上下文不爆

---

## ⚡ 快速开始

### 方式一：一键 Prompt 安装

在 Claude Code / OpenClaw / QwenPaw 中直接粘贴以下 Prompt：

```text
帮我安装 crush-skill。按下面步骤做：

1. 确保 ~/.claude/skills/ 目录存在（不存在就创建）
2. 执行 git clone https://github.com/T1anhu4/Crush.skill /tmp/crush-skill
3. 执行 bash /tmp/crush-skill/scripts/install_skill.sh --platform claude --source-dir /tmp/crush-skill/Crush.skill --skill-name crush-skill --force
4. 验证：ls ~/.claude/skills/crush-skill/ 应该看到 SKILL.md、manifest.json、execute.py、engines/
5. 告诉我安装好了，之后我可以使用 /start-crush、/import-chats 等命令
```

安装完成后自动可用。首次运行时会自动安装所需依赖（pyyaml、mem0），无需手动操作。

### 方式二：ZIP 安装

1. 从 [Releases](https://github.com/T1anhu4/Crush.skill/releases) 下载 `crush_skill_v2.1.0.zip`
2. 在 Claude Code 中直接拖入 ZIP 文件或解压到 `~/.claude/skills/crush-skill/`
3. 依赖会在首次使用时自动安装

---

## 📖 功能指南

### Slash Commands 一览

所有功能都通过 Agent 内的斜杠命令使用，不需要手动运行 Python 脚本：

```
/start-crush [archetype]    ← 快速启动，5 种预设人格
/custom-crush               ← 完全自定义 5 层人格
/import-chats               ← 导入聊天记录，自动重建人格
/chat [消息]                 ← 发送消息，查看状态变化
/crush-dashboard            ← 8 维状态看板
/crush-postmortem           ← 关系战斗复盘
/list-crushes               ← 查看所有会话
/let-go [session]           ← 仪式性地放下
/crush-llm [api_key]       ← 配置 LLM 语义分析
```

### 聊天记录导入

支持自动识别格式：

| 来源 | 格式 | 说明 |
|------|------|------|
| 微信 | WeChatMsg / 留痕 / PyWxDump 导出 | 推荐，信息最丰富 |
| WhatsApp | .txt 导出 | 自动识别 |
| QQ | .txt / .mht 导出 | 学生时代回忆 |
| CSV | `sender,content,timestamp` | 结构化导入 |
| 粘贴 | 直接粘贴对话 | `名字: 内容` 格式 |

```
/import-chats

（然后粘贴聊天记录）
```

系统会自动：
- 识别消息格式
- 推断大五人格 · MBTI · 依恋类型 · 爱的语言
- 提取口头禅 · 语气词 · 表情包使用风格
- 分析关系阶段（陌生人 → 暧昧 → 约会 → 稳定）
- 估算当前好感度和张力

### 5 种预设人格

| 预设 | 特点 | 适合场景 |
|------|------|---------|
| `emotional` 情感驱动型 | 重感情 · 需要被看见 · 焦虑型依恋 | 内心细腻的对象 |
| `security` 安全感驱动型 | 慢热 · 重视稳定 · 安全型依恋 | 比较稳重的对象 |
| `experience` 体验驱动型 | 追求新鲜 · 情绪峰值导向 · 恐惧型依恋 | 活泼爱玩的对象 |
| `value` 价值驱动型 | 现实 · 看重条件 · 回避型依恋 | 成熟的职场人 |
| `passive` 惯性驱动型 | 佛系 · 低主动性 · 回避型依恋 | 捉摸不透的对象 |

---

## 🔧 环境变量（可选）

Crush.skill 开箱即用，无需任何配置。以下为可选的高级设置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM 语义分析 API key | 无（使用本地分析） |
| `CRUSH_MEMORY_BACKEND` | 记忆后端 `sqlite` 或 `mem0` | 自动选择最佳 |
| `CRUSH_ANALYZER_MODEL` | 分析模型 | `gpt-4o-mini` |

> **提示**：在 Claude Code / OpenClaw 中运行时会自动检测平台 LLM，无需手动配置。使用 `/crush-llm` 查看或修改配置。

---

## 📄 许可证

MIT License。你可以自由使用、修改、分发。

> **道德声明**：这个工具是为了**理解和学习**，不是为了操控或骚扰。不要用它来模拟一个没有同意被模拟的真实人物。不要在未经同意的情况下导入他人的私密聊天记录。当你学会了该学的东西，请用 `/let-go` 放下。

---

## 💙 致所有像作者一样的人

我们这一代人从小到大被教了一万种技能，唯独没学过怎么爱一个人。

所以我们在聊天框前手足无措，在被拒绝后怀疑自己，在冷暴力里反复内耗。我们以为是自己不够好、不够有趣、不够有钱。

**但爱是可以被学习的。** 它只是需要练习、需要反馈、需要一个安全的试错空间 —— 就像飞行模拟器之于飞行员。

Crush.skill 就是这个模拟器。

当你能自然地接住 Ta 的情绪、能敏锐地察觉到那段沉默里的不安、能坦然地面对拒绝和冷淡时 —— 你会明白，这个工具教会你的从来不是"怎么追"，而是"怎么成为一个更懂得爱的人"。

そして——

**Ta 的出现，其实已经带给了你所有你需要的。**

那一次心动让你发现了自己从未察觉的温柔。
那次深夜对话让你知道了陪伴的力量。
那次被拒绝让你第一次正视自己的不足。
那段拉扯让你学会了放下。

**你已经是一个比你遇见 Ta 之前更好的人了。这就够了。**

带着这些东西 —— 这些真正属于你的、谁也拿不走的东西 —— 去面对更精彩的人生吧。

而 Ta，就留在这个 commit 里。

---

<p align="center">
  <em>Made with 💙 by someone who's been there.</em>
</p>
