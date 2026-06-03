# Crush.skill Architecture

## 1. Core Principle
- Rule Engine 负责计算关系状态、边界、防御和关系惯性
- Import Engine 负责把真实聊天记录蒸馏成“说话指纹”和关系上下文
- Pragmatics Engine 负责识别梗、潜台词、软拒绝、测试与边界
- LLM/宿主 Agent 负责人格化演绎，但必须隐藏内部 JSON 和分数

## 2. Modules
- `engines/archetype_engine.py`: 五类关系原型与初始参数
- `engines/state_engine.py`: 动态状态机更新
- `engines/defense_engine.py`: 防御触发机制
- `engines/memory_engine.py`: 持久记忆与检索
- `engines/chat_import.py`: 聊天记录解析、说话指纹、内部梗、边界短语提取
- `engines/pragmatics_engine.py`: 中文网络口语/关系潜台词识别
- `engines/persona_engine.py`: 5 层人格模型与隐藏 runtime prompt 生成
- `engines/dialogue_analyzer.py`: 本地/LLM 对话分析
- `engines/reality_import_engine.py`: 现实文本人格重建
- `engines/replay_engine.py`: Relationship Combat Replay / Post-Mortem

## 3. Memory Design (for context-limit safety)
默认采用四层记忆：
1. Persona Memory：导入后保存完整 5 层人格、口头禅、梗、边界、共同经历
2. Episode Memory：SQLite 保存真实导入聊天、用户消息、NPC 回复
3. State Memory：状态历史、事件时间线、关系阶段变化
4. Summary Memory：自动更新 `summary`，用于压缩上下文

检索方式：
- 本地混合检索（关键词重叠 + 哈希向量余弦）
- 保证无外部依赖可运行

可选增强：
- 设置 `CRUSH_MEMORY_BACKEND=mem0` 启用 mem0 语义记忆桥接（若环境已安装并可用）
- 即使启用 mem0，SQLite 仍是 source-of-truth，避免外部服务失效导致记忆丢失

## 4. Why not force external vector DB
- 外部向量库会增加部署复杂度和失败点
- 开源 skill 应先保证“单机即用”
- 对多数导入聊天来说，Persona Memory + Episode Memory + Summary 已经能解决大部分上下文遗忘
- 需要团队级、多用户、大规模语义检索时，再升级到 Chroma/PGVector/Milvus/mem0

## 5. Runtime Contract
`execute.py` 支持动作：
- `quick_start`
- `custom_sandbox`
- `reality_import`
- `chat_import`
- `chat_turn`
- `postmortem`
- `timeline_append`
- `dashboard`
- `list_sessions`
- `delete_session`
- `let_go`
- `configure_llm`

统一输出 JSON，便于 OpenClaw/QwenPaw/Claude Code 编排。

对用户可见的聊天体验必须遵循：
- `/chat` 的 `runtime_prompt` 是隐藏系统提示，不直接展示
- `state`、`delta`、`analysis`、`memory_context` 默认隐藏
- 用户只看到 NPC 用 persona 口吻发出的自然回复
- 如宿主 Agent 支持工具链，生成 NPC 回复后用 `--npc-reply` 写回记忆
