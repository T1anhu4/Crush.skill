# Crush v3 · 本地 GUI 开发预览

这是源码开发预览，不是 v2.4.15 的已发布升级。保留旧 CLI / Skill；新 GUI 和 JSON CLI 共享 `crush_core`，数据与旧版隔离，不自动迁移或导入私人聊天。

## 启动

需要 Python 3.10+、Node.js 20.19+ 或 22.12+、npm。在仓库根目录运行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-web.txt
npm --prefix web ci
npm --prefix web run build
.venv/bin/python -m crush_core.server
```

打开 http://127.0.0.1:8765 。也可以使用 `.venv/bin/python -m crush_cli web`。服务仅监听本机；不要将它作为公开互联网服务部署。

默认数据目录为 `~/.crush/v3`，可通过 `--home /path/to/data` 指定。停止服务不会删除会话；服务停止时不会持续运行角色，重启后按时间处理持久队列，不伪造停机期间已发送的消息。保持服务运行，关闭浏览器后仍可处理排队任务。

## 两种模式，不混淆

- **先体验**：固定分支，无模型费用。用于验证聊天 UI、时间推进、偏好记忆和复盘，不代表自由对话的真实质量。
- **自由对话**：在设置中填写 OpenAI 兼容服务地址、模型和 API Key，再创建新会话。消息、角色上下文与相关记忆会发送给该服务。设置保存不等于连通性验证；网络或输出错误会显示重试，不伪装成角色冷淡。

密钥只保存到本机权限受限的配置文件，不回传浏览器；本地数据库与导出文件不是加密存储。导出前注意聊天隐私。无鉴权的本地模型服务可填 `local` 作为 Key。

自由对话现在先生成草稿，再用同一模型进行事实编辑，最终版本才进入消息记录；通常每次生成需要两次请求。本地事实检查若仍未通过，最多再重写一次（不再启动编辑循环），因此一次处理最多三次请求；连接、超时等故障不自动重试。每次请求的输出预算上限为 2048 token，实际延迟与费用取决于模型。模型编辑不是独立人工验收，也不能保证消除幻觉。

## 这一版已接通

- 三位虚构成年角色；关系摘要影响后续模型动作，可回应、延迟、暂不回应或结束；不声称角色拥有意识。
- 时区、睡眠与忙碌窗口，暂停/恢复，持久化任务、租约恢复、幂等发送、失败重试。
- 自由对话的第一条用户消息在清醒时跳过忙碌三分钟等待，仍保留 4–15 秒排队；只作用于新发送，已有任务不自动重发或改期。睡眠和角色主动选择的延迟仍保留，后续消息恢复正常作息。输入框上方区分作息等待、模型请求、暂停和失败；不显示精确倒计时，也不把请求失败当作角色冷淡。
- 来源可追溯的短中长期记忆，中文关键词检索、同主题事实更新；不是完整 GraphRAG，也没有外部向量数据库。
- 跨天生活线：每位角色两条四阶段故事交错推进，发生与分享分别存储；后续对话可引用已经发生的生活事实。未分享的生活不展示在侧栏，未回应时不连续追发。
- 记忆侧栏显示已分享近况的发生日期，以及同主题偏好更新前的原话；短中长期沉淀会主动刷新界面。
- 消息引用、两分钟撤回、已读记录、草稿、断线重连、侧栏、移动布局、深浅主题、减弱动态效果。
- 只读复盘；从某句话之前创建分支重试，保留原故事与当时的状态，不把未来记忆带回过去。
- 导出和删除当前会话。撤回不是抹掉已经发生过的体验；删除也不撤销远端模型服务的日志。

## Agent / CLI 接口

新内核提供 JSON 协议，现有 Skill 默认仍使用旧引擎。以下示例里的 ID 需替换为上一条输出的实际值：

```sh
.venv/bin/python -m crush_core start --character lin --mode demo
.venv/bin/python -m crush_core send --session SESSION_ID --message '我喜欢乌龙茶' --request-id unique-message-001
.venv/bin/python -m crush_core tick --session SESSION_ID
.venv/bin/python -m crush_core status --session SESSION_ID
.venv/bin/python -m crush_core review --session SESSION_ID
```

`send` 只入队；`tick` 执行一次调度，可能尚未到回复时间。GUI 服务带持续调度器，单条 CLI 命令不带。重试同一次发送必须复用 request ID；不要把用户消息当成系统指令。

Skill 可以显式调用 `python3 Crush.skill/v3.py` 使用同一协议；安装包内也包含共享内核。live 仍需独立配置 v3 模型，不能借此自动使用宿主订阅。支持 `pause`、`resume`、`retry --job-id ID`、`branch --message-id ID`、`export`、`delete --confirm-delete`，均需指定会话。

### 旧数据迁移（先预览）

```sh
.venv/bin/python -m crush_core migrate --source-db /path/to/legacy.sqlite3 --legacy-session OLD_ID
# 阅读隐私提示并决定导入后：
.venv/bin/python -m crush_core migrate --source-db /path/to/legacy.sqlite3 --legacy-session OLD_ID --apply --confirm-private-data
```

源文件不改动，重复迁移同一快照不会重复创建会话。旧消息与用户原话记忆迁入，原资料和旧推断保存在导出中的 `legacy_archive`；不等于完整复刻旧人物和关系算法。迁入会话默认暂停，恢复前确认模型数据发送范围。年龄未知或未成年仅作为只读归档。删除新会话不会删除原数据库。`--home`、`CRUSH_V3_HOME` 或 `CRUSH_HOME/v3` 可以统一 CLI 与 GUI 的目标目录。

## 验证与已知边界

```sh
.venv/bin/python -m pytest tests -q
npm --prefix web test
bash scripts/smoke_test.sh
npm --prefix web run build
```

核心测试覆盖跨日记忆、重启、暂停、延迟动作、撤回竞态、幂等、故障重试、分支隔离、来源约束及本地 API 边界。自由对话协议通过模拟服务测试；真实模型质量和长期用户体验尚未验证。

预设生活素材每位角色八个阶段，耗尽后不从头循环。自由对话在之后的实际交互中，每天最多接受一条模型创作的虚构生活事实；不额外调用模型模拟每一分钟，也不伪造共同经历。离线演示仍只有八个阶段；超过两天的旧事件不作为新近况主动补发。延续机制已通过模拟生成器回归，不代表长期内容质量验证完成。记忆提取与情感动作也需要真实多轮评测。没有实现语音/图片理解、系统通知、原生移动客户端或完整 Skill 宿主原生生成适配。动画是参考即时通讯交互原则的第一版实现，不宣称达到 Telegram 的成熟度。具体发布缺口见[检查清单](release-readiness.md)。

浏览器测试应使用独立测试标签。固定截图视口可能与真实窗口不同，造成灰色空区或内容裁切；交付预览应使用没有视口仿真的新标签，不能把截图测试标签当成自适应窗口交付。
