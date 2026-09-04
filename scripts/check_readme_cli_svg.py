#!/usr/bin/env python3
"""Check the layout and animation contract for the README CLI SVG demo."""
from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "assets/readme-cli-demo.svg"
LAYOUT_IDS = ("message-one-layout", "readout-layout", "message-two-layout")
REQUIRED_IDS = ("terminal-panel", *LAYOUT_IDS)
REVEAL_KEYFRAMES = ("reveal-one", "reveal-two", "reveal-three")
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
TRANSLATE = re.compile(rf"translate\(\s*({NUMBER})[ ,]+({NUMBER})\s*\)")


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def numeric(value: str | None, label: str) -> float:
    assert value is not None and re.fullmatch(NUMBER, value.strip()), f"{label} must be numeric"
    return float(value)


def element_by_id(elements: dict[str, ET.Element], element_id: str) -> ET.Element:
    assert element_id in elements, f"missing required id: {element_id}"
    return elements[element_id]


def main() -> int:
    root = ET.parse(SVG_PATH).getroot()
    elements = {element.get("id"): element for element in root.iter() if element.get("id")}
    for element_id in REQUIRED_IDS:
        element_by_id(elements, element_id)

    styles = ["".join(element.itertext()) for element in root.iter() if local_name(element) == "style"]
    style = "\n".join(styles)
    for name in REVEAL_KEYFRAMES:
        assert f"@keyframes {name}" in style, f"missing @keyframes {name}"
    assert "animation-fill-mode:both" in style, "missing animation-fill-mode:both"
    assert "animation-delay" not in style, "animation-delay is forbidden"

    panel_height = numeric(element_by_id(elements, "terminal-panel").get("height"), "terminal-panel height")
    for layout_id in LAYOUT_IDS:
        layout = element_by_id(elements, layout_id)
        transform = layout.get("transform")
        match = TRANSLATE.fullmatch(transform.strip()) if transform else None
        assert match, f"{layout_id} must use a complete translate(x y) transform"
        base_y = float(match.group(2))

        children = list(layout)
        assert children, f"{layout_id} must contain a reveal group"
        inner = children[0]
        classes = set((inner.get("class") or "").split())
        assert "reveal" in classes, f"{layout_id}'s first child must have class reveal"
        assert inner.get("transform") is None, f"{layout_id}'s reveal group must not have transform"

        baselines = [numeric(text.get("y"), f"{layout_id} text y") for text in inner.iter() if local_name(text) == "text"]
        assert baselines, f"{layout_id} reveal group must contain text"
        assert base_y + max(baselines) <= panel_height - 20, f"{layout_id} exceeds terminal-panel bottom clearance"

    print("CLI SVG animation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
