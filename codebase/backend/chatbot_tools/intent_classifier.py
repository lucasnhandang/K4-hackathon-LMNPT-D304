"""Intent classifier + slot extraction for the Discord student assistant.

Rule-based classifier that works without LLM calls.
Normalizes Vietnamese text, classifies intent, and extracts slots.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Vietnamese normalization
# ---------------------------------------------------------------------------

def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text: lowercase, remove diacritics, normalize whitespace."""
    text = text.lower().strip()
    # Replace đ -> d
    text = text.replace("đ", "d").replace("Đ", "d")
    # Remove diacritics
    normalized = unicodedata.normalize("NFD", text)
    no_marks = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    # Normalize whitespace and special chars
    no_marks = re.sub(r"\s+", " ", no_marks).strip()
    return no_marks


# ---------------------------------------------------------------------------
# Intent definitions
# ---------------------------------------------------------------------------

INTENTS = {
    # Greetings / chitchat
    "greeting": {
        "keywords": ["xin chao", "chao ban", "hello", "hi", "hey", "chao", "alo", "bot oi", "hey bot"],
        "patterns": [r"^(xin\s*)?chao\b", r"^hello\b", r"^\bhi\b", r"^\bhey\b", r"^alo\b"],
    },
    "thanks": {
        "keywords": ["cam on", "cam on ban", "thank", "thanks", "tks", "ok thanks", "hay qua"],
        "patterns": [r"cam\s*on", r"thank"],
    },
    "help": {
        "keywords": ["giup minh", "help", "huong dan", "cach su dung", "ban co the lam gi", "ban lam gi duoc"],
        "patterns": [r"giup\s*(toi|minh|em)", r"^help\b", r"cach\s*su\s*dung"],
    },

    # Deadline
    "ask_deadline": {
        "keywords": [
            "deadline", "dealine", "dead line", "dl", "han nop", "han chot",
            "nop bai", "nop khi nao", "bao gio nop", "het han", "khi nao nop"
        ],
        "patterns": [
            r"deadline", r"dealine", r"dead\s*line", r"\bdl\b", r"han\s*nop",
            r"han\s*chot", r"nop\s*bai", r"bao\s*gio\s*nop", r"het\s*han"
        ],
        "slots": {
            "assignment": [
                r"weekly\s*assignment\s*\d*",  # Capture "weekly assignment" or "weekly assignment 3"
                r"wa\s*\d*",
                r"bai\s*weekly\s*\d*",
                r"ai\s*log",
                r"demo\s*day",
                r"deliverable",
                r"source\s*code",
                r"pitch\s*deck",
                r"readme",
                r"wireframe",
                r"business\s*model",
            ],
            "module": [
                r"module\s*(\w+)",
                r"mon\s*(\w+)",
            ],
        },
    },

    # Events
    "ask_event_schedule": {
        "keywords": ["su kien", "lich hoc", "workshop", "office hour", "mentoring", "demo day", "khi nao co", "lich trinh"],
        "patterns": [
            r"su\s*kien", r"lich\s*hoc", r"workshop", r"office\s*hour",
            r"mentoring", r"demo\s*day", r"khi\s*nao\s*co", r"lich\s*trinh",
            r"buoi\s*hoc",
        ],
        "slots": {
            "event_name": [
                r"workshop",
                r"office\s*hour",
                r"mentoring",
                r"demo\s*day",
                r"stand\s*up",
                r"coaching",
            ],
        },
    },

    # Gates
    "ask_gate": {
        "keywords": ["gate", "checkpoint", "cp1", "cp2", "cp3", "dieu kien", "yeu cau"],
        "patterns": [
            r"\bgate\b", r"checkpoint", r"\bcp[1-4]\b", r"dieu\s*kien", r"yeu\s*cau",
        ],
        "slots": {
            "gate_name": [
                r"\bcp[1-4]\b",
                r"gate\s*(\d)",
                r"checkpoint\s*(\d)",
                r"final\s*gate",
            ],
        },
    },

    # Exam slots
    "ask_exam_slot": {
        "keywords": ["ca thi", "lich thi", "exam", " thi ", "phong thi", "review"],
        "patterns": [
            r"ca\s*thi", r"lich\s*thi", r"\bexam\b", r"phong\s*thi",
            r"final\s*review", r"review\s*\d",
        ],
        "slots": {
            "exam_name": [
                r"final\s*review",
                r"midterm",
                r"cp\s*review",
            ],
        },
    },

    # XP
    "ask_xp": {
        "keywords": ["xp", "diem", "hang", "level", "lv", "rank", "bao nhieu xp", "tich luy"],
        "patterns": [
            r"\bxp\b", r"\bdiem\b", r"\bhang\b", r"\blevel\b", r"\blv\d\b",
            r"bao\s*nhieu\s*xp", r"tich\s*luy", r"\brank\b",
        ],
        "slots": {
            "activity": [
                r"daily",
                r"weekly",
                r"submit",
                r"peer\s*review",
                r"gate",
                r"workshop",
                r"checkin",
            ],
        },
    },

    # Team / Mentor
    "ask_team_mentor": {
        "keywords": ["mentor", "team", "nhom", "gia su", "ho tro", "lien he"],
        "patterns": [
            r"\bmentor\b", r"\bteam\b", r"\bnhom\b", r"gia\s*su",
            r"ho\s*tro", r"lien\s*he", r"ai\s*la\s*mentor",
        ],
        "slots": {
            "team": [
                r"team\s*(\d+)",
                r"team\s*(\w+)",
                r"nhom\s*(\d+)",
            ],
        },
    },

    # Slash commands
    "ask_slash_command": {
        "keywords": ["lenh", "command", "slash", " /", "cach dung"],
        "patterns": [
            r"\/\w+",
            r"lenh\s*discord",
            r"command",
            r"cach\s*dung",
            r"slash\s*command",
        ],
        "slots": {
            "command": [
                r"(\/\w+)",
            ],
        },
    },

    # Out of scope / escalation
    "request_deadline_exception": {
        "keywords": ["gia han", "xin gia han", "muon gia han", "nop muon", "tre han", "extension"],
        "patterns": [
            r"gia\s*han", r"xin\s*gia\s*han", r"nop\s*muon", r"tre\s*han",
            r"extension",
        ],
    },

    "report_issue": {
        "keywords": ["loi", "bug", "loi khong", "khong hoat dong", "bi loi", "error"],
        "patterns": [
            r"\bloi\b", r"\bbug\b", r"khong\s*hoat\s*dong", r"bi\s*loi",
            r"error",
        ],
    },

    "report_harassment": {
        "keywords": ["quay roi", "quấy rối", "18+", "nội dung nhạy cảm", "pii", "thông tin ca nhan"],
        "patterns": [
            r"quay\s*roi", r"18\+", r"noi\d* dung\s*nha\s*cam", r"pii",
            r"thong\s*tin\s*ca\s*nhan",
        ],
    },

    # Prompt injection defense
    "reject_prompt_injection": {
        "keywords": ["ignore", "ignore previous", "system prompt", "developer", "api key"],
        "patterns": [
            r"ignore\s*(all|previous|previous\s*instructions)",
            r"system\s*prompt",
            r"developer\s*instructions",
            r"api\s*key",
            r"bỏ qua",
            r"ignore",
        ],
    },
}


# ---------------------------------------------------------------------------
# Intent + Slot extraction
# ---------------------------------------------------------------------------

@dataclass
class IntentResult:
    intent: str
    confidence: float
    slots: dict[str, Any] = field(default_factory=dict)
    normalized_query: str = ""


def classify_intent(message: str) -> IntentResult:
    """Classify user message intent and extract slots.

    Returns IntentResult with best matching intent, confidence score,
    and extracted slots.
    """
    normalized = normalize_vietnamese(message)

    best_intent = "unknown"
    best_score = 0.0
    best_slots: dict[str, Any] = {}

    for intent, config in INTENTS.items():
        score = 0.0
        slots: dict[str, Any] = {}

        # Check keywords (short keywords <=3 chars require word boundaries)
        keyword_matches = 0
        for kw in config["keywords"]:
            if len(kw) <= 3:
                if re.search(r"\b" + re.escape(kw) + r"\b", normalized):
                    keyword_matches += 1
            else:
                if kw in normalized:
                    keyword_matches += 1

        if keyword_matches:
            score += min(keyword_matches * 0.3, 0.6)

        # Check patterns
        pattern_matches = 0
        for pattern in config["patterns"]:
            match = re.search(pattern, normalized)
            if match:
                pattern_matches += 1
                score += 0.2

        # Extract slots
        if "slots" in config:
            for slot_name, slot_patterns in config["slots"].items():
                for pattern in slot_patterns:
                    match = re.search(pattern, normalized)
                    if match:
                        # Get the first captured group if available
                        if match.lastindex:
                            slots[slot_name] = match.group(1).strip()
                        else:
                            slots[slot_name] = match.group(0).strip()
                        break

        # Normalize score
        score = min(score, 1.0)

        if score > best_score:
            best_score = score
            best_intent = intent
            best_slots = slots

    # Special handling: if no intent matched, check for question patterns
    if best_score == 0.0:
        if "?" in message or any(w in normalized for w in ["bao gio", "bao nhieu", "o dau", "tai sao", "the nao"]):
            best_intent = "unknown_question"
            best_score = 0.3

    # Greeting/thanks get high confidence if matched
    if best_intent in ("greeting", "thanks") and best_score > 0:
        best_score = max(best_score, 0.9)

    return IntentResult(
        intent=best_intent,
        confidence=round(best_score, 2),
        slots=best_slots,
        normalized_query=normalized,
    )
