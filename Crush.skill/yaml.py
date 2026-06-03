from __future__ import annotations

import ast
from typing import Any, TextIO


def safe_load(stream: str | TextIO) -> dict[str, Any]:
    """Tiny YAML subset parser used when PyYAML is unavailable.

    It supports the preset files in this repository: indentation-based dicts,
    scalar values, quoted strings, numbers, booleans, nulls, and inline lists.
    """
    text = stream.read() if hasattr(stream, "read") else str(stream)
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root

        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)

    return root


def _parse_scalar(value: str) -> Any:
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith(("[", "{", '"', "'")):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value.strip("\"'")
    try:
        if any(ch in value for ch in [".", "e", "E"]):
            return float(value)
        return int(value)
    except ValueError:
        return value
