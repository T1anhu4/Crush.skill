#!/usr/bin/env python3
"""Validate the public README transition contract without trusting hidden text."""
from __future__ import annotations
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN = ("github.com/t1anhu4/crush.skill", "raw.githubusercontent.com/t1anhu4/crush.skill", "repos=t1anhu4/crush.skill", "repos=t1anhu4%2fcrush.skill", "founder_origin", "private_origin_story", "real_person_source")
CONTRACTS = {
    "README.md": {"minimum_lines": 323, "markers": ("Crush.skill 是一台关系飞行模拟器", "普通角色聊天主要围绕当前对话生成下一句", "## 为什么做这个", "## 当前可用，以及正在构建", "## 为什么普通 AI 聊天还是“不像人”", "## v3 Living Mind：正在构建", "## 一起把它做成真的", "## 一分钟上手", "## WeFlow 微信 JSON 导入", "## Skill Slash Commands", "## 致所有人", "项目不宣称角色具有真实意识", "而 Ta，就留在这个 commit 里。", "Made with 💙 by T1anhu4", "for everyone learning how to love.", "v2.4.15", "v3 Living Mind", "开发中", "T1anhu4"), "headings": ("项目简介", "为什么做这个", "当前可用，以及正在构建", "为什么普通 AI 聊天还是“不像人”", "v3 Living Mind：正在构建", "项目定位", "一分钟上手", "WeFlow 微信 JSON 导入", "运行效果", "它能做什么", "技术架构", "安装到 Agent", "Skill Slash Commands", "预设人格", "一起把它做成真的", "版本摘要", "Star History", "伦理边界", "License", "致所有人"), "assets": ("assets/readme-hero-zh.svg", "assets/readme-cli-demo.svg", "assets/architecture-zh.svg")},
    "README_EN.md": {"minimum_lines": 318, "markers": ("Crush.skill is a relationship flight simulator", "## Why This Exists", "## Available Now, Building Next", "## Why Ordinary AI Chat Still Feels Fake", "## v3 Living Mind: In Development", "## Help Make It Real", "## One-Minute Start", "## WeFlow WeChat JSON Import", "## Skill Slash Commands", "## For Everyone Like The Author", "v2.4.15", "v3 Living Mind", "In development", "T1anhu4"), "headings": ("One Sentence", "Why This Exists", "Available Now, Building Next", "Why Ordinary AI Chat Still Feels Fake", "v3 Living Mind: In Development", "Product Positioning", "One-Minute Start", "WeFlow WeChat JSON Import", "Demo", "What It Does", "Architecture", "Install As An Agent Skill", "Skill Slash Commands", "Persona Presets", "Help Make It Real", "Version Summary", "Ethics", "License", "For Everyone Like The Author"), "assets": ("assets/readme-hero-en.svg", "assets/readme-cli-demo.svg", "assets/architecture-en.svg")},
}

def visible_content(text: str) -> tuple[str, list[str]]:
    out, errors, active = [], [], None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if active is None:
            if match: active = (match.group(1)[0], len(match.group(1)))
            else: out.append(line)
            continue
        char, length = active
        if re.match(rf"^\s*{re.escape(char)}{{{length},}}\s*$", line): active = None
    if active is not None: errors.append("unclosed fenced code block at EOF")
    return re.sub(r"<!--[\s\S]*?-->", "", "\n".join(out)), errors

def check_html(text: str, path: Path) -> list[str]:
    errors, stack = [], []
    token = re.compile(r"</?(p|div|details|summary)\b[^>]*>", re.I)
    for index, match in enumerate(token.finditer(text), 1):
        tag = match.group(1).lower()
        if match.group(0).startswith("</"):
            if not stack: errors.append(f"{path}: HTML close </{tag}> has no open tag")
            elif stack[-1][0] != tag:
                errors.append(f"{path}: HTML close </{tag}> mismatches <{stack[-1][0]}> (token {index})"); stack.pop()
            else: stack.pop()
        else: stack.append((tag, index))
    errors.extend(f"{path}: HTML <{tag}> opened at token {index} is not closed" for tag, index in stack)
    return errors

def check(path: Path) -> list[str]:
    contract = CONTRACTS.get(path.name)
    if contract is None: return [f"{path}: unsupported README filename"]
    try: raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc: return [f"{path}: unable to read: {exc}"]
    errors = []
    if len(raw.splitlines()) < contract["minimum_lines"]: errors.append(f"{path}: expected at least {contract['minimum_lines']} lines, found {len(raw.splitlines())}")
    visible, fence_errors = visible_content(raw)
    plain_visible = re.sub(r"<[^>]+>", "", visible)
    errors.extend(f"{path}: {error}" for error in fence_errors)
    markers = tuple("许多角色聊天主要围绕当前对话生成下一句" if marker == "普通角色聊天主要围绕当前对话生成下一句" else marker for marker in contract["markers"])
    for marker in markers:
        if marker not in visible and marker not in plain_visible: errors.append(f"{path}: missing visible required marker: {marker}")
    headings = [m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", visible, re.M)]
    positions = []
    for heading in contract["headings"]:
        if heading not in headings: errors.append(f"{path}: missing heading: {heading}")
        else: positions.append((headings.index(heading), heading))
    if positions != sorted(positions): errors.append(f"{path}: headings are out of order")
    errors.extend(f"{path}: forbidden marker: {marker}" for marker in FORBIDDEN if marker in raw.lower())
    errors.extend(check_html(visible, path))
    images = re.findall(r"<img\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>", visible, re.I)
    for asset in contract["assets"]:
        if images.count(asset) != 1: errors.append(f"{path}: <img src=...> must reference {asset} exactly once")
        elif not (ROOT / asset).is_file(): errors.append(f"{path}: missing local asset: {asset}")
    for target in ("docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md", "docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md"):
        links = re.findall(r"\[[^]]+\]\(([^)\s]+)\)", visible)
        if target not in links: errors.append(f"{path}: missing visible Markdown link: {target}")
        elif not (ROOT / target).is_file(): errors.append(f"{path}: missing local document: {target}")
    if images.count("assets/readme-cli-demo.svg") != 1: errors.append(f"{path}: CLI demo asset must be referenced exactly once")
    for url in re.findall(r"(?:https?://[^\s)\"'<>]+|git@github\.com:[^\s)\"'<>]+)", raw, re.I):
        decoded = unquote(url).lower()
        if any(marker in decoded for marker in FORBIDDEN): errors.append(f"{path}: forbidden legacy URL: {url}")
        if "github.com" in decoded:
            parsed = urlparse(decoded.replace("git@github.com:", "ssh://git@github.com/"))
            if parsed.hostname == "github.com" and parsed.path.startswith("/t1anhu4/"):
                repo = parsed.path.split("/")[2].removesuffix(".git") if len(parsed.path.split("/")) > 2 else ""
                if repo and repo != "crush-skill": errors.append(f"{path}: non-canonical repository URL: {url}")
    return errors

def main(argv: list[str]) -> int:
    errors = [error for path in (map(Path, argv) if argv else (Path("README.md"), Path("README_EN.md"))) for error in check(path)]
    if errors: print("\n".join(errors)); return 1
    print("README transition contract passed"); return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
