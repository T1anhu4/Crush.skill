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
LAYOUTS = {
    "message-one-layout": (132, "reveal-one", 106, 238, 250),
    "readout-layout": (274, "reveal-two", 70, 344, 356),
    "message-two-layout": (376, "reveal-three", 110, 486, 498),
}
MAX_REVEAL_TRANSLATE_Y = 12
REVEAL_TIMELINES = {
    "reveal-one": "@keyframesreveal-one{0%,5%{opacity:0;transform:translateY(12px)}12%,92%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(0)}}",
    "reveal-two": "@keyframesreveal-two{0%,33%{opacity:0;transform:translateY(12px)}40%,92%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(0)}}",
    "reveal-three": "@keyframesreveal-three{0%,63%{opacity:0;transform:translateY(12px)}70%,92%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(0)}}",
}


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
    elements: dict[str, ET.Element] = {}
    for element in root.iter():
        element_id = element.get("id")
        if element_id is not None:
            assert element_id not in elements, f"duplicate id: {element_id}"
            elements[element_id] = element
    assert root.get("width") == "1200", "SVG width must be 1200"
    assert root.get("height") == "620", "SVG height must be 620"
    assert root.get("viewBox") == "0 0 1200 620", "SVG viewBox must be 0 0 1200 620"
    for element_id in REQUIRED_IDS:
        element_by_id(elements, element_id)

    panel = element_by_id(elements, "terminal-panel")
    assert panel.get("width") == "1040", "terminal-panel width must be 1040"
    assert panel.get("height") == "520", "terminal-panel height must be 520"
    parents = {child: parent for parent in root.iter() for child in parent}
    panel_parent = parents.get(panel)
    assert panel_parent is not None and local_name(panel_parent) == "g", "terminal-panel must have a group parent"
    assert panel_parent.get("transform") == "translate(80 50)", "terminal-panel parent must be translate(80 50)"

    styles = ["".join(element.itertext()) for element in root.iter() if local_name(element) == "style"]
    style = re.sub(r"\s+", "", "\n".join(styles))
    for name in REVEAL_KEYFRAMES:
        assert REVEAL_TIMELINES[name] in style, f"missing required {name} timeline"
    assert ".reveal{animation-duration:10s;animation-timing-function:ease-in-out;animation-iteration-count:infinite;animation-fill-mode:both}" in style, "missing reveal animation contract"
    for name in REVEAL_KEYFRAMES:
        assert f".{name}{{animation-name:{name}}}" in style, f"missing {name} animation name"
    assert "animation-delay" not in style, "animation-delay is forbidden"
    assert "@media(prefers-reduced-motion:reduce){.cursor,.wait,.reveal{animation:none;opacity:1;transform:none}}" in style, "missing reduced-motion reveal contract"

    panel_height = numeric(panel.get("height"), "terminal-panel height")
    for layout_id, (expected_y, reveal_class, expected_local_max, expected_resting_bottom, expected_animated_bottom) in LAYOUTS.items():
        layout = element_by_id(elements, layout_id)
        transform = layout.get("transform")
        match = TRANSLATE.fullmatch(transform.strip()) if transform else None
        assert match, f"{layout_id} must use a complete translate(x y) transform"
        base_y = float(match.group(2))
        assert transform == f"translate(46 {expected_y})", f"{layout_id} must use its exact layout transform"
        assert base_y == expected_y, f"{layout_id} must use base y {expected_y}"

        children = list(layout)
        assert children, f"{layout_id} must contain a reveal group"
        inner = children[0]
        classes = set((inner.get("class") or "").split())
        assert {"reveal", reveal_class} <= classes, f"{layout_id}'s first child must have reveal and {reveal_class}"
        assert inner.get("transform") is None, f"{layout_id}'s reveal group must not have transform"

        baselines = [numeric(text.get("y"), f"{layout_id} text y") for text in inner.iter() if local_name(text) == "text"]
        assert baselines, f"{layout_id} reveal group must contain text"
        local_max = max(baselines)
        resting_bottom = base_y + local_max
        animated_bottom = resting_bottom + MAX_REVEAL_TRANSLATE_Y
        assert local_max == expected_local_max, f"{layout_id} max local y must be {expected_local_max}"
        assert resting_bottom == expected_resting_bottom, f"{layout_id} resting bottom must be {expected_resting_bottom}"
        assert animated_bottom == expected_animated_bottom, f"{layout_id} animated bottom must be {expected_animated_bottom}"
        assert resting_bottom <= panel_height - 20, f"{layout_id} resting bottom exceeds terminal-panel clearance"
        assert animated_bottom <= panel_height - 20, f"{layout_id} animated bottom exceeds terminal-panel clearance"

    print("CLI SVG animation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
