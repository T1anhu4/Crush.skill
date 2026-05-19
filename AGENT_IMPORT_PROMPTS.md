# Agent One-Sentence Import Prompts

将 `<GITHUB_REPO_URL>` 替换成你的仓库地址，例如：
`https://github.com/<your-org>/crush-xiehou-skill.git`

## Claude Code

```text
帮我安装 crush-xiehou-skill 这个 Claude Code skill。请按下面步骤做：
1. 确保 ~/.claude/skills/ 目录存在（不存在就创建）
2. 执行 git clone <GITHUB_REPO_URL> /tmp/crush-xiehou-skill
3. 执行 bash /tmp/crush-xiehou-skill/scripts/install_skill.sh --platform claude --source-dir /tmp/crush-xiehou-skill/Crush邂逅.skill --skill-name crush-xiehou-skill --force
4. 验证：ls ~/.claude/skills/crush-xiehou-skill/ 应该看到 SKILL.md、manifest.json、execute.py、engines/
5. 告诉我安装好了，之后我说“帮我做一次关系复盘”之类的话就会触发这个 skill
```

## OpenClaw

```text
帮我安装 crush-xiehou-skill 到 OpenClaw。请按下面步骤做：
1. 执行 git clone <GITHUB_REPO_URL> /tmp/crush-xiehou-skill
2. 执行 bash /tmp/crush-xiehou-skill/scripts/install_skill.sh --platform openclaw --source-dir /tmp/crush-xiehou-skill/Crush邂逅.skill --skill-name crush-xiehou-skill --force
3. 验证安装目录（默认 ~/.openclaw/skills/crush-xiehou-skill/，若你的 OpenClaw 有自定义目录就按实际目录验证），应看到 SKILL.md、manifest.json、execute.py、engines/
4. 告诉我安装完成并给我一个 quick_start 的调用示例
```

## QwenPaw

```text
帮我安装 crush-xiehou-skill 到 QwenPaw。请按下面步骤做：
1. 执行 git clone <GITHUB_REPO_URL> /tmp/crush-xiehou-skill
2. 执行 bash /tmp/crush-xiehou-skill/scripts/install_skill.sh --platform qwenpaw --source-dir /tmp/crush-xiehou-skill/Crush邂逅.skill --skill-name crush-xiehou-skill --force
3. 如果你的 QwenPaw skills 目录不是默认值，请加上 --target-dir <你的skills目录>
4. 验证目标目录应看到 SKILL.md、manifest.json、execute.py、engines/
5. 告诉我安装好了，并给我一个 chat_turn 调用示例
```

## 统一脚本说明

安装脚本：`scripts/install_skill.sh`

支持参数：
- `--platform claude|openclaw|qwenpaw`
- `--target-dir <path>`
- `--skill-name <name>`
- `--force`
- `--mode copy|symlink`
- `--repo-url <git-url>`（让脚本自己 clone 后安装）
