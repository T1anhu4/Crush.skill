#!/usr/bin/env python3
"""Validate README transition contracts using only visible Markdown/HTML."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = (
    "docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md",
    "docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md",
)
COMMANDS = ("/start-crush", "/custom-crush", "/import-chats", "/crush-distill", "/chat", "/crush-dashboard", "/crush-postmortem", "/list-crushes", "/let-go", "/crush-llm")
ACTIONS = ("quick_start", "custom_sandbox", "chat_import", "distillation_report", "chat_turn", "record_reply", "proactive_prompt", "dashboard", "postmortem", "list_sessions", "delete_session", "let_go", "configure_llm")
PERSONAS = ("emotional", "security", "experience", "value", "passive")
VERSIONS = ("v2.4.3", "v2.4.4", "v2.4.5", "v2.4.6", "v2.4.7", "v2.4.9", "v2.4.12", "v2.4.13", "v2.4.14", "v2.4.15")

CONTRACTS = {
    "README.md": {
        "minimum_lines": 323,
        "markers": ("Crush.skill 是一台关系飞行模拟器", "许多角色聊天主要围绕当前对话生成下一句", "## 为什么做这个", "## 当前可用，以及正在构建", "## 为什么普通 AI 聊天还是“不像人”", "## v3 Living Mind：正在构建", "## 一起把它做成真的", "## 一分钟上手", "## WeFlow 微信 JSON 导入", "## Skill Slash Commands", "## 致所有人", "项目不宣称角色具有真实意识", "而 Ta，就留在这个 commit 里。", "Made with 💙 by T1anhu4", "for everyone learning how to love.", "v2.4.15", "v3 Living Mind", "开发中", "T1anhu4"),
        "headings": ("项目简介", "为什么做这个", "当前可用，以及正在构建", "为什么普通 AI 聊天还是“不像人”", "v3 Living Mind：正在构建", "项目定位", "一分钟上手", "WeFlow 微信 JSON 导入", "运行效果", "它能做什么", "技术架构", "安装到 Agent", "Skill Slash Commands", "预设人格", "一起把它做成真的", "版本摘要", "Star History", "伦理边界", "License", "致所有人"),
        "assets": ("assets/readme-hero-zh.svg", "assets/readme-cli-demo.svg", "assets/architecture-zh.svg"),
        "preserved_markers": ("curl -fsSL https://raw.githubusercontent.com/T1anhu4/Crush-skill/2.4/scripts/install_cli.sh | bash", "crush", "crush import weflow", "/import-weflow", "隐私边界：默认导入是 safe 模式", "现有 Agent Skill", "独立 CLI", "WeFlow 微信导入", "本地 SQLite 记忆", "时间线主动消息", "关系读秒", "复盘", "git clone https://github.com/T1anhu4/Crush-skill", "install_skill.sh", "ls ~/.claude/skills/crush-skill/", *COMMANDS, *ACTIONS, *PERSONAS, *VERSIONS, "Star History", "不鼓励伤害性拉扯", "不把“拜金/养鱼/慢热/喜欢你”变成单句武断标签", "不建议在未经同意的情况下导入他人的私密聊天记录", "当你学会该学的东西，可以用 `/let-go` 删除会话并放下", "本项目采用 MIT License", "而 Ta，就留在这个 commit 里。", "Made with 💙 by", "for everyone learning how to love."),
    },
    "README_EN.md": {
        "minimum_lines": 318,
        "markers": ("Crush.skill is a relationship flight simulator", "## Why This Exists", "## Available Now, Building Next", "## Why Ordinary AI Chat Still Feels Fake", "## v3 Living Mind: In Development", "## Help Make It Real", "## One-Minute Start", "## WeFlow WeChat JSON Import", "## Skill Slash Commands", "## For Everyone Like The Author", "v2.4.15", "v3 Living Mind", "In development", "T1anhu4"),
        "headings": ("One Sentence", "Why This Exists", "Available Now, Building Next", "Why Ordinary AI Chat Still Feels Fake", "v3 Living Mind: In Development", "Product Positioning", "One-Minute Start", "WeFlow WeChat JSON Import", "Demo", "What It Does", "Architecture", "Install As An Agent Skill", "Skill Slash Commands", "Persona Presets", "Help Make It Real", "Version Summary", "Ethics", "License", "For Everyone Like The Author"),
        "assets": ("assets/readme-hero-en.svg", "assets/readme-cli-demo.svg", "assets/architecture-en.svg"),
        "preserved_markers": ("curl -fsSL https://raw.githubusercontent.com/T1anhu4/Crush-skill/2.4/scripts/install_cli.sh | bash", "crush", "crush import weflow", "/import-weflow", "Privacy boundary", "Agent Skill", "Standalone CLI", "WeFlow", "SQLite", "timeline", "relationship countdown", "postmortem", "git clone https://github.com/T1anhu4/Crush-skill", "install_skill.sh", "ls ~/.claude/skills/crush-skill/", *COMMANDS, *ACTIONS, *PERSONAS, *VERSIONS, "Star History", "Do not encourage", "Do not turn", "Do not recommend importing", "MIT License", "As for Ta, they stay in this commit.", "Made with 💙", "by someone who's been there."),
    },
}

def strip_fences(text: str) -> tuple[str, list[str]]:
    visible, errors, fence = [], [], None
    for line in text.splitlines():
        opening = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence is None:
            if opening: fence = (opening.group(1)[0], len(opening.group(1)))
            else: visible.append(line)
            continue
        char, size = fence
        if re.match(rf"^\s*{re.escape(char)}{{{size},}}\s*$", line): fence = None
    if fence is not None: errors.append("unclosed fenced code block at EOF")
    return "\n".join(visible), errors

def remove_comments(text: str) -> tuple[str, list[str]]:
    errors = []
    if text.count("<!--") > text.count("-->"): errors.append("unclosed HTML comment at EOF")
    return re.sub(r"<!--[\s\S]*?-->", "", text), errors

def visible_content(text: str) -> tuple[str, list[str]]:
    without_fences, errors = strip_fences(text)
    without_comments, comment_errors = remove_comments(without_fences)
    return without_comments, errors + comment_errors

def check_html(text: str, path: Path) -> list[str]:
    stack, errors = [], []
    tags = re.compile(r"</?(p|div|details|summary|a|em|strong)\b[^>]*>", re.I)
    for token in tags.finditer(text):
        tag = token.group(1).lower()
        if token.group(0).startswith("</"):
            if not stack: errors.append(f"{path}: HTML close </{tag}> has no open tag")
            elif stack[-1] != tag:
                errors.append(f"{path}: HTML close </{tag}> mismatches <{stack[-1]}>")
                stack.pop()
            else: stack.pop()
        else: stack.append(tag)
    errors.extend(f"{path}: HTML <{tag}> is not closed" for tag in stack)
    return errors

def check_urls(text: str, path: Path) -> list[str]:
    errors = []
    urls = re.findall(r"(?:https?://[^\s)\"'<>]+|git@github\.com:[^\s)\"'<>]+)", text, re.I)
    for original in urls:
        url = unquote(original)
        lower = url.lower()
        if any(word in lower for word in ("crush.skill", "founder_origin", "private_origin_story", "real_person_source")):
            errors.append(f"{path}: forbidden legacy URL: {original}")
        parsed = urlparse(url.replace("git@github.com:", "ssh://git@github.com/"))
        if parsed.hostname and parsed.hostname.lower() == "github.com" and parsed.path.lower().startswith("/t1anhu4/"):
            repo = parsed.path.split("/")[2].removesuffix(".git")
            if repo != "Crush-skill": errors.append(f"{path}: non-canonical repository URL: {original}")
        if parsed.hostname and parsed.hostname.lower() == "raw.githubusercontent.com":
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2 and parts[:2] != ["T1anhu4", "Crush-skill"]:
                errors.append(f"{path}: non-canonical raw URL: {original}")
        if parsed.hostname and parsed.hostname.lower() in ("api.star-history.com", "www.star-history.com"):
            query = parse_qs(parsed.query)
            if query.get("repos", [""])[0] != "T1anhu4/Crush-skill": errors.append(f"{path}: non-canonical Star History URL: {original}")
    return errors

def check(path: Path) -> list[str]:
    contract = CONTRACTS.get(path.name)
    if contract is None: return [f"{path}: unsupported README filename"]
    try: raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc: return [f"{path}: unable to read: {exc}"]
    errors = []
    if len(raw.splitlines()) < contract["minimum_lines"]: errors.append(f"{path}: too short")
    visible, parser_errors = visible_content(raw)
    errors.extend(f"{path}: {error}" for error in parser_errors)
    plain = re.sub(r"<[^>]+>", "", visible)
    preserved_source, comment_errors = remove_comments(raw)
    errors.extend(f"{path}: {error}" for error in comment_errors)
    for marker in contract["markers"]:
        if marker not in visible and marker not in plain: errors.append(f"{path}: missing visible marker: {marker}")
    for marker in contract["preserved_markers"]:
        if marker not in visible and marker not in plain and marker not in preserved_source:
            errors.append(f"{path}: missing preserved marker: {marker}")
    headings = [m.group(1).strip().rstrip("#").strip() for m in re.finditer(r"^#{1,6}\s+(.+)$", visible, re.M)]
    indexes = []
    for heading in contract["headings"]:
        if heading not in headings: errors.append(f"{path}: missing heading: {heading}")
        else: indexes.append(headings.index(heading))
    if indexes != sorted(indexes): errors.append(f"{path}: headings are out of order")
    errors.extend(check_html(visible, path))
    images = re.findall(r"<img\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>", visible, re.I)
    for asset in contract["assets"]:
        if images.count(asset) != 1: errors.append(f"{path}: image {asset} must appear exactly once")
        elif not (ROOT / asset).is_file(): errors.append(f"{path}: missing local asset: {asset}")
    links = re.findall(r"\[[^]]+\]\(([^)\s]+)\)", visible)
    for target in DOCS:
        if target not in links: errors.append(f"{path}: missing visible Markdown link: {target}")
        elif not (ROOT / target).is_file(): errors.append(f"{path}: missing local document: {target}")
    if images.count("assets/readme-cli-demo.svg") != 1: errors.append(f"{path}: CLI demo asset must appear exactly once")
    errors.extend(check_urls(raw, path))
    return errors

def main(argv: list[str]) -> int:
    paths = [Path(item) for item in argv] or [Path("README.md"), Path("README_EN.md")]
    errors = [error for path in paths for error in check(path)]
    if errors: print("\n".join(errors)); return 1
    print("README transition contract passed"); return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
