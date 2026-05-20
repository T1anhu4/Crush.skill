"""
Multi-format Chat Record Import Pipeline.

Supported formats:
- WeChat exports (WeChatMsg / 留痕 / PyWxDump)
- WhatsApp .txt exports
- QQ chat exports
- Plain text transcripts (pasted conversations)
- JSON/CSV structured imports

Pipeline:
Raw chat → Clean → Segment → Analyze → Reconstruct Persona + State
"""
from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ChatMessage:
    """Normalized chat message."""
    timestamp: str = ""
    sender: str = ""  # "self" or "other"
    content: str = ""
    original_line: str = ""


@dataclass
class ChatImportResult:
    """Output of the chat import pipeline."""
    total_messages: int = 0
    date_range: Tuple[str, str] = ("", "")
    message_frequency: Dict[str, int] = field(default_factory=dict)  # day → count
    avg_message_length: float = 0.0
    avg_reply_time_minutes: float = 0.0

    # Inferred traits
    inferred_archetype: str = "experience"
    inferred_attachment: str = "Secure"
    inferred_mbti: str = "ENFP"
    inferred_love_language: str = "words_of_affirmation"
    inferred_big_five: Dict[str, float] = field(default_factory=lambda: {
        "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
        "agreeableness": 0.5, "neuroticism": 0.5,
    })

    # Speech fingerprint
    signature_phrases: List[str] = field(default_factory=list)
    filler_words: List[str] = field(default_factory=list)
    emoji_style: str = "moderate"
    emoji_favorites: List[str] = field(default_factory=list)
    sentence_structure: str = "casual"
    humor_style: str = "dry"

    # Relationship signals
    relationship_phase: str = "talking"
    sentiment_trend: str = "stable"  # improving | declining | stable | volatile
    key_topics: List[str] = field(default_factory=list)
    emotional_rhythm: Dict[str, Any] = field(default_factory=dict)

    # State estimation
    estimated_favorability: float = 30.0
    estimated_tension: float = 20.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_messages": self.total_messages,
            "date_range": list(self.date_range),
            "message_frequency": self.message_frequency,
            "avg_message_length": self.avg_message_length,
            "avg_reply_time_minutes": self.avg_reply_time_minutes,
            "inferred_archetype": self.inferred_archetype,
            "inferred_attachment": self.inferred_attachment,
            "inferred_mbti": self.inferred_mbti,
            "inferred_love_language": self.inferred_love_language,
            "inferred_big_five": self.inferred_big_five,
            "signature_phrases": self.signature_phrases,
            "filler_words": self.filler_words,
            "emoji_style": self.emoji_style,
            "emoji_favorites": self.emoji_favorites,
            "sentence_structure": self.sentence_structure,
            "humor_style": self.humor_style,
            "relationship_phase": self.relationship_phase,
            "sentiment_trend": self.sentiment_trend,
            "key_topics": self.key_topics,
            "estimated_favorability": self.estimated_favorability,
            "estimated_tension": self.estimated_tension,
        }


# ── Format Detectors and Parsers ─────────────────────────────────

class ChatImporter:
    """Main import engine that handles multiple formats."""

    def __init__(self):
        self.messages: List[ChatMessage] = []

    def detect_and_parse(self, text: str) -> List[ChatMessage]:
        """Auto-detect format and parse."""
        text = text.strip()
        if not text:
            return []

        # Try WeChat format first (most common)
        if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', text[:500]):
            return self._parse_wechat(text)

        # Try WhatsApp format
        if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}[,，]\s*\d{1,2}:\d{2}\s*[-–—]', text[:500]):
            return self._parse_whatsapp(text)

        # Try CSV/structured
        if text.startswith(("sender,", "timestamp,", "role,", "name,")):
            return self._parse_csv(text)

        # Fallback: generic conversation
        return self._parse_generic(text)

    def _parse_wechat(self, text: str) -> List[ChatMessage]:
        """Parse WeChat exported format."""
        messages = []
        # Pattern: 2024-01-15 14:30:25 昵称\n消息内容
        # or: 2024年1月15日 14:30 昵称：消息内容
        patterns = [
            re.compile(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)(?:\n|：|:)(.*)'),
            re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2})\s+(.+?)[：:](.*)'),
        ]

        # Try to identify the two participants
        name_counts: Counter = Counter()

        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith(("====", "---", "消息分组")):
                continue
            for pat in patterns:
                m = pat.match(line)
                if m:
                    timestamp, sender, content = m.group(1), m.group(2).strip(), m.group(3).strip()
                    name_counts[sender] += 1
                    messages.append(ChatMessage(
                        timestamp=timestamp, sender=sender, content=content, original_line=line,
                    ))
                    break

        # Heuristic: most frequent speaker is "other", second is "self"
        if len(name_counts) >= 2:
            top_two = name_counts.most_common(2)
            other_name = top_two[0][0]
            for msg in messages:
                msg.sender = "other" if msg.sender == other_name else "self"
        else:
            for msg in messages:
                msg.sender = "other"

        return messages

    def _parse_whatsapp(self, text: str) -> List[ChatMessage]:
        """Parse WhatsApp exported .txt format."""
        messages = []
        pat = re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4}[,，]\s*\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*(.+?):\s*(.*)')

        name_counts: Counter = Counter()
        for line in text.split("\n"):
            m = pat.match(line.strip())
            if m:
                timestamp, sender, content = m.group(1), m.group(2).strip(), m.group(3).strip()
                name_counts[sender] += 1
                messages.append(ChatMessage(
                    timestamp=timestamp, sender=sender, content=content, original_line=line,
                ))

        if len(name_counts) >= 2:
            top_two = name_counts.most_common(2)
            for msg in messages:
                msg.sender = "other" if msg.sender == top_two[0][0] else "self"

        return messages

    def _parse_csv(self, text: str) -> List[ChatMessage]:
        """Parse CSV formatted chat."""
        messages = []
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            messages.append(ChatMessage(
                timestamp=row.get("timestamp", row.get("time", "")),
                sender=row.get("sender", row.get("role", "other")),
                content=row.get("content", row.get("message", row.get("text", ""))),
            ))
        return messages

    def _parse_generic(self, text: str) -> List[ChatMessage]:
        """Parse generic conversation: alternating lines, "A: ... B: ..." """
        messages = []
        pat = re.compile(r'^(.+?)[：:]\s*(.+)')

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        speaker_map: Dict[str, str] = {}
        speaker_idx = 0

        for line in lines:
            m = pat.match(line)
            if m:
                name, content = m.group(1).strip(), m.group(2).strip()
                if name not in speaker_map:
                    speaker_map[name] = "other" if speaker_idx == 0 else "self"
                    speaker_idx += 1
                messages.append(ChatMessage(
                    sender=speaker_map[name], content=content, original_line=line,
                ))
        return messages

    def analyze(self, messages: List[ChatMessage]) -> ChatImportResult:
        """Run full analysis pipeline on parsed messages."""
        if not messages:
            return ChatImportResult()

        result = ChatImportResult()
        result.total_messages = len(messages)

        # Other-person messages only
        other_msgs = [m for m in messages if m.sender == "other"]
        self_msgs = [m for m in messages if m.sender == "self"]
        all_other_text = " ".join(m.content for m in other_msgs)

        # ── Date range & frequency ──
        times = [m.timestamp for m in messages if m.timestamp]
        if times:
            result.date_range = (times[0], times[-1])
            for t in times:
                day = t[:10] if len(t) >= 10 else t
                result.message_frequency[day] = result.message_frequency.get(day, 0) + 1

        # ── Average message length ──
        result.avg_message_length = sum(len(m.content) for m in other_msgs) / max(1, len(other_msgs))

        # ── Average reply time ──
        result.avg_reply_time_minutes = self._estimate_reply_time(messages)

        # ── Infer archetype ──
        result.inferred_archetype = self._infer_archetype(other_msgs, all_other_text)

        # ── Infer attachment style ──
        result.inferred_attachment = self._infer_attachment(other_msgs, all_other_text)

        # ── Infer MBTI ──
        result.inferred_mbti = self._infer_mbti(other_msgs, all_other_text)

        # ── Infer love language ──
        result.inferred_love_language = self._infer_love_language(other_msgs, all_other_text)

        # ── Infer Big Five ──
        result.inferred_big_five = self._infer_big_five(other_msgs, all_other_text)

        # ── Speech fingerprint ──
        result.signature_phrases = self._extract_signature_phrases(other_msgs)
        result.filler_words = self._extract_filler_words(other_msgs)
        result.emoji_style, result.emoji_favorites = self._analyze_emoji_usage(other_msgs)
        result.sentence_structure = self._analyze_sentence_structure(other_msgs)
        result.humor_style = self._detect_humor_style(other_msgs)

        # ── Relationship phase ──
        result.relationship_phase = self._detect_relationship_phase(other_msgs, self_msgs)

        # ── Sentiment trend ──
        result.sentiment_trend = self._analyze_sentiment_trend(other_msgs)

        # ── Key topics ──
        result.key_topics = self._extract_key_topics(messages)

        # ── State estimation ──
        result.estimated_favorability = self._estimate_favorability(other_msgs)
        result.estimated_tension = self._estimate_tension(other_msgs)

        return result

    # ── Inference Methods ─────────────────────────────────────────

    def _infer_archetype(self, msgs: List[ChatMessage], text: str) -> str:
        scores = {
            "emotional": len(re.findall(r"真诚|情绪|共鸣|理解|在乎|灵魂|走心|感受|情绪价值", text)),
            "security": len(re.findall(r"稳定|未来|计划|责任|靠谱|长期|安全感|踏实|安心", text)),
            "experience": len(re.findall(r"新鲜|刺激|开心|好玩|氛围|体验|情绪|快乐|有趣", text)),
            "value": len(re.findall(r"价值|条件|资源|能力|上进|现实|匹配|优秀|厉害", text)),
            "passive": len(re.findall(r"随缘|佛系|懒得|无所谓|顺其自然|慢热|都好|随便", text)),
        }
        return max(scores, key=scores.get)

    def _infer_attachment(self, msgs: List[ChatMessage], text: str) -> str:
        scores = {
            "Secure": len(re.findall(r"稳定|沟通|边界|信任|慢慢|理解|表达|坦诚", text)),
            "Anxious": len(re.findall(r"焦虑|患得患失|怕失去|秒回|不安|你怎么|为什么不|离开", text)),
            "Dismissive_Avoidant": len(re.findall(r"独立|距离|不想被管|别管|自己|需要空间|冷淡", text)),
            "Fearful_Avoidant": len(re.findall(r"忽冷忽热|拉扯|矛盾|靠近又害怕|不确定|纠结", text)),
        }
        max_score = max(scores.values())
        if max_score == 0:
            return "Secure"
        return max(scores, key=scores.get)

    def _infer_mbti(self, msgs: List[ChatMessage], text: str) -> str:
        e_score = len(re.findall(r"社交|朋友|聚会|一起|见面|热闹|出去玩", text))
        i_score = len(re.findall(r"独处|安静|一个人|宅|宅家|不想出门|累|内向", text))
        n_score = len(re.findall(r"想象|可能|未来|如果|也许|抽象|概念|新", text))
        s_score = len(re.findall(r"具体|实际|经验|以前|知道|现实|事实|清楚", text))
        t_score = len(re.findall(r"逻辑|道理|应该|分析|正确|合理|客观|对错", text))
        f_score = len(re.findall(r"感受|感觉|情绪|共情|在乎|温暖|喜欢|讨厌", text))
        j_score = len(re.findall(r"计划|安排|提前|准时|确定|要|得|必须", text))
        p_score = len(re.findall(r"随便|到时候|看情况|再说|灵活|随性|无所谓", text))

        letters = []
        letters.append("E" if e_score > i_score else "I")
        letters.append("N" if n_score > s_score else "S")
        letters.append("T" if t_score > f_score else "F")
        letters.append("J" if j_score > p_score else "P")
        return "".join(letters)

    def _infer_love_language(self, msgs: List[ChatMessage], text: str) -> str:
        scores = {
            "words_of_affirmation": len(re.findall(r"爱|喜欢|想你|在乎|重要|特别|唯一|最|永远", text)),
            "quality_time": len(re.findall(r"一起|见面|陪|见面|待在一起|聊天|散步|吃饭", text)),
            "acts_of_service": len(re.findall(r"帮|做|准备|带|送|接|照顾|操心", text)),
            "physical_touch": len(re.findall(r"抱|牵手|亲|贴贴|靠近|碰到|拥抱|拉着", text)),
            "receiving_gifts": len(re.findall(r"送|礼物|惊喜|想起我|纪念|买|存着", text)),
        }
        return max(scores, key=scores.get)

    def _infer_big_five(self, msgs: List[ChatMessage], text: str) -> Dict[str, float]:
        total = len(msgs) + 1
        return {
            "openness": min(1.0, len(re.findall(r"新鲜|新|尝试|好奇|艺术|音乐|电影|书|旅行|探索", text)) / total * 8),
            "conscientiousness": min(1.0, len(re.findall(r"计划|准时|安排|整理|完成|条理|责任|规律", text)) / total * 8),
            "extraversion": min(1.0, len(re.findall(r"朋友|聚会|社交|开心|热闹|玩|哈哈|一起", text)) / total * 8),
            "agreeableness": min(1.0, len(re.findall(r"理解|包容|体谅|没事|算了|没关系|听你的|好的", text)) / total * 8),
            "neuroticism": min(1.0, len(re.findall(r"焦虑|担心|烦|压力|累|崩溃|难受|失眠|不安", text)) / total * 8),
        }

    def _extract_signature_phrases(self, msgs: List[ChatMessage]) -> List[str]:
        """Find unique, repeated phrases that characterize this person."""
        word_counter: Counter = Counter()
        for msg in msgs:
            # Extract 2-4 character phrases
            content = msg.content
            for phrase_len in [2, 3, 4]:
                for i in range(len(content) - phrase_len + 1):
                    phrase = content[i:i+phrase_len]
                    if re.match(r'^[一-鿿]+$', phrase):
                        word_counter[phrase] += 1

        # Filter: must appear at least 3 times, not be common words
        common = {"哈哈哈", "不知道", "我觉得", "是不是", "可以的", "就是说", "哈哈哈", "嗯嗯嗯"}
        phrases = [(p, c) for p, c in word_counter.most_common(30)
                   if c >= 3 and p not in common]
        return [p for p, _ in phrases[:8]]

    def _extract_filler_words(self, msgs: List[ChatMessage]) -> List[str]:
        filler_candidates = ["就", "然后", "那个", "嗯", "啊", "哦", "吧", "嘛", "呀", "啦", "就是说", "反正", "其实", "感觉"]
        counter: Counter = Counter()
        for msg in msgs:
            for fw in filler_candidates:
                if fw in msg.content:
                    counter[fw] += 1
        return [w for w, _ in counter.most_common(5)]

    def _analyze_emoji_usage(self, msgs: List[ChatMessage]) -> Tuple[str, List[str]]:
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]|[☀-➿]|[︀-﻿]')
        emoji_counter: Counter = Counter()
        msg_with_emoji = 0
        for msg in msgs:
            emojis = emoji_pattern.findall(msg.content)
            if emojis:
                msg_with_emoji += 1
                for e in emojis:
                    emoji_counter[e] += 1

        ratio = msg_with_emoji / max(1, len(msgs))
        style = "heavy" if ratio > 0.6 else "moderate" if ratio > 0.3 else "minimal" if ratio > 0.1 else "none"
        return style, [e for e, _ in emoji_counter.most_common(6)]

    def _analyze_sentence_structure(self, msgs: List[ChatMessage]) -> str:
        avg_len = sum(len(m.content) for m in msgs) / max(1, len(msgs))
        if avg_len < 8:
            return "fragmented"
        elif avg_len < 20:
            return "casual"
        elif avg_len < 50:
            return "verbose"
        return "formal"

    def _detect_humor_style(self, msgs: List[ChatMessage]) -> str:
        text = " ".join(m.content for m in msgs)
        scores = {
            "sarcastic": len(re.findall(r"呵呵|行吧|嗯嗯|可以的|牛逼|厉害|真行", text)),
            "goofy": len(re.findall(r"哈哈|笑死|xswl|233+|hhhh+|绝了|笑不活", text)),
            "self-deprecating": len(re.findall(r"我不行|我是废物|我好菜|我太|我配|我算什么", text)),
            "dry": len(re.findall(r"确实|嗯|哦|知道了|好|行|那没事了", text)),
        }
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "dry"

    def _detect_relationship_phase(self, other_msgs: List[ChatMessage], self_msgs: List[ChatMessage]) -> str:
        total = len(other_msgs) + len(self_msgs)
        if total < 20:
            return "strangers"
        if total < 100:
            return "talking"
        if total < 500:
            return "dating"
        return "committed"

    def _analyze_sentiment_trend(self, msgs: List[ChatMessage]) -> str:
        if len(msgs) < 20:
            return "stable"
        # Split into quartiles and compare early vs late
        quartile = len(msgs) // 4
        early = msgs[:quartile]
        late = msgs[-quartile:]

        early_pos = sum(1 for m in early if any(w in m.content for w in POSITIVE_WORDS_SET))
        late_pos = sum(1 for m in late if any(w in m.content for w in POSITIVE_WORDS_SET))

        diff = late_pos - early_pos
        if diff > 5:
            return "improving"
        if diff < -5:
            return "declining"
        if abs(diff) <= 2 and early_pos > 2 and late_pos > 2:
            return "stable"
        return "volatile"

    def _extract_key_topics(self, msgs: List[ChatMessage]) -> List[str]:
        topic_keywords = ["工作", "学习", "家人", "朋友", "旅行", "美食", "电影", "音乐", "运动", "游戏", "未来", "感情", "前任", "钱"]
        counter: Counter = Counter()
        for msg in msgs:
            for kw in topic_keywords:
                if kw in msg.content:
                    counter[kw] += 1
        return [k for k, _ in counter.most_common(5)]

    def _estimate_favorability(self, msgs: List[ChatMessage]) -> float:
        if not msgs:
            return 30.0
        text = " ".join(m.content for m in msgs)
        pos = len(re.findall(r"开心|喜欢|想你|期待|见面|哈哈哈|晚安|早安|想你|在乎", text))
        neg = len(re.findall(r"算了|随便|无所谓|烦|冷淡|别烦|走开|不想|不理", text))
        total = max(1, pos + neg)
        base = (pos - neg) / total * 50 + 40
        # Adjust by message volume trend
        return max(5.0, min(80.0, base + min(15, len(msgs) / 50)))

    def _estimate_tension(self, msgs: List[ChatMessage]) -> float:
        if not msgs:
            return 20.0
        text = " ".join(m.content for m in msgs)
        tension_signals = len(re.findall(r"吵|怼|生气|冷战|不爽|呵呵|随便你|你爱怎么|无所谓", text))
        return max(5.0, min(70.0, tension_signals * 8.0 + 10.0))

    def _estimate_reply_time(self, msgs: List[ChatMessage]) -> float:
        """Estimate average reply time in minutes from alternating patterns."""
        if len(msgs) < 4:
            return 10.0
        # Rough heuristic based on message density
        other_count = sum(1 for m in msgs if m.sender == "other")
        if other_count < 2:
            return 10.0
        # More messages per day = faster replies
        days = max(1, len(set(m.timestamp[:10] for m in msgs if m.timestamp and len(m.timestamp) >= 10)))
        msgs_per_day = len(msgs) / days
        if msgs_per_day > 50:
            return 3.0
        if msgs_per_day > 20:
            return 15.0
        if msgs_per_day > 5:
            return 60.0
        return 180.0


# Shared POSITIVE_WORDS_SET for sentiment analysis
POSITIVE_WORDS_SET = {"开心", "想你", "喜欢", "期待", "见面", "哈哈哈", "晚安", "早安", "想你", "在乎", "甜甜", "美好"}
