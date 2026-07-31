"""Deterministic commands for explicit user-profile memory."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal


MemoryAction = Literal["remember_name", "recall_name", "forget_name"]


@dataclass(frozen=True)
class MemoryCommand:
    action: MemoryAction
    value: str | None = None
    remainder: str | None = None


REMEMBER_PATTERNS = (
    re.compile(
        r"(?:^|\b)(?:tôi|mình|em)\s+tên(?:\s+là)?\s+(.+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:^|\b)(?:hãy\s+)?gọi\s+(?:tôi|mình|em)\s+là\s+(.+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:đổi|sửa|cập\s+nhật)(?:\s+lại)?\s+"
        r"(?:tên\s+(?:của\s+)?)?(?:tôi|mình|em)\s+"
        r"(?:tên\s+)?(?:là|thành)\s+(.+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:đổi|sửa|cập\s+nhật)(?:\s+lại)?\s+"
        r"tên\s+(?:của\s+)?(?:tôi|mình|em)\s+thành\s+(.+)$",
        re.IGNORECASE,
    ),
)
NAME_SUFFIX_PATTERN = re.compile(
    r"(?:[,;.!?]\s*|\s+)(?:"
    r"từ\s+(?:giờ|nay)|"
    r"sau\s+này|"
    r"hãy\s+gọi|"
    r"cứ\s+gọi|"
    r"gọi\s+(?:tôi|mình|em)|"
    r"bạn\s+(?:hãy|có\s+thể)\b"
    r")\b.*$",
    re.IGNORECASE,
)
POLITE_SUFFIX_PATTERN = re.compile(
    r"\s+(?:nhé|nha|ạ|nè)[.!?]*$",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    lowered = text.casefold().replace("đ", "d")
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    words = re.sub(r"[^a-z0-9]+", " ", without_marks)
    return " ".join(words.split())


def _valid_name(value: str) -> bool:
    if not 1 <= len(value) <= 50:
        return False
    if len(value.split()) > 6:
        return False
    return all(
        character.isalpha() or character in {" ", "-", "'"}
        for character in value
    )


def is_capabilities_question(message: str) -> bool:
    normalized = _normalize(message)
    patterns = (
        r"\b(?:ban|bot) (?:co the )?lam (?:duoc )?(?:nhung )?(?:gi|j)\b",
        r"\b(?:ban|bot) (?:co the )?giup (?:duoc )?(?:nhung )?(?:gi|j)\b",
        r"\b(?:ban|bot) co (?:nhung )?(?:chuc nang|kha nang) (?:gi|j)\b",
        r"\b(?:ban|bot) co (?:nhung )?thong tin (?:gi|j)\b",
        r"\b(?:ban|bot) (?:co the )?(?:biet|tra loi) "
        r"(?:duoc )?(?:nhung )?(?:gi|j)\b",
        r"\b(?:ban|bot) (?:co the )?ho tro "
        r"(?:duoc )?(?:nhung )?(?:gi|j)\b",
        r"\b(?:ban|bot) duoc cung cap (?:nhung )?thong tin (?:gi|j)\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def parse_memory_command(message: str) -> MemoryCommand | None:
    normalized = _normalize(message)

    recall_patterns = (
        r"\b(?:toi|minh|em) ten (?:la )?(?:gi|j)\b",
        r"\bten (?:cua )?(?:toi|minh|em) (?:la )?(?:gi|j)\b",
        r"\bban (?:co )?nho ten (?:toi|minh|em) (?:khong|ko|k)\b",
    )
    if any(re.search(pattern, normalized) for pattern in recall_patterns):
        return MemoryCommand(action="recall_name")

    forget_patterns = (
        r"^(?:hay )?(?:quen|xoa) ten (?:cua )?(?:toi|minh|em)$",
        r"^(?:dung|khong) nho ten (?:cua )?(?:toi|minh|em) nua$",
    )
    if any(re.search(pattern, normalized) for pattern in forget_patterns):
        return MemoryCommand(action="forget_name")

    cleaned = message.strip()
    for pattern in REMEMBER_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        raw_candidate = match.group(1)
        suffix_match = NAME_SUFFIX_PATTERN.search(raw_candidate)
        remainder = None
        if suffix_match:
            remainder = raw_candidate[suffix_match.start():].strip(" ,;.!?")
            candidate = raw_candidate[:suffix_match.start()]
        else:
            candidate = raw_candidate
        candidate = POLITE_SUFFIX_PATTERN.sub("", candidate)
        name = candidate.strip(" .!?")
        if _valid_name(name):
            return MemoryCommand(
                action="remember_name",
                value=name,
                remainder=remainder,
            )
        return None
    return None
