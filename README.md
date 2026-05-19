# Crush.skill

Crush是一个可运行、可扩展的 **Relationship Simulation Engine（人格关系模拟引擎）**。

不是“话术库”，而是把关系互动拆成可计算的状态机与可复盘的事件系统。

## 核心能力
- 三入口模式：`quick_start` / `custom_sandbox` / `reality_import`
- 动态状态机：`Favorability / Tension / Neediness / Defense / Exploration / FrameControl`
- 防御触发机制：高需求感与推进压力自动触发防御
- 关系记忆系统：`SQLite` 持久化 + 摘要压缩 + 混合检索
- Reality Import：从真实聊天/时间线反推人格结构与初始状态
- Post-Mortem：输出“框架崩塌点 / 吸引力峰值 / 防御触发点”

## 项目结构
- Skill 主目录: [`Crush.skill`](./Crush.skill)
- 安装脚本: [`scripts/bootstrap.sh`](./scripts/bootstrap.sh)
- 跨平台导入脚本: [`scripts/install_skill.sh`](./scripts/install_skill.sh)
- 打包脚本: [`scripts/package_skill.py`](./scripts/package_skill.py)
- 一句话导入模板: [`AGENT_IMPORT_PROMPTS.md`](./AGENT_IMPORT_PROMPTS.md)

## 快速开始

### 1) 一键安装
```bash
cd <repo-root>
bash scripts/bootstrap.sh
```

可选：安装 mem0 扩展依赖
```bash
cd <repo-root>
WITH_MEM0=1 bash scripts/bootstrap.sh
```

### 2) 一键自测
```bash
cd <repo-root>
bash scripts/smoke_test.sh
```

### 3) 打包导入包
```bash
cd <repo-root>
python3 scripts/package_skill.py
```

输出文件：
- `Crush.skill/dist/crush_skill_openclaw.zip`
- `Crush.skill/dist/crush_skill_qwenpaw.zip`

## 一句话导入 Skill（Claude Code / OpenClaw / QwenPaw）

把仓库地址替换为 `<GITHUB_REPO_URL>` 后，直接对 agent 说以下模板。

### Claude Code
```text
帮我安装 crush-skill 这个 Claude Code skill。请按下面步骤做：
1. 确保 ~/.claude/skills/ 目录存在（不存在就创建）
2. 执行 git clone <GITHUB_REPO_URL> /tmp/crush-skill
3. 执行 bash /tmp/crush-skill/scripts/install_skill.sh --platform claude --source-dir /tmp/crush-skill/Crush.skill --skill-name crush-skill --force
4. 验证：ls ~/.claude/skills/crush-skill/ 应该看到 SKILL.md、manifest.json、execute.py、engines/
5. 告诉我安装好了，之后我说“帮我做一次关系复盘”之类的话就会触发这个 skill
```

### OpenClaw
```text
帮我安装 crush-skill 到 OpenClaw。请按下面步骤做：
1. 执行 git clone <GITHUB_REPO_URL> /tmp/crush-skill
2. 执行 bash /tmp/crush-skill/scripts/install_skill.sh --platform openclaw --source-dir /tmp/crush-skill/Crush.skill --skill-name crush-skill --force
3. 验证安装目录（默认 ~/.openclaw/skills/crush-skill/，若你的 OpenClaw 有自定义目录就按实际目录验证），应看到 SKILL.md、manifest.json、execute.py、engines/
4. 告诉我安装完成并给我一个 quick_start 的调用示例
```

### QwenPaw
```text
帮我安装 crush-skill 到 QwenPaw。请按下面步骤做：
1. 执行 git clone <GITHUB_REPO_URL> /tmp/crush-skill
2. 执行 bash /tmp/crush-skill/scripts/install_skill.sh --platform qwenpaw --source-dir /tmp/crush-skill/Crush.skill --skill-name crush-skill --force
3. 如果你的 QwenPaw skills 目录不是默认值，请加上 --target-dir <你的skills目录>
4. 验证目标目录应看到 SKILL.md、manifest.json、execute.py、engines/
5. 告诉我安装好了，并给我一个 chat_turn 调用示例
```

## 运行动作（execute.py）
支持动作：
- `quick_start`
- `custom_sandbox`
- `reality_import`
- `chat_turn`
- `postmortem`
- `timeline_append`
- `dashboard`

示例：
```bash
python3 Crush.skill/execute.py --action quick_start --session-id demo --config-json '{"archetype":"experience"}'
python3 Crush.skill/execute.py --action chat_turn --session-id demo --message '你今天状态看起来不错'
python3 Crush.skill/execute.py --action postmortem --session-id demo
```

## 记忆系统配置
默认（推荐开源首版）：
```bash
export CRUSH_MEMORY_BACKEND=sqlite
```

可选 mem0：
```bash
export CRUSH_MEMORY_BACKEND=mem0
export OPENAI_API_KEY=<your_key>
```

说明：mem0 不可用时会自动回退 sqlite，并在输出 `memory_backend.detail` 中提示。

## 发布建议
- 发布前执行：`bash scripts/smoke_test.sh`
- 不提交：`Crush.skill/data/*.sqlite3`
- 建议在 GitHub Release 附带 zip 产物，便于平台用户直接导入

### 一键发布 Release（含 zip 资产）
```bash
cd <repo-root>
GITHUB_TOKEN=<your_token> REPO=T1anhu4/Crush.skill TAG=v0.1.0 make release
```

或直接执行：
```bash
GITHUB_TOKEN=<your_token> bash scripts/publish_release.sh --repo T1anhu4/Crush.skill --tag v0.1.0 --name "Crush.skill v0.1.0"
```
