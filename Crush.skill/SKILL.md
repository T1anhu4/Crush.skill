---
name: crush_skill
description: 关系人格模拟引擎技能。用于构建长期人格、动态状态机、现实导入、关系战斗回放和复盘诊断。适用于 OpenClaw/QwenPaw 通过 execute.py 执行 quick_start/custom_sandbox/reality_import/chat_turn/postmortem 等动作。
---

# Crush.skill

## 用途
把“聊天”升级为“人格关系模拟系统”：
- 规则引擎负责算状态
- LLM 负责演角色

## 执行入口
```bash
python3 execute.py --action quick_start --session-id demo --config-json '{"archetype":"experience"}'
```

## 动作
- `quick_start`
- `custom_sandbox`
- `reality_import`
- `chat_turn`
- `postmortem`
- `timeline_append`
- `dashboard`

## 关键环境变量
- `CRUSH_MEMORY_BACKEND=sqlite|mem0`（默认 `sqlite`）
- `OPENAI_API_KEY`（仅 mem0 模式可能需要）

## 输出约定
所有动作输出 JSON：
- `success=true`：执行成功
- `state/delta/dashboard`：状态机主输出
- `runtime_prompt`：可直接喂给 LLM 的角色运行提示
- `report/markdown`：复盘输出（postmortem）
