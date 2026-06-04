"""Relationship distillation report engine.

This module turns imported chats or saved episodes into an evidence-first
relationship literacy report. It intentionally avoids deterministic labels from
thin evidence; every sensitive readout is paired with confidence and limits.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List


@dataclass
class EvidenceItem:
    layer: str
    signal: str
    confidence: float
    examples: List[str] = field(default_factory=list)
    readout: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "signal": self.signal,
            "confidence": round(self.confidence, 2),
            "examples": self.examples,
            "readout": self.readout,
        }


class RelationshipDistillationEngine:
    """Build transparent persona and relationship reports from conversation data."""

    BOUNDARY_RE = re.compile(r"看情况|再说|别太|别上头|不想|不要|算了|随便|冷静|太快|尴尬|压力|先别|过了")
    FLIRT_RE = re.compile(r"喜欢|想你|见面|约|吃饭|电影|可爱|想见|心动|暧昧|宝宝|宝贝|亲|晚安|早安")
    MATERIAL_RE = re.compile(r"红包|转账|买包|礼物|请我|给我买|奶茶|请客|钱|贵|消费|付款|aa|AA")
    HUMOR_RE = re.compile(r"笑死|哈哈+|hhh+|救命|抽象|离谱|地铁老人|我真的会谢|绝了|绷不住|蚌埠住|xswl")
    QUESTION_RE = re.compile(r"[?？]|吗|嘛|呢|怎么|为什么|啥|干嘛|在干嘛|吃了没|到哪")
    SOFT_DECLINE_RE = re.compile(r"看情况|下次吧|再说吧|不一定|有空再|先看看|可能吧")

    def build_from_messages(self, messages: Iterable[Any], analysis: Any | None = None) -> Dict[str, Any]:
        rows = [self._normalize_message(item) for item in messages]
        return self._build(rows, analysis)

    def build_from_episodes(self, episodes: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        rows = []
        for item in reversed(list(episodes)):
            role = item.get("role", "")
            sender = "other" if role in {"npc", "other", "import"} else "self"
            rows.append(
                {
                    "sender": sender,
                    "content": item.get("content", ""),
                    "timestamp": item.get("created_at", ""),
                    "original_line": item.get("content", ""),
                }
            )
        return self._build(rows, None)

    def _build(self, rows: List[Dict[str, str]], analysis: Any | None) -> Dict[str, Any]:
        rows = [row for row in rows if row.get("content", "").strip()]
        other = [row for row in rows if row["sender"] == "other"]
        self_rows = [row for row in rows if row["sender"] == "self"]
        other_text = "\n".join(row["content"] for row in other)
        self_text = "\n".join(row["content"] for row in self_rows)

        source = {
            "total_messages": len(rows),
            "other_messages": len(other),
            "self_messages": len(self_rows),
            "date_range": self._date_range(rows, analysis),
        }
        expression = self._expression_dna(other, other_text, analysis)
        rhythm = self._rhythm(rows, other, self_rows)
        boundaries = self._boundary_readout(other, other_text)
        flirt = self._flirt_readout(rows, other, self_rows)
        material = self._material_readout(rows, other_text, self_text)
        radar = self._relationship_radar(source, expression, rhythm, boundaries, flirt, material, analysis)
        evidence = self._evidence_items(expression, rhythm, boundaries, flirt, material, radar)
        playbook = self._coaching_playbook(radar, boundaries, flirt, material, rhythm)
        validation = self._validation(source, evidence)
        limitations = self._limitations(source, validation)
        report = {
            "source": source,
            "evidence_map": [item.to_dict() for item in evidence],
            "persona_dna": expression,
            "relationship_radar": radar,
            "communication_patterns": {
                "rhythm": rhythm,
                "boundaries": boundaries,
                "flirtation": flirt,
                "materiality": material,
            },
            "coaching_playbook": playbook,
            "validation": validation,
            "limitations": limitations,
        }
        report["markdown"] = self.render_markdown(report)
        return report

    def _normalize_message(self, item: Any) -> Dict[str, str]:
        if isinstance(item, dict):
            sender = str(item.get("sender") or item.get("role") or "")
            if sender in {"npc", "other", "import"}:
                sender = "other"
            elif sender in {"user", "self"}:
                sender = "self"
            else:
                sender = "other"
            return {
                "sender": sender,
                "content": str(item.get("content") or item.get("message") or item.get("text") or ""),
                "timestamp": str(item.get("timestamp") or item.get("created_at") or ""),
                "original_line": str(item.get("original_line") or item.get("content") or ""),
            }
        return {
            "sender": getattr(item, "sender", "other"),
            "content": getattr(item, "content", ""),
            "timestamp": getattr(item, "timestamp", ""),
            "original_line": getattr(item, "original_line", ""),
        }

    def _date_range(self, rows: List[Dict[str, str]], analysis: Any | None) -> List[str]:
        if analysis and hasattr(analysis, "date_range"):
            return list(getattr(analysis, "date_range") or ["", ""])
        stamps = [row["timestamp"] for row in rows if row.get("timestamp")]
        return [stamps[0], stamps[-1]] if stamps else ["", ""]

    def _expression_dna(self, other: List[Dict[str, str]], text: str, analysis: Any | None) -> Dict[str, Any]:
        phrases = []
        if analysis and hasattr(analysis, "signature_phrases"):
            phrases.extend(getattr(analysis, "signature_phrases") or [])
        phrases.extend(hit for hit in self.HUMOR_RE.findall(text))
        emoji = re.findall(r"[\U0001f300-\U0001faff]|[😂🤣💀🔥🥲😭😅🥸]", text)
        tokens = Counter(re.findall(r"[\u4e00-\u9fff]{2,6}|[a-zA-Z]{2,}", text))
        filler = [word for word, _ in tokens.most_common(12) if word not in {"这个", "那个", "就是", "可以"}]
        question_ratio = self._ratio(sum(1 for row in other if self.QUESTION_RE.search(row["content"])), len(other))
        avg_len = round(sum(len(row["content"]) for row in other) / max(1, len(other)), 1)
        phrase_list = list(dict.fromkeys(phrases))[:10]
        return {
            "signature_phrases": phrase_list,
            "emoji_favorites": [item for item, _ in Counter(emoji).most_common(6)],
            "avg_message_length": avg_len,
            "question_ratio": round(question_ratio, 2),
            "humor_density": round(self._ratio(len(self.HUMOR_RE.findall(text)), len(other)), 2),
            "top_terms": filler[:8],
            "style_readout": self._style_readout(avg_len, question_ratio, phrase_list),
        }

    def _rhythm(self, rows: List[Dict[str, str]], other: List[Dict[str, str]], self_rows: List[Dict[str, str]]) -> Dict[str, Any]:
        starts = 0
        for idx, row in enumerate(rows):
            if row["sender"] == "other" and (idx == 0 or rows[idx - 1]["sender"] == "other"):
                starts += 1
        other_questions = sum(1 for row in other if self.QUESTION_RE.search(row["content"]))
        self_questions = sum(1 for row in self_rows if self.QUESTION_RE.search(row["content"]))
        initiative = self._ratio(starts + other_questions, max(1, len(other)))
        return {
            "other_question_count": other_questions,
            "self_question_count": self_questions,
            "other_initiative_score": round(min(1.0, initiative), 2),
            "initiative_readout": "主动探索" if initiative >= 0.38 else "被动接话" if initiative <= 0.18 else "中等主动",
            "dialogue_balance": "你问得更多" if self_questions > other_questions + 1 else "对方也在探索" if other_questions >= self_questions else "基本均衡",
        }

    def _boundary_readout(self, other: List[Dict[str, str]], text: str) -> Dict[str, Any]:
        hits = self._examples(other, self.BOUNDARY_RE, 5)
        soft = self._examples(other, self.SOFT_DECLINE_RE, 5)
        score = min(1.0, (len(hits) * 0.24) + (len(soft) * 0.18))
        if hits and soft:
            score = max(score, 0.42)
        return {
            "score": round(score, 2),
            "examples": hits,
            "soft_declines": soft,
            "readout": "边界敏感，需要慢推进" if score >= 0.4 else "边界信号较少，但仍需保留节奏",
        }

    def _flirt_readout(self, rows: List[Dict[str, str]], other: List[Dict[str, str]], self_rows: List[Dict[str, str]]) -> Dict[str, Any]:
        other_hits = self._examples(other, self.FLIRT_RE, 6)
        self_hits = self._examples(self_rows, self.FLIRT_RE, 6)
        other_score = min(1.0, len(other_hits) * 0.2)
        self_score = min(1.0, len(self_hits) * 0.16)
        friend_frame = other_score < 0.25 and self_score < 0.45
        return {
            "other_flirt_score": round(other_score, 2),
            "self_romance_push_score": round(self_score, 2),
            "other_examples": other_hits,
            "self_examples": self_hits,
            "readout": "有暧昧窗口" if other_score >= 0.4 else "更像朋友/观察期" if friend_frame else "你推进更多，对方证据不足",
        }

    def _material_readout(self, rows: List[Dict[str, str]], other_text: str, self_text: str) -> Dict[str, Any]:
        other_hits = [line for line in other_text.splitlines() if self.MATERIAL_RE.search(line)][:6]
        self_hits = [line for line in self_text.splitlines() if self.MATERIAL_RE.search(line)][:6]
        score = min(1.0, len(other_hits) * 0.18)
        return {
            "material_request_score": round(score, 2),
            "other_examples": other_hits,
            "self_examples": self_hits,
            "readout": "出现物质请求线索，需看长期一致性" if score >= 0.35 else "没有足够证据判断物质导向",
            "safety_note": "单句红包/请客不能等同于拜金；必须结合频率、互惠、语境和边界。",
        }

    def _relationship_radar(
        self,
        source: Dict[str, Any],
        expression: Dict[str, Any],
        rhythm: Dict[str, Any],
        boundaries: Dict[str, Any],
        flirt: Dict[str, Any],
        material: Dict[str, Any],
        analysis: Any | None,
    ) -> Dict[str, Any]:
        active = rhythm["other_initiative_score"]
        boundary = boundaries["score"]
        other_flirt = flirt["other_flirt_score"]
        self_push = flirt["self_romance_push_score"]
        archetype = getattr(analysis, "inferred_archetype", "") if analysis else ""
        phase = getattr(analysis, "relationship_phase", "") if analysis else ""
        return {
            "active_passive": "推进型/主动型" if active >= 0.42 else "被动型/慢热型" if active <= 0.2 else "中等主动",
            "ie_tendency": "偏 E：表达和反应外放" if expression["humor_density"] >= 0.35 or expression["question_ratio"] >= 0.45 else "偏 I 或谨慎：表达更收敛",
            "warm_guarded": "热情但有边界" if other_flirt >= 0.35 and boundary >= 0.35 else "偏防备/观察" if boundary >= 0.45 else "轻松友好",
            "friend_or_flirt": "暧昧窗口存在" if other_flirt >= 0.4 else "朋友框架或观察期" if self_push <= 0.35 else "用户推进高于对方回应",
            "slow_burn_or_fishing": self._slow_burn_readout(boundary, active, material["material_request_score"], other_flirt),
            "material_risk": material["readout"],
            "current_phase": phase or ("talking" if source["total_messages"] else "unknown"),
            "import_archetype": archetype or "evidence_based",
        }

    def _slow_burn_readout(self, boundary: float, active: float, material: float, flirt: float) -> str:
        if material >= 0.5 and active >= 0.25:
            return "可能存在资源/关注索取风险，需要更多互惠证据"
        if boundary >= 0.4 and active >= 0.2:
            return "慢热或谨慎推进：不是拒绝，但需要尊重节奏"
        if flirt >= 0.45:
            return "有推进意愿，可低成本轻推"
        return "证据不足，先维持探索"

    def _evidence_items(
        self,
        expression: Dict[str, Any],
        rhythm: Dict[str, Any],
        boundaries: Dict[str, Any],
        flirt: Dict[str, Any],
        material: Dict[str, Any],
        radar: Dict[str, Any],
    ) -> List[EvidenceItem]:
        return [
            EvidenceItem("表达 DNA", "口头禅/梗/表情", 0.7 if expression["signature_phrases"] else 0.35, expression["signature_phrases"][:5], expression["style_readout"]),
            EvidenceItem("互动节奏", "主动性与问题比例", 0.68, [rhythm["dialogue_balance"]], rhythm["initiative_readout"]),
            EvidenceItem("边界系统", "软拒绝/降速信号", 0.75 if boundaries["examples"] else 0.42, boundaries["examples"][:4], boundaries["readout"]),
            EvidenceItem("暧昧窗口", "对方主动暧昧与用户推进差", 0.65 if flirt["other_examples"] or flirt["self_examples"] else 0.35, (flirt["other_examples"] + flirt["self_examples"])[:4], flirt["readout"]),
            EvidenceItem("物质/互惠", "礼物、请客、转账等语义", 0.55 if material["other_examples"] else 0.3, material["other_examples"][:4], material["readout"]),
            EvidenceItem("关系雷达", "综合阶段判断", 0.62, [radar["friend_or_flirt"], radar["slow_burn_or_fishing"]], radar["warm_guarded"]),
        ]

    def _coaching_playbook(
        self,
        radar: Dict[str, Any],
        boundaries: Dict[str, Any],
        flirt: Dict[str, Any],
        material: Dict[str, Any],
        rhythm: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        next_moves = []
        avoid = []
        drills = []
        if boundaries["score"] >= 0.35:
            next_moves.append("先接住对方的边界，再用低成本话题继续探索。")
            avoid.append("不要把昵称、喜欢、见面、承诺连续追问成考试。")
            drills.append("练习把“你喜欢我吗”改成“你刚刚这个反应有点可爱，我先记一笔”。")
        if flirt["other_flirt_score"] >= 0.4:
            next_moves.append("可以轻推一句暧昧，但不要马上要确定答案。")
        elif flirt["self_romance_push_score"] > flirt["other_flirt_score"] + 0.2:
            next_moves.append("降一点需求感，把话题拉回共同经历和轻松探索。")
            avoid.append("不要用“你不拒绝就是同意”这类默认同意规则。")
        if rhythm["other_initiative_score"] <= 0.2:
            next_moves.append("先判断对方是否只是礼貌回复，减少连续输出。")
        if material["material_request_score"] >= 0.35:
            avoid.append("不要用花钱换亲密，也不要立刻给道德审判。")
            drills.append("观察互惠：她是否也投入时间、关心、计划和解释。")
        drills.append("每 5 轮复盘一次：我是在探索她，还是在索取确认？")
        return {
            "next_best_moves": next_moves or ["维持轻松探索，多问生活细节，少要关系答案。"],
            "avoid": avoid or ["不要把单句玩笑当成稳定人格标签。"],
            "practice_drills": drills,
            "ethical_boundary": ["训练目标是识别关系信号和尊重边界，不是操控、冷暴力或故意制造焦虑。"],
        }

    def _validation(self, source: Dict[str, Any], evidence: List[EvidenceItem]) -> Dict[str, Any]:
        size_score = min(1.0, source["total_messages"] / 80)
        evidence_score = sum(item.confidence for item in evidence) / max(1, len(evidence))
        confidence = round((size_score * 0.45) + (evidence_score * 0.55), 2)
        if confidence >= 0.72:
            level = "high"
        elif confidence >= 0.48:
            level = "medium"
        else:
            level = "low"
        return {
            "confidence": confidence,
            "level": level,
            "source_coverage": round(size_score, 2),
            "evidence_layers": len(evidence),
            "triple_check": [
                "source snippets: every label should trace to concrete lines",
                "counterexamples: one friendly message is not proof of romantic interest",
                "safety: sensitive labels stay probabilistic until repeated evidence appears",
            ],
        }

    def _limitations(self, source: Dict[str, Any], validation: Dict[str, Any]) -> List[str]:
        notes = []
        if source["total_messages"] < 30:
            notes.append("样本少于 30 条，报告只能作为训练假设，不能当作稳定人格判断。")
        if not any(source["date_range"]):
            notes.append("缺少时间戳，无法可靠判断回复节奏、冷淡周期和长期主动性。")
        if validation["level"] == "low":
            notes.append("当前置信度较低，建议导入更多真实聊天记录后重新运行 /distill。")
        notes.append("报告不替代现实沟通；真正的边界需要对方明确表达。")
        return notes

    def render_markdown(self, report: Dict[str, Any]) -> str:
        source = report["source"]
        radar = report["relationship_radar"]
        validation = report["validation"]
        lines = [
            "# Relationship Distillation Report",
            "",
            f"- messages: {source['total_messages']} (other {source['other_messages']} / self {source['self_messages']})",
            f"- confidence: {validation['level']} / {validation['confidence']}",
            "",
            "## Evidence Map",
            "| Layer | Signal | Confidence | Readout | Evidence |",
            "|---|---:|---:|---|---|",
        ]
        for item in report["evidence_map"]:
            examples = " / ".join(item["examples"][:3]) or "not enough evidence"
            lines.append(f"| {item['layer']} | {item['signal']} | {item['confidence']} | {item['readout']} | {examples} |")
        lines.extend([
            "",
            "## Relationship Radar",
            f"- Active / Passive: {radar['active_passive']}",
            f"- I / E tendency: {radar['ie_tendency']}",
            f"- Warm / Guarded: {radar['warm_guarded']}",
            f"- Friend or Flirt: {radar['friend_or_flirt']}",
            f"- Slow-burn / Fishing: {radar['slow_burn_or_fishing']}",
            f"- Material risk: {radar['material_risk']}",
            "",
            "## Training Playbook",
        ])
        playbook = report["coaching_playbook"]
        for item in playbook["next_best_moves"]:
            lines.append(f"- Next: {item}")
        for item in playbook["avoid"]:
            lines.append(f"- Avoid: {item}")
        for item in playbook["practice_drills"]:
            lines.append(f"- Drill: {item}")
        lines.extend([
            "",
            "## Validation And Limits",
        ])
        for item in validation["triple_check"]:
            lines.append(f"- Check: {item}")
        for item in report["limitations"]:
            lines.append(f"- Limit: {item}")
        return "\n".join(lines)

    def _style_readout(self, avg_len: float, question_ratio: float, phrases: List[str]) -> str:
        length = "短句快节奏" if avg_len <= 18 else "中长句表达"
        curiosity = "高探索" if question_ratio >= 0.45 else "低问题密度"
        flavor = "梗感明显" if phrases else "表达指纹不足"
        return f"{length} / {curiosity} / {flavor}"

    def _examples(self, rows: List[Dict[str, str]], pattern: re.Pattern[str], limit: int) -> List[str]:
        result = []
        for row in rows:
            content = row["content"].strip()
            if pattern.search(content):
                result.append(content[:80])
            if len(result) >= limit:
                break
        return result

    def _ratio(self, value: int | float, total: int | float) -> float:
        return float(value) / max(1.0, float(total))
