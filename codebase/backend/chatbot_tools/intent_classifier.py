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

_CHAT_PHRASE_ALIASES = (
    (r"\bbao\s+h\b", "bao gio"),
    (r"\bchung\s+nao\b", "khi nao"),
    (r"\bkhi\s+mo\b", "khi nao"),
    (r"\bmentor\s+duty\b", "mentoring duty"),
)

REQUESTED_FACT_PATTERNS = {
    "deadline": (
        r"\bdeadline\b|\bdealine\b|\bdead\s*line\b|\bdl\b|"
        r"\bhan\s*(?:nop|chot|gate)\b|\bbao\s*gio\b|\bkhi\s*nao\b|"
        r"\bluc\s*nao\b|"
        r"\bhet\s*han\b|\bcon\s*(?:bao|may)\s*nhieu?\s*ngay\b|"
        r"\bcon\s*may\s*ngay\b|"
        r"\b(?:nop.*\bbh\b|\bbh\b.*nop)\b"
    ),
    "requirements": (
        r"\b(?:yeu\s*cau|dieu\s*kien|can\s+nhung?\s*gi|can\s*gi|"
        r"can\s+nop\s+gi|nop\s+nhung?\s*gi|nop\s+gi)\b"
    ),
    "submission_method": (
        r"\b(?:nop\s*o\s*dau|cach\s*nop|nop\s*the\s*nao|"
        r"kenh\s*nop|nop\s*bang\s*gi|submit\s*o\s*dau)\b"
    ),
    "grading": (
        r"\b(?:cham\s*diem|tinh\s*diem|bao\s*nhieu\s*diem|"
        r"grading|rubric)\b"
    ),
    "general": r"\b(?:thong\s*tin|noi\s*dung|tong\s*quan)\b",
}


def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text, including a small safe chat-language layer."""
    text = text.lower().strip()
    # Replace đ -> d
    text = text.replace("đ", "d").replace("Đ", "d")
    # Remove diacritics
    normalized = unicodedata.normalize("NFD", text)
    no_marks = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    # Normalize whitespace and special chars
    no_marks = re.sub(r"\s+", " ", no_marks).strip()
    for pattern, replacement in _CHAT_PHRASE_ALIASES:
        no_marks = re.sub(pattern, replacement, no_marks)
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
        "keywords": ["giup minh", "help", "huong dan", "cach su dung", "ban co the lam gi", "ban lam gi duoc", "giup gi", "co the giup gi"],
        "patterns": [r"giup\s*(toi|minh|em|gi)", r"^help\b", r"cach\s*su\s*dung", r"lam\s*(duoc\s*)?gi", r"giup\s*gi"],
    },
    "ask_datetime": {
        "keywords": [
            "may gio", "thu may", "ngay may", "bay gio",
            "gio hien tai", "ngay bao nhieu", "hom nay ngay bao nhieu", "hom nay thu may", "ngay gio"
        ],
        "patterns": [
            r"hom\s*nay\s*(la\s*)?(ngay|thu)\s*may",
            r"bay\s*gio\s*(la\s*)?may\s*gio",
            r"gio\s*hien\s*tai",
            r"hom\s*nay\s*ngay\s*bao\s*nhieu",
            r"hom\s*nay\s*thu\s*may",
            r"ngay\s*gio\s*hom\s*nay",
            r"ngay\s*may\s*hom\s*nay",
        ],
    },
    "out_of_domain": {
        "keywords": [
            "thoi tiet", "gia vang", "chung khoan", "crypto", "bitcoin",
            "nhiet do", "bong da", "tin tuc", "nau an", "am thuc", "du lich", "mua ban"
        ],
        "patterns": [
            r"thoi\s*tiet", r"gia\s*vang", r"chung\s*khoan", r"nhiet\s*do",
            r"bong\s*da", r"tin\s*tuc", r"nau\s*an", r"du\s*lich"
        ],
    },

    # Core course-support policies and resources
    "ask_attendance_policy": {
        "keywords": ["chuyen can", "nghi hoc", "vang hoc", "nghi toi da", "duoc nghi"],
        "patterns": [
            r"chuyen\s*can", r"nghi\s*(hoc|toi\s*da|may|bao\s*nhieu)",
            r"vang\s*(hoc|mat)", r"duoc\s*nghi",
        ],
    },
    "ask_online_learning_availability": {
        "keywords": ["hoc online", "hoc truc tiep", "hoc offline", "hinh thuc hoc"],
        "patterns": [
            r"hoc\s*(online|offline|truc\s*tiep)",
            r"(online|offline|truc\s*tiep)\s*(duoc\s*)?(khong|ko|k)?",
            r"hinh\s*thuc\s*hoc",
        ],
    },
    "ask_laptop_requirements": {
        "keywords": ["cau hinh laptop", "cau hinh may", "cpu", "ram", "ssd", "may tinh"],
        "patterns": [
            r"cau\s*hinh\s*(laptop|may)", r"\bcpu\b", r"\bram\b", r"\bssd\b",
            r"(laptop|may\s*tinh).*(toi\s*thieu|yeu\s*cau|can)",
        ],
    },
    "ask_submission_channel": {
        "keywords": ["nop o dau", "nop bao cao", "kenh nop", "noi nop", "submission"],
        "patterns": [
            r"nop.*o\s*dau", r"(kenh|noi)\s*nop", r"nop\s*bao\s*cao",
            r"submission",
        ],
    },
    "ask_learning_material": {
        "keywords": ["tai lieu", "slide", "codelab", "jira", "syllabus", "bai setup"],
        "patterns": [
            r"tai\s*lieu", r"\bslide\b", r"\bcodelabs?\b", r"\bjira\b",
            r"\bsyllabus\b", r"bai\s*setup",
        ],
    },
    "ask_team_naming": {
        "keywords": ["doi ten team", "dat ten team", "dat ten nhom", "ten nhom", "dat ten"],
        "patterns": [
            r"(doi|dat)\s*ten\s*(team|nhom)",
            r"ten\s*(team|nhom).*(o\s*dau|the\s*nao)",
            r"nhom.{0,30}dat\s*ten",
            r"dat\s*ten.{0,20}(nhom|team|o\s*dau)",
        ],
    },
    "ask_topic_availability": {
        "keywords": ["kiem tra de tai", "de tai da co", "de tai co nhom"],
        "patterns": [
            r"kiem\s*tra.*de\s*tai", r"de\s*tai.*(da\s*co|co\s*nhom|nhom\s*nao)",
        ],
    },
    "ask_holiday_schedule": {
        "keywords": ["nghi tet", "tet", "lich nghi", "nghi le", "nghi bao nhieu ngay"],
        "patterns": [
            r"nghi\s*(tet|le)", r"lich\s*nghi",
            r"nghi.*bao\s*nhieu\s*ngay",
        ],
    },
    "ask_scholarship_info": {
        "keywords": ["hoc bong", "du hoc"],
        "patterns": [
            r"hoc\s*bong", r"du\s*hoc",
        ],
    },

    # Deadline
    "ask_deadline": {
        "keywords": [
            "deadline", "dealine", "dead line", "dl", "han nop", "han chot",
            "nop bai", "nop khi nao", "bao gio nop", "het han", "khi nao nop",
            "nop luc nao", "con may ngay",
        ],
        "patterns": [
            r"deadline", r"dealine", r"dead\s*line", r"\bdl\b", r"han\s*nop",
            r"han\s*chot", r"nop\s*bai", r"bao\s*gio\s*nop", r"het\s*han",
            r"nop\s*(?:bao\s*gio|khi\s*nao|luc\s*nao)",
            r"(?:bao\s*gio|khi\s*nao|luc\s*nao)\s*nop",
            r"con\s*may\s*ngay",
        ],
        "slots": {
            "assignment": [
                r"weekly\s*assignment\s*\d*",  # Capture "weekly assignment" or "weekly assignment 3"
                r"wa\s*\d*",
                r"bai\s*weekly\s*\d*",
                r"\/?weekly\s*(?:submit|report)",
                r"bao\s*cao\s*tuan",
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
        "keywords": [
            "xp", "diem", "hang", "level", "lv", "rank", "daily",
            "bao nhieu xp", "tich luy",
        ],
        "patterns": [
            r"\bxp\b", r"\bdiem\b", r"\bhang\b", r"\blevel\b", r"\blv\d\b",
            r"bao\s*nhieu\s*xp", r"tich\s*luy", r"\brank\b", r"\bdaily\b",
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
                r"rank",
                r"tong\s*diem\s*kinh\s*nghiem",
                r"mentor(?:ing)?\s*duty",
            ],
        },
    },

    # Team / Mentor
    "ask_team_mentor": {
        "keywords": ["mentor", "gia su", "team cua toi", "nhom cua toi", "lien he mentor"],
        "patterns": [
            r"\bmentor\b", r"gia\s*su", r"ai\s*la\s*mentor",
            r"(team|nhom)\s*(cua\s*)?(toi|minh|em)",
            r"(team|nhom)\s*\d+",
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
        "keywords": ["lenh", "command", "slash", " /", "cach dung", "bao cao tuan"],
        "patterns": [
            r"\/\w+",
            r"lenh\s*discord",
            r"lenh.*bao\s*cao\s*tuan",
            r"command",
            r"cach\s*dung",
            r"slash\s*command",
        ],
        "slots": {
            "command": [
                r"(\/\w+)",
                r"(bao\s*cao\s*tuan)",
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
    "request_leave_of_absence": {
        "keywords": ["bao luu", "xin nghi khoa", "tam dung khoa", "nghi hoc dai han"],
        "patterns": [
            r"bao\s*luu", r"xin\s*nghi\s*khoa", r"tam\s*dung\s*khoa",
            r"nghi\s*hoc\s*dai\s*han",
        ],
    },
    "request_grade_review": {
        "keywords": ["cham lai", "phuc khao", "sua diem", "xem lai diem"],
        "patterns": [
            r"cham\s*lai", r"phuc\s*khao", r"sua\s*diem", r"xem\s*lai\s*diem",
        ],
    },
    "request_team_change": {
        "keywords": ["doi nhom", "join nhom khac", "doi de tai"],
        "patterns": [
            r"(doi|chuyen|join).*(nhom|team)",
            r"(nhom|team).*(doi|chuyen|join)",
            r"doi\s*de\s*tai",
        ],
    },

    "report_issue": {
        "keywords": ["loi", "bug", "loi khong", "khong hoat dong", "bi loi", "error"],
        "patterns": [
            r"\bloi\b", r"\bbug\b", r"khong\s*hoat\s*dong", r"bi\s*loi",
            r"error",
        ],
        "slots": {
            "operation": [
                r"dang\s*nhap", r"login", r"nop\s*bai", r"submit",
                r"tai\s*(file|slide|tai\s*lieu)", r"mo\s*(link|file|slide)",
                r"ket\s*noi\s*discord", r"chay\s*(code|app)",
            ],
            "error_code": [
                r"\b([45]\d{2})\b",
                r"(error\s*[\w-]+)",
            ],
            "platform": [
                r"\b(discord|vlearn|learnworlds|jira|github)\b",
            ],
        },
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
    "reject_answer_key_request": {
        "keywords": ["xin dap an", "cho dap an", "dap an bai kiem tra", "answer key"],
        "patterns": [
            r"(xin|cho|gui).*(dap\s*an|answer\s*key)",
            r"đap\s*an\s*bai\s*(kiem\s*tra|quiz)",
            r"dap\s*an\s*bai\s*(kiem\s*tra|quiz)",
        ],
    },
    "reject_do_assignment_for_user": {
        "keywords": [
            "lam bai ho", "code ho", "nop bai ho", "nop giup",
            "lam assignment ho", "submit ho",
        ],
        "patterns": [
            r"lam\s*(bai|assignment).*\bho\b",
            r"code\s*(bai\s*)?\bho\b",
            r"(nop|submit)\s*(bai\s*)?\bho\b",
            r"(nop|submit).*\bgiup\b",
        ],
    },
}


INTENT_PRIORITY = {
    "reject_prompt_injection": 100,
    "report_harassment": 95,
    "reject_answer_key_request": 90,
    "reject_do_assignment_for_user": 90,
    "request_deadline_exception": 85,
    "request_leave_of_absence": 85,
    "request_grade_review": 85,
    "request_team_change": 85,
    "report_issue": 80,
    "ask_team_naming": 60,
    "greeting": 10,
    "thanks": 10,
    "help": 10,
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
    best_priority = -1

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

        priority = INTENT_PRIORITY.get(intent, 50)
        if score > best_score or (score == best_score and score > 0 and priority > best_priority):
            best_score = score
            best_intent = intent
            best_slots = slots
            best_priority = priority

    # Special handling: if no intent matched, check for question patterns
    if best_score == 0.0:
        if "?" in message or any(w in normalized for w in ["bao gio", "bao nhieu", "o dau", "tai sao", "the nao"]):
            best_intent = "unknown_question"
            best_score = 0.3

    # Greeting/thanks get high confidence if matched
    if best_intent in ("greeting", "thanks") and best_score > 0:
        best_score = max(best_score, 0.9)

    # A gate/checkpoint is the subject, while deadline/requirements describe
    # the fact the student wants. Keep both dimensions instead of allowing the
    # deadline keyword to erase the gate entity (or vice versa).
    gate_anchor = re.search(
        r"\b(?:gate|checkpoint|cp\s*[1-4])\b",
        normalized,
    )
    if gate_anchor and best_intent in {
        "ask_gate",
        "ask_deadline",
        "ask_submission_channel",
        "unknown",
        "unknown_question",
    }:
        best_intent = "ask_gate"
        gate_match = re.search(
            r"\bcp\s*([1-4])\b|"
            r"\b(?:gate|checkpoint)\s*(?:so\s*)?([1-4])\b",
            normalized,
        )
        if gate_match:
            best_slots["gate_name"] = f"cp{gate_match.group(1) or gate_match.group(2)}"
        elif re.search(r"\bfinal(?:\s*gate)?\b|\bgate\s*cuoi\b", normalized):
            best_slots["gate_name"] = "final"

        for requested_fact, pattern in REQUESTED_FACT_PATTERNS.items():
            if re.search(pattern, normalized):
                best_slots["requested_fact"] = requested_fact
                break

    return IntentResult(
        intent=best_intent,
        confidence=round(best_score, 2),
        slots=best_slots,
        normalized_query=normalized,
    )
