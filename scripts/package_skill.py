#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "Crush邂逅.skill"
DIST_DIR = SKILL_DIR / "dist"

EXCLUDED_PARTS = {
    "__pycache__",
    "data",
    "dist",
    "examples",
}

EXCLUDED_SUFFIXES = {".pyc", ".sqlite3"}



def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDED_PARTS:
            return True
    if path.name.startswith("."):
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    return False



def build_zip(target: Path) -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(SKILL_DIR.rglob("*")):
            if file_path.is_dir():
                continue
            rel = file_path.relative_to(SKILL_DIR)
            if should_skip(rel):
                continue
            zf.write(file_path, arcname=str(rel))



def main() -> int:
    openclaw_zip = DIST_DIR / "crush_xiehou_openclaw.zip"
    qwenpaw_zip = DIST_DIR / "crush_xiehou_qwenpaw.zip"

    build_zip(openclaw_zip)
    build_zip(qwenpaw_zip)

    print(f"built: {openclaw_zip}")
    print(f"built: {qwenpaw_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
