#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "Crush.skill" / "dist"
TARGET = DIST_DIR / "crush_cli_standalone.zip"

INCLUDE_DIRS = ["Crush.skill", "crush_cli", "scripts", "assets"]
INCLUDE_FILES = [
    "README.md",
    "README_EN.md",
    "LICENSE",
    "requirements.txt",
    "requirements-mem0.txt",
    "Makefile",
]
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".claude",
    ".learnings",
    "__pycache__",
    "data",
    "dist",
}
EXCLUDED_SUFFIXES = {".pyc", ".sqlite3"}


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    if path.name.startswith(".") and path.name not in {".gitignore"}:
        return True
    return path.suffix in EXCLUDED_SUFFIXES


def add_path(zf: zipfile.ZipFile, path: Path) -> None:
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file():
                add_path(zf, item)
        return
    rel = path.relative_to(ROOT)
    if should_skip(rel):
        return
    zf.write(path, arcname=str(rel))


def main() -> int:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirname in INCLUDE_DIRS:
            add_path(zf, ROOT / dirname)
        for filename in INCLUDE_FILES:
            add_path(zf, ROOT / filename)
    print(f"built: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
