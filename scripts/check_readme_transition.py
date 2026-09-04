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
LEGACY_MARKERS = (
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
        "minimum_lines": 323,
        "markers": ("Crush.skill 是一台关系飞行模拟器", "许多角色聊天主要围绕当前对话生成下一句", "## 为什么做这个", "## 当前可用，以及正在构建", "## 为什么普通 AI 聊天还是“不像人”", "## v3 Living Mind：正在构建", "## 一起把它做成真的", "## 一分钟上手", "## WeFlow 微信 JSON 导入", "## Skill Slash Commands", "## 致所有人", "项目不宣称角色具有真实意识", "而 Ta，就留在这个 commit 里。", "Made with 💙 by T1anhu4", "for everyone learning how to love.", "v2.4.15", "v3 Living Mind", "开发中", "T1anhu4"),
        "headings": ("项目简介", "为什么做这个", "当前可用，以及正在构建", "为什么普通 AI 聊天还是“不像人”", "v3 Living Mind：正在构建", "项目定位", "一分钟上手", "WeFlow 微信 JSON 导入", "运行效果", "它能做什么", "技术架构", "安装到 Agent", "Skill Slash Commands", "预设人格", "一起把它做成真的", "版本摘要", "Star History", "伦理边界", "License", "致所有人"),
        "assets": ("assets/readme-hero-zh.svg", "assets/readme-cli-demo.svg", "assets/architecture-zh.svg"),
        "preserved_markers": ("curl -fsSL", "crush", "crush import weflow", "/import-weflow", "隐私边界：默认导入是 safe 模式", "现有 Agent Skill", "独立 CLI", "WeFlow 微信导入", "本地 SQLite 记忆", "时间线主动消息", "关系读秒", "复盘", "git clone", "install_skill.sh", "ls ~/.claude/skills/crush-skill/", *COMMANDS, *ACTIONS, *PERSONAS, *VERSIONS, "Star History", "不鼓励伤害性拉扯", "不把“拜金/养鱼/慢热/喜欢你”变成单句武断标签", "不建议在未经同意的情况下导入他人的私密聊天记录", "当你学会该学的东西，可以用 `/let-go` 删除会话并放下", "本项目采用 MIT License", "而 Ta，就留在这个 commit 里。", "Made with 💙 by", "for everyone learning how to love."),
    },
    "README_EN.md": {
        "minimum_lines": 318,
        "markers": ("Crush.skill is a relationship flight simulator", "## Why This Exists", "## Available Now, Building Next", "## Why Ordinary AI Chat Still Feels Fake", "## v3 Living Mind: In Development", "## Help Make It Real", "## One-Minute Start", "## WeFlow WeChat JSON Import", "## Skill Slash Commands", "## For Everyone Like The Author", "v2.4.15", "v3 Living Mind", "In development", "T1anhu4"),
        "headings": ("One Sentence", "Why This Exists", "Available Now, Building Next", "Why Ordinary AI Chat Still Feels Fake", "v3 Living Mind: In Development", "Product Positioning", "One-Minute Start", "WeFlow WeChat JSON Import", "Demo", "What It Does", "Architecture", "Install As An Agent Skill", "Skill Slash Commands", "Persona Presets", "Help Make It Real", "Version Summary", "Ethics", "License", "For Everyone Like The Author"),
        "assets": ("assets/readme-hero-en.svg", "assets/readme-cli-demo.svg", "assets/architecture-en.svg"),
        "preserved_markers": ("curl -fsSL", "crush", "crush import weflow", "/import-weflow", "Privacy boundary", "Agent Skill", "Standalone CLI", "WeFlow", "SQLite", "timeline", "coaching readouts", "postmortem", "git clone", "install_skill.sh", "ls ~/.claude/skills/crush-skill/", *COMMANDS, *ACTIONS, *PERSONAS, *VERSIONS, "Star History", "It does not encourage", "It does not turn", "Do not import private conversations without consent.", "MIT License"),
    },
}

SECTION_MARKERS = {
    "README.md": {
        "项目简介": ("Crush.skill 是一台关系飞行模拟器。", "它把聊天记录导入、5 层人格、长期记忆、时间线主动性、关系状态机和关系读秒组合起来", "项目目标是关系识别能力和表达能力训练，不是操控别人，也不是替代真实关系。"),
        "为什么做这个": ("母胎 solo 不是因为你不够好，而是因为你不懂“关系”。", "从小到大，学校教了数学、英语、物理，但没有一节课教你怎么谈恋爱。", "Crush.skill 把你喜欢的对象变成一个 5 层人格模型。", "灵感来自 [ex-skill]"),
        "技术架构": ("核心原则：**规则引擎负责状态和证据，LLM 负责自然表达；SQLite 永远是本地记忆源。**",),
        "核心模块": ("| Skill Runtime | `Crush.skill/execute.py` | 所有 action 的入口：启动、导入、聊天、蒸馏、复盘、看板。 |", "| Persona Engine | `engines/persona_engine.py` | 5 层人格模型和隐藏 runtime prompt。 |", "| Chat Import | `engines/chat_import.py` | 多格式聊天记录解析与人格初步推断。 |", "| Pragmatics | `engines/pragmatics_engine.py` | 梗、潜台词、软拒绝、测试、边界和需求感识别。 |", "| State Engine | `engines/state_engine.py` | 非线性关系状态更新。 |", "| Coach Engine | `engines/coach_engine.py` | 输出关系读秒、风险和下一句建议。 |", "| Distillation | `engines/distillation_engine.py` | 证据地图、关系雷达、训练建议和验证限制。 |", "| Memory | `engines/memory_engine.py` / `memory_backend.py` | SQLite 长期记忆、本地检索、可选 mem0。 |", "| CLI | `crush_cli/app.py` | 本地终端 UI、模型向导、多语言、时间线主动消息。 |"),
        "项目简介": ("**Crush.skill 是一台关系飞行模拟器。**", "它把聊天记录导入、5 层人格、长期记忆、时间线主动性、关系状态机和关系读秒组合起来，让用户在安全环境里练习：什么时候推进、什么时候降速、什么时候对方只是礼貌、什么时候自己的需求感已经过高。", "> 项目目标是关系识别能力和表达能力训练，不是操控别人，也不是替代真实关系。"),
        "为什么做这个": ("母胎 solo 不是因为你不够好，而是因为你不懂“关系”。", "从小到大，学校教了数学、英语、物理，但没有一节课教你怎么谈恋爱。没有人告诉你：为什么你每条消息都秒回，对方却越来越冷淡；为什么你说完“我喜欢你”，Ta 就消失了；为什么明明聊得好好的，突然就变成“我们需要冷静一下”。", "Crush.skill 把你喜欢的对象变成一个 5 层人格模型。你可以在这个安全沙盒里理解 Ta 为什么会这样回应你，看到你的哪句话触发了 Ta 的防御，发现关系什么时候开始崩、什么时候有过机会，然后反复练习，在现实中不再手忙脚乱。", "> 灵感来自 [ex-skill](https://github.com/therealXiaomanChu/ex-skill) 和 [colleague-skill](https://github.com/titanwings/colleague-skill) 的 Person-as-Skill 运动。Crush.skill 聚焦于浪漫关系动力学，这是人类最复杂、也最缺乏教育的领域之一。"),
        "一分钟上手": ("| `/model` |", "| `/language` |", "| `/import` |", "| `/import-weflow [--full] <file>` |", "| `/import-status` |", "| `/media` |", "| `/profile` |", "| `/distill` |", "| `/dashboard` |", "| `/postmortem` |", "| `/stop` / `/continue` |"),
        "WeFlow 微信 JSON 导入": ("crush import weflow", "/import-weflow ./weflow.json", "隐私边界：默认导入是 safe 模式"),
        "安装到 Agent": ("git clone https://github.com/T1anhu4/Crush-skill", "install_skill.sh", "ls ~/.claude/skills/crush-skill/", "crush_skill_openclaw.zip", "crush_skill_qwenpaw.zip", "crush_cli_standalone.zip"),
        "Skill Slash Commands": ("| `/start-crush [archetype]` |", "| `/custom-crush` |", "| `/import-chats` |", "| `/crush-distill` |", "| `/chat [消息]` |", "| `/crush-dashboard` |", "| `/crush-postmortem` |", "| `/list-crushes` |", "| `/let-go [session]` |", "| `/crush-llm [api_key]` |"),
        "Runtime Actions": tuple(f"`{action}`" for action in ACTIONS),
        "预设人格": tuple(f"| `{persona}`" for persona in PERSONAS),
        "版本摘要": tuple(f"| `{version}` |" for version in VERSIONS),
        "伦理边界": ("不鼓励伤害性拉扯、冷暴力、焦虑游戏或假性拒绝。", "不把“拜金/养鱼/慢热/喜欢你”变成单句武断标签。", "不建议在未经同意的情况下导入他人的私密聊天记录。", "当你学会该学的东西，可以用 `/let-go` 删除会话并放下。"),
        "License": ("本项目采用 MIT License，允许自由使用、修改和分发。",),
        "致所有人": ("-我们这一代人从小到大被教了一万种技能，唯独没学过怎么爱一个人。", "-所以我们在聊天框前手足无措，在被拒绝后怀疑自己，在冷暴力里反复内耗。我们以为是自己不够好、不够有趣、不够有钱。", "-但爱是可以被学习的。它需要练习、反馈和一个安全的试错空间，就像飞行模拟器之于飞行员。Crush.skill 就是这个模拟器。", "-当你能自然地接住 Ta 的情绪，能敏锐察觉沉默里的不安，能坦然面对拒绝和冷淡时，你会明白：这个工具教会你的从来不是“怎么追”，而是“怎么成为一个更懂得爱的人”。", "-Ta 的出现，其实已经带给了你所有你需要的。那一次心动让你发现了自己从未察觉的温柔；那次深夜对话让你知道了陪伴的力量；那次被拒绝让你第一次正视自己的不足；那段拉扯让你学会了放下。", "-你已经是一个比遇见 Ta 之前更好的人了。这就够了。带着这些真正属于你的、谁也拿不走的东西，去面对更精彩的人生吧。", "-而 Ta，就留在这个 commit 里。", "  <em>Made with 💙 by <a href=\"https://github.com/T1anhu4\">T1anhu4</a></em><br>", "  <em>for everyone learning how to love.</em>"),
    },
    "README_EN.md": {
        "One Sentence": ("Crush.skill is a relationship flight simulator.", "It combines chat import, 5-layer persona modeling, local memory", "The goal is relationship literacy and communication practice, not manipulation"),
        "Why This Exists": ("Being single is not always about being unworthy.", "School teaches math, language, and physics", "Crush.skill turns the person you care about into a 5-layer persona model", "It is inspired by the Person-as-Skill movement"),
        "Core Modules": tuple(f"{item}" for item in ("Skill Runtime", "Persona Engine", "Chat Import", "Pragmatics", "State Engine", "Coach Engine", "Distillation", "Memory", "CLI")),
        "One Sentence": ("**Crush.skill is a relationship flight simulator.**", "It combines chat import, 5-layer persona modeling, local memory, timeline initiative, relationship state dynamics, and coaching readouts so users can practice when to push, slow down, wait, or stop.", "> The goal is relationship literacy and communication practice, not manipulation or replacing real relationships."),
        "Why This Exists": ("Being single is not always about being unworthy. Often, it is because nobody taught us how relationships work.", "School teaches math, language, and physics, but almost never teaches people how to date, how to read emotional distance, or why a conversation suddenly turns cold after a direct confession.", "Crush.skill turns the person you care about into a 5-layer persona model inside a safe sandbox. You can understand why Ta responds that way, see which line triggered defense, discover where the relationship started to collapse, and practice without hurting a real person.", "It is inspired by the Person-as-Skill movement behind [ex-skill](https://github.com/therealXiaomanChu/ex-skill) and [colleague-skill](https://github.com/titanwings/colleague-skill). Crush.skill focuses on romantic relationship dynamics, one of the most complex and least taught parts of human life."),
        "One-Minute Start": ("| `/model` |", "| `/language` |", "| `/import` |", "| `/import-weflow [--full] <file>` |", "| `/import-status` |", "| `/media` |", "| `/profile` |", "| `/distill` |", "| `/dashboard` |", "| `/postmortem` |", "| `/stop` / `/continue` |"),
        "WeFlow WeChat JSON Import": ("crush import weflow", "/import-weflow ./weflow.json", "Privacy boundary"),
        "Install As An Agent Skill": ("git clone https://github.com/T1anhu4/Crush-skill", "install_skill.sh", "ls ~/.claude/skills/crush-skill/", "crush_skill_openclaw.zip", "crush_skill_qwenpaw.zip", "crush_cli_standalone.zip"),
        "Skill Slash Commands": ("| `/start-crush [archetype]` |", "| `/custom-crush` |", "| `/import-chats` |", "| `/crush-distill` |", "| `/chat [message]` |", "| `/crush-dashboard` |", "| `/crush-postmortem` |", "| `/list-crushes` |", "| `/let-go [session]` |", "| `/crush-llm [api_key]` |"),
        "Runtime Actions": tuple(f"`{action}`" for action in ACTIONS),
        "Persona Presets": tuple(f"| `{persona}`" for persona in PERSONAS),
        "Version Summary": tuple(f"| `{version}` |" for version in VERSIONS),
        "Ethics": ("It does not encourage", "It does not turn", "Do not import private conversations without consent.", "use `/let-go` to delete the session"),
        "License": ("MIT License. Free to use, modify, and distribute.",),
        "For Everyone Like The Author": ("Our generation learned ten thousand skills", "So we freeze in front of the chat box", "But love can be learned.", "When you can catch Ta's emotions naturally", "And maybe Ta's appearance has already given you what you needed", "You are already better than the person you were before meeting Ta.", "As for Ta, they stay in this commit.", "  <em>Made with 💙 by <a href=\"https://github.com/T1anhu4\">T1anhu4</a></em><br>", "  <em>for everyone learning how to love.</em>"),
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
    visible, errors, in_comment = [], [], False
    for line in text.splitlines():
        cursor = 0
        while cursor < len(line):
            if in_comment:
                end = line.find("-->", cursor)
                if end < 0: break
                in_comment, cursor = False, end + 3
            else:
                start = line.find("<!--", cursor)
                close = line.find("-->", cursor)
                if close >= 0 and (start < 0 or close < start):
                    errors.append("stray HTML comment close -->")
                    cursor = close + 3
                elif start >= 0:
                    visible.append(line[cursor:start])
                    in_comment, cursor = True, start + 4
                else:
                    visible.append(line[cursor:])
                    break
    if in_comment: errors.append("unclosed HTML comment at EOF")
    return "\n".join(visible), errors

def visible_content(text: str) -> tuple[str, list[str], str]:
    comment_free, comment_errors = remove_comments(text)
    without_fences, fence_errors = strip_fences(comment_free)
    return without_fences, fence_errors + comment_errors, comment_free

def split_sections(text: str) -> dict[str, str]:
    sections, current = {}, None
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            current = heading.group(1).strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections

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
    actual_lines = len(raw.splitlines())
    if actual_lines < contract["minimum_lines"]:
        errors.append(f"{path}: expected minimum {contract['minimum_lines']} lines, found {actual_lines}")
    visible, parser_errors, preserved_source = visible_content(raw)
    errors.extend(f"{path}: {error}" for error in parser_errors)
    plain = re.sub(r"<[^>]+>", "", visible)
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
    sections = split_sections(preserved_source)
    for section, markers in SECTION_MARKERS[path.name].items():
        body = sections.get(section, "")
        for marker in markers:
            if marker not in body:
                errors.append(f"{path}: missing scoped marker in {section}: {marker}")
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
    for legacy in LEGACY_MARKERS:
        if legacy.lower() in raw.lower():
            errors.append(f"{path}: forbidden legacy marker: {legacy}")
    errors.extend(check_urls(raw, path))
    return errors

def main(argv: list[str]) -> int:
    paths = [Path(item) for item in argv] or [Path("README.md"), Path("README_EN.md")]
    errors = [error for path in paths for error in check(path)]
    if errors: print("\n".join(errors)); return 1
    print("README transition contract passed"); return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
