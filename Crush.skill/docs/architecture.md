# Crush.skill Architecture

## 1. Core Principle
- Rule Engine 负责计算关系状态
- LLM 负责人格化演绎

## 2. Modules
- `engines/archetype_engine.py`: 五类关系原型与初始参数
- `engines/state_engine.py`: 动态状态机更新
- `engines/defense_engine.py`: 防御触发机制
- `engines/memory_engine.py`: 持久记忆与检索
- `engines/reality_import_engine.py`: 现实文本人格重建
- `engines/replay_engine.py`: Relationship Combat Replay / Post-Mortem

## 3. Memory Design (for context-limit safety)
默认采用三层记忆：
1. 短期记忆：最近对话片段
2. 长期记忆：SQLite 持久化事件/状态历史
3. 摘要记忆：自动更新 `summary`，用于压缩上下文

检索方式：
- 本地混合检索（关键词重叠 + 哈希向量余弦）
- 保证无外部依赖可运行

可选增强：
- 设置 `CRUSH_MEMORY_BACKEND=mem0` 启用 mem0 语义记忆桥接（若环境已安装并可用）
- 即使启用 mem0，SQLite 仍是 source-of-truth，避免外部服务失效导致记忆丢失

## 4. Why not force external vector DB in V1
- 外部向量库会增加部署复杂度和失败点
- 开源首版更适合“单机即用”
- 先保证稳定人格连续性，再按需要升级到 Chroma/PGVector/Milvus

## 5. Runtime Contract
`execute.py` 支持动作：
- `quick_start`
- `custom_sandbox`
- `reality_import`
- `chat_turn`
- `postmortem`
- `timeline_append`
- `dashboard`

统一输出 JSON，便于 OpenClaw/QwenPaw 编排。
