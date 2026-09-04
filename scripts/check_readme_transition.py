#!/usr/bin/env python3
"""Validate the public README transition contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


COMMON_FORBIDDEN = (
    "github.com/T1anhu4/Crush.skill",
    "raw.githubusercontent.com/T1anhu4/Crush.skill",
    "repos=T1anhu4/Crush.skill",
    "repos=T1anhu4%2FCrush.skill",
    "founder_origin",
    "private_origin_story",
    "real_person_source",
)

CONTRACTS = {
    "README.md": {
        "lines": 320,
        "markers": (
            "Crush.skill 是一台关系飞行模拟器",
            "## 为什么做这个",
            "## 当前可用，以及正在构建",
            "## 为什么普通 AI 聊天还是“不像人”",
            "## v3 Living Mind：正在构建",
            "## 一起把它做成真的",
            "## 一分钟上手",
            "## WeFlow 微信 JSON 导入",
            "## Skill Slash Commands",
            "## 致所有人",
            "assets/readme-hero-zh.svg",
            "assets/readme-cli-demo.svg",
            "assets/architecture-zh.svg",
            "docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md",
            "docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md",
            "v2.4.15",
            "v3 Living Mind",
            "开发中",
            "T1anhu4",
        ),
    },
    "README_EN.md": {
        "lines": 315,
        "markers": (
            "Crush.skill is a relationship flight simulator",
            "## Why This Exists",
            "## Available Now, Building Next",
            "## Why Ordinary AI Chat Still Feels Fake",
            "## v3 Living Mind: In Development",
            "## Help Make It Real",
            "## One-Minute Start",
            "## WeFlow WeChat JSON Import",
            "## Skill Slash Commands",
            "## For Everyone Like The Author",
            "assets/readme-hero-en.svg",
            "assets/readme-cli-demo-en.svg",
            "assets/architecture-en.svg",
            "docs/superpowers/specs/2026-09-04-crush-v3-living-mind-design.md",
            "docs/superpowers/plans/2026-09-04-crush-v3-living-mind.md",
            "v2.4.15",
            "v3 Living Mind",
            "In development",
            "T1anhu4",
        ),
    },
}


def check(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    name = path.name
    contract = CONTRACTS.get(name)
    if contract is None:
        errors.append(f"{path}: unsupported README filename")
        return errors
    lines = text.splitlines()
    if len(lines) < contract["lines"]:
        errors.append(f"{path}: expected at least {contract['lines']} lines, found {len(lines)}")
    for marker in contract["markers"]:
        if marker not in text:
            errors.append(f"{path}: missing required marker: {marker}")
    for marker in COMMON_FORBIDDEN:
        if marker in text:
            errors.append(f"{path}: forbidden legacy marker: {marker}")
    if text.count("```") % 2:
        errors.append(f"{path}: unpaired triple-backtick fence")
    for tag in ("p", "div", "details", "summary"):
        opens = len(re.findall(rf"<{tag}(?:\s[^>]*)?>", text, re.I))
        closes = len(re.findall(rf"</{tag}\s*>", text, re.I))
        if opens != closes:
            errors.append(f"{path}: unbalanced HTML <{tag}> tags ({opens} open, {closes} close)")
    cli_pattern = r"assets/readme-cli-demo(?:-[a-z]+)?\.svg"
    if len(re.findall(cli_pattern, text)) != 1:
        errors.append(f"{path}: CLI demo asset must be referenced exactly once")
    for url in re.findall(r"https://github\.com/T1anhu4/[^\s)\"'<>]+", text):
        if not url.startswith("https://github.com/T1anhu4/Crush-skill"):
            errors.append(f"{path}: non-canonical repository link: {url}")
    return errors


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv] if argv else [Path("README.md"), Path("README_EN.md")]
    errors = [error for path in paths for error in check(path)]
    if errors:
        print("\n".join(errors))
        return 1
    print("README transition contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
