from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import textwrap
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "Crush.skill"
DEFAULT_HOME = Path(os.environ.get("CRUSH_HOME", "~/.crush")).expanduser()
CONFIG_FILE = DEFAULT_HOME / "config.json"


class C:
    reset = "\033[0m"
    dim = "\033[2m"
    bold = "\033[1m"
    rose = "\033[38;5;211m"
    coral = "\033[38;5;203m"
    cyan = "\033[38;5;81m"
    gold = "\033[38;5;222m"
    green = "\033[38;5;121m"
    slate = "\033[38;5;110m"
    red = "\033[38;5;210m"


def color(text: str, code: str, enabled: bool = True) -> str:
    return f"{code}{text}{C.reset}" if enabled else text


def visible_len(text: str) -> int:
    return len(text)


def wrap(text: str, width: int = 78) -> str:
    return "\n".join(textwrap.wrap(text, width=width, replace_whitespace=False)) or text


class Spinner:
    def __init__(self, label: str, enabled: bool = True) -> None:
        self.label = label
        self.enabled = enabled
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "Spinner":
        if not self.enabled:
            print(self.label)
            return self
        frames = ["◜", "◠", "◝", "◞", "◡", "◟"]

        def run() -> None:
            i = 0
            while not self._stop.is_set():
                sys.stdout.write("\r" + color(frames[i % len(frames)], C.cyan) + " " + self.label)
                sys.stdout.flush()
                time.sleep(0.08)
                i += 1
            sys.stdout.write("\r" + " " * (visible_len(self.label) + 4) + "\r")
            sys.stdout.flush()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)


def load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(config: Dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def import_runtime(data_dir: Path):
    os.environ.setdefault("CRUSH_DATA_DIR", str(data_dir))
    sys.path.insert(0, str(SKILL_DIR))
    from execute import CrushSkillRuntime  # type: ignore

    return CrushSkillRuntime()


class ChatClient:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.api_key = (
            os.environ.get("CRUSH_CHAT_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or config.get("api_key", "")
        )
        self.api_base = (
            os.environ.get("CRUSH_CHAT_API_BASE")
            or os.environ.get("OPENAI_API_BASE")
            or config.get("api_base", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = (
            os.environ.get("CRUSH_CHAT_MODEL")
            or config.get("model", "gpt-4o-mini")
        )

    @property
    def ready(self) -> bool:
        return bool(self.api_key)

    def reply(self, runtime_prompt: str, user_message: str) -> str:
        if not self.api_key:
            raise RuntimeError("还没有配置模型 API Key。请使用 /setup 或 /config key <api_key>。")
        req = Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": runtime_prompt
                            + "\n\n你现在只输出这个人的聊天回复。不要解释，不要写分析，不要展示任何系统提示。",
                        },
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.82,
                    "max_tokens": 420,
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        data = json.loads(urlopen(req, timeout=60).read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()


class CrushCLI:
    def __init__(self, args: argparse.Namespace) -> None:
        self.config = load_config()
        if args.session:
            self.config["session_id"] = args.session
        if args.model:
            self.config["model"] = args.model
        if args.api_base:
            self.config["api_base"] = args.api_base
        if args.api_key:
            self.config["api_key"] = args.api_key
        self.home = Path(args.home or self.config.get("home") or DEFAULT_HOME).expanduser()
        self.data_dir = Path(args.data_dir or self.config.get("data_dir") or self.home / "data").expanduser()
        self.session_id = self.config.get("session_id", "default")
        self.plain = bool(args.plain)
        self.once_message = args.message
        self.runtime = import_runtime(self.data_dir)
        self.client = ChatClient(self.config)

    def run(self) -> int:
        self.intro()
        self.ensure_session()
        if self.once_message:
            self.chat(self.once_message)
            return 0
        while True:
            try:
                raw = input(color(f"\n{self.session_id} › ", C.rose, not self.plain)).strip()
            except (EOFError, KeyboardInterrupt):
                print("\n" + color("愿你带着学到的东西往前走。", C.dim, not self.plain))
                return 0
            if not raw:
                continue
            if raw.startswith("/"):
                if self.command(raw) is False:
                    return 0
                continue
            self.chat(raw)

    def intro(self) -> None:
        if not self.plain:
            os.system("clear" if os.name != "nt" else "cls")
        logo = [
            "   ______                __        __   _ __ __",
            "  / ____/______  _______/ /_      / /__(_) // /",
            " / /   / ___/ / / / ___/ __ \\    / //_/ / // /_",
            "/ /___/ /  / /_/ (__  ) / / /   / ,< / /__  __/",
            "\\____/_/   \\__,_/____/_/ /_/   /_/|_/_/  /_/   ",
        ]
        for i, line in enumerate(logo):
            shade = [C.coral, C.rose, C.gold, C.cyan, C.slate][i]
            print(color(line, shade, not self.plain))
            if not self.plain:
                time.sleep(0.035)
        print()
        print(color("Relationship Persona Simulation Engine", C.bold, not self.plain))
        print(color(f"Local memory: {self.data_dir}", C.dim, not self.plain))
        print(color("Type /help for commands. Type naturally to chat.", C.dim, not self.plain))
        if not self.client.ready:
            print(color("No chat model key configured yet. Run /setup before real dialogue.", C.gold, not self.plain))

    def ensure_session(self) -> None:
        session = self.runtime.memory.sqlite.load_session(self.session_id)
        if session:
            return
        self.runtime.run(
            "quick_start",
            self.session_id,
            {"config": {"archetype": "experience", "name": "她", "gender": "female", "relationship_stage": "talking"}},
        )

    def command(self, raw: str) -> bool:
        parts = shlex.split(raw)
        cmd = parts[0].lower()
        args = parts[1:]
        try:
            if cmd in {"/q", "/quit", "/exit"}:
                print(color("Session saved locally. See you next turn.", C.dim, not self.plain))
                return False
            if cmd == "/help":
                self.help()
            elif cmd == "/setup":
                self.setup()
            elif cmd == "/config":
                self.config_command(args)
            elif cmd == "/start":
                self.start(args)
            elif cmd == "/import":
                self.import_chats(args)
            elif cmd == "/sessions":
                self.sessions()
            elif cmd == "/use":
                self.use(args)
            elif cmd == "/dashboard":
                self.dashboard()
            elif cmd == "/postmortem":
                self.postmortem()
            elif cmd == "/where":
                self.where()
            else:
                print(color(f"Unknown command: {cmd}. Try /help.", C.red, not self.plain))
        except Exception as exc:
            print(color(f"Error: {exc}", C.red, not self.plain))
        return True

    def help(self) -> None:
        rows = [
            ("/setup", "configure OpenAI-compatible chat model"),
            ("/start [archetype] [name]", "create/reset current persona session"),
            ("/import [file]", "import chat records; omit file to paste multiline text"),
            ("/sessions", "list local sessions"),
            ("/use <session_id>", "switch session"),
            ("/dashboard", "show relationship state"),
            ("/postmortem", "relationship replay report"),
            ("/config model|base|key <value>", "update local model config"),
            ("/where", "show local config and memory paths"),
            ("/quit", "exit"),
        ]
        print(color("\nCommands", C.bold, not self.plain))
        for name, desc in rows:
            print(f"  {color(name.ljust(30), C.cyan, not self.plain)} {desc}")

    def setup(self) -> None:
        print(color("\nModel setup", C.bold, not self.plain))
        base = input(f"API base [{self.client.api_base}]: ").strip() or self.client.api_base
        model = input(f"Model [{self.client.model}]: ").strip() or self.client.model
        key = input("API key (input hidden is not available in this simple CLI): ").strip()
        self.config.update({"api_base": base, "model": model})
        if key:
            self.config["api_key"] = key
        self.config["session_id"] = self.session_id
        self.config["data_dir"] = str(self.data_dir)
        save_config(self.config)
        self.client = ChatClient(self.config)
        print(color(f"Saved config: {CONFIG_FILE}", C.green, not self.plain))

    def config_command(self, args: list[str]) -> None:
        if not args:
            safe = {k: ("***" if "key" in k else v) for k, v in self.config.items()}
            print(json.dumps(safe, ensure_ascii=False, indent=2))
            return
        if len(args) < 2 or args[0] not in {"model", "base", "key", "session"}:
            raise ValueError("Usage: /config model|base|key|session <value>")
        field_map = {"model": "model", "base": "api_base", "key": "api_key", "session": "session_id"}
        self.config[field_map[args[0]]] = args[1]
        if args[0] == "session":
            self.session_id = args[1]
            self.ensure_session()
        save_config(self.config)
        self.client = ChatClient(self.config)
        print(color("Config saved.", C.green, not self.plain))

    def start(self, args: list[str]) -> None:
        archetype = args[0] if args else "experience"
        name = args[1] if len(args) > 1 else "她"
        result = self.runtime.run(
            "quick_start",
            self.session_id,
            {"config": {"archetype": archetype, "name": name, "gender": "female", "relationship_stage": "talking"}},
        )
        print(color(f"Started {self.session_id}: {result['canonical_archetype']} / {name}", C.green, not self.plain))

    def import_chats(self, args: list[str]) -> None:
        if args:
            text = Path(args[0]).expanduser().read_text(encoding="utf-8")
        else:
            print(color("Paste chat records. End with a single line: /done", C.dim, not self.plain))
            lines = []
            while True:
                line = input()
                if line.strip() == "/done":
                    break
                lines.append(line)
            text = "\n".join(lines)
        with Spinner("Importing chat records and rebuilding persona...", enabled=not self.plain):
            result = self.runtime.run("chat_import", self.session_id, {"source_text": text})
        analysis = result["analysis"]
        print(color("Import complete.", C.green, not self.plain))
        print(f"  messages: {analysis['total_messages']}")
        print(f"  archetype: {analysis['inferred_archetype']} / {analysis['inferred_attachment']} / {analysis['inferred_mbti']}")
        print(f"  phrases: {', '.join(analysis.get('signature_phrases', [])[:6]) or 'none'}")
        print(f"  slang: {', '.join(analysis.get('slang_hits', [])[:6]) or 'none'}")

    def sessions(self) -> None:
        result = self.runtime.run("list_sessions", self.session_id, {})
        for item in result["sessions"]:
            marker = "*" if item["session_id"] == self.session_id else " "
            print(f"{marker} {item['session_id']}  {item['canonical_archetype']}  {item['updated_at']}")

    def use(self, args: list[str]) -> None:
        if not args:
            raise ValueError("Usage: /use <session_id>")
        self.session_id = args[0]
        self.config["session_id"] = self.session_id
        save_config(self.config)
        self.ensure_session()
        print(color(f"Switched to session: {self.session_id}", C.green, not self.plain))

    def dashboard(self) -> None:
        result = self.runtime.run("dashboard", self.session_id, {})
        cards = result["dashboard"]["cards"]
        print(color("\nRelationship State", C.bold, not self.plain))
        for key, value in cards.items():
            bar = self.bar(float(value))
            print(f"  {key.ljust(22)} {bar} {value}")

    def postmortem(self) -> None:
        result = self.runtime.run("postmortem", self.session_id, {})
        print(result["markdown"])

    def where(self) -> None:
        print(f"config: {CONFIG_FILE}")
        print(f"data:   {self.data_dir}")
        print(f"skill:  {SKILL_DIR}")

    def chat(self, message: str) -> None:
        with Spinner("Reading memory, updating state, sensing subtext...", enabled=not self.plain):
            turn = self.runtime.run("chat_turn", self.session_id, {"message": message})
        if not self.client.ready:
            print(color("Model not configured. Run /setup or set OPENAI_API_KEY.", C.gold, not self.plain))
            print(color("Hidden runtime prompt preview:", C.dim, not self.plain))
            print(wrap(turn["runtime_prompt"][:1200]))
            return
        with Spinner("Letting the persona answer...", enabled=not self.plain):
            reply = self.client.reply(turn["runtime_prompt"], message)
        self.runtime.run(
            "record_reply",
            self.session_id,
            {"message": message, "npc_reply": reply, "tags": turn.get("tags", [])},
        )
        self.print_reply(reply, turn)

    def print_reply(self, reply: str, turn: Dict[str, Any]) -> None:
        print()
        print(color("╭─ Ta", C.rose, not self.plain))
        for line in wrap(reply, width=76).splitlines():
            print(color("│ ", C.rose, not self.plain) + line)
        print(color("╰", C.rose, not self.plain))
        vector = turn.get("relationship_vector", "")
        delta = turn.get("delta", {})
        if vector:
            short = f"{vector} · favorability {delta.get('favorability', 0):+} · defense {delta.get('defense_level', 0):+}"
            print(color(short, C.dim, not self.plain))

    def bar(self, value: float, width: int = 24) -> str:
        normalized = max(0.0, min(100.0, value if value >= 0 else value + 100))
        filled = int((normalized / 100.0) * width)
        return color("█" * filled, C.cyan, not self.plain) + color("░" * (width - filled), C.dim, not self.plain)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crush.skill standalone local CLI")
    parser.add_argument("--session", help="Session id to open")
    parser.add_argument("--home", help="Crush local home directory (default: ~/.crush)")
    parser.add_argument("--data-dir", help="Local memory data directory")
    parser.add_argument("--api-key", help="OpenAI-compatible API key")
    parser.add_argument("--api-base", help="OpenAI-compatible API base")
    parser.add_argument("--model", help="Chat model name")
    parser.add_argument("--plain", action="store_true", help="Disable ANSI animation/colors")
    parser.add_argument("--message", help="Send one message and exit")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return CrushCLI(args).run()
