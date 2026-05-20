from __future__ import annotations

from typing import Any, Dict, List

from .memory_engine import MemoryEngine


class ReplayEngine:
    def build_postmortem(self, memory: MemoryEngine, session_id: str, limit: int = 40) -> Dict[str, Any]:
        history = memory.get_state_history(session_id, limit=limit)
        timeline = memory.get_timeline(session_id, limit=limit)

        frame_collapses = self._frame_collapses(history)
        attraction_peaks = self._attraction_peaks(history)
        defense_triggers = self._defense_triggers(history)

        diagnostics = {
            "frame_collapses": frame_collapses,
            "attraction_peaks": attraction_peaks,
            "defense_triggers": defense_triggers,
        }

        narrative = self._build_narrative(diagnostics)

        return {
            "session_id": session_id,
            "diagnostics": diagnostics,
            "timeline": timeline,
            "narrative": narrative,
        }

    def _frame_collapses(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for item in history:
            delta = item.get("delta", {})
            tags = item.get("tags", [])
            if delta.get("favorability", 0) <= -10 or "frame_collapse_risk" in tags:
                findings.append(
                    {
                        "created_at": item.get("created_at"),
                        "signal": "框架崩塌点",
                        "why": item.get("note") or "高需求感/高压力导致吸引力下滑",
                        "delta": delta,
                    }
                )
        return findings[:5]

    def _attraction_peaks(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for item in history:
            delta = item.get("delta", {})
            state = item.get("state", {})
            if delta.get("favorability", 0) >= 10 or state.get("propulsion", 0) >= 55:
                findings.append(
                    {
                        "created_at": item.get("created_at"),
                        "signal": "吸引力峰值",
                        "why": item.get("note") or "情绪共鸣/推拉成功",
                        "state": state,
                    }
                )
        return findings[:5]

    def _defense_triggers(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for item in history:
            tags = item.get("tags", [])
            state = item.get("state", {})
            if "defense_triggered" in tags or state.get("defense_level", 0) >= 60:
                findings.append(
                    {
                        "created_at": item.get("created_at"),
                        "signal": "防御触发点",
                        "why": item.get("note") or "关系推进过快或安全感缺失",
                        "state": state,
                    }
                )
        return findings[:5]

    def _build_narrative(self, diagnostics: Dict[str, List[Dict[str, Any]]]) -> str:
        lines = []

        if diagnostics["frame_collapses"]:
            lines.append("框架崩塌: 检测到需求感或推进压力导致的关系降温。")
        else:
            lines.append("框架崩塌: 暂未检测到明显崩塌事件。")

        if diagnostics["attraction_peaks"]:
            lines.append("吸引力峰值: 存在有效的共鸣/张力上升时刻。")
        else:
            lines.append("吸引力峰值: 峰值不足，建议增加轻松互动和真实表达。")

        if diagnostics["defense_triggers"]:
            lines.append("防御触发: 对方出现防御反应，需降压并拉长节奏。")
        else:
            lines.append("防御触发: 防御状态整体可控。")

        return "\n".join(lines)
