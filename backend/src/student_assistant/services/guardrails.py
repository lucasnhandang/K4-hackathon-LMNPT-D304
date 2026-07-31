"""Deterministic input/output guardrails for the chat pipeline."""

import asyncio
import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic

from student_assistant.core.config import settings


EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?84|0)(?:[\s.\-]?\d){9,10}(?!\d)"
)
SECRET_PATTERNS = (
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{25,}\b"),
    re.compile(
        r"\b(?:discord[_ -]?bot[_ -]?token|gemini[_ -]?api[_ -]?key)"
        r"\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
)
INJECTION_PHRASES = (
    "boquahuongdan",
    "boquachidan",
    "ignorepreviousinstructions",
    "ignoresystemprompt",
    "revealsystemprompt",
    "insystemprompt",
    "showdeveloperprompt",
    "developerinstructions",
)


class GuardrailViolation(ValueError):
    """Base exception for rejected user input."""


class MessageTooLong(GuardrailViolation):
    pass


class SecretDetected(GuardrailViolation):
    pass


class PromptInjectionDetected(GuardrailViolation):
    pass


class RateLimitExceeded(GuardrailViolation):
    pass


@dataclass(frozen=True)
class SanitizedInput:
    raw: str
    redacted: str
    pii_types: tuple[str, ...]


def _normalized_for_rules(text: str) -> str:
    lowered = text.casefold().replace("đ", "d")
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return "".join(character for character in without_marks if character.isalnum())


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def redact_pii(text: str) -> str:
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)


def sanitize_input(text: str) -> SanitizedInput:
    cleaned = text.strip()
    if len(cleaned) > settings.max_message_characters:
        raise MessageTooLong(
            f"Tin nhắn vượt quá {settings.max_message_characters} ký tự."
        )
    if contains_secret(cleaned):
        raise SecretDetected(
            "Tin nhắn có vẻ chứa API key hoặc token. Hãy thu hồi key nếu đã lộ "
            "và không gửi secret qua Discord."
        )

    normalized = _normalized_for_rules(cleaned)
    if any(phrase in normalized for phrase in INJECTION_PHRASES):
        raise PromptInjectionDetected(
            "Mình không thể thực hiện yêu cầu thay đổi hoặc tiết lộ chỉ dẫn hệ thống."
        )

    pii_types: list[str] = []
    if EMAIL_PATTERN.search(cleaned):
        pii_types.append("email")
    if PHONE_PATTERN.search(cleaned):
        pii_types.append("phone")
    redacted = redact_pii(cleaned)
    return SanitizedInput(
        raw=cleaned,
        redacted=redacted,
        pii_types=tuple(pii_types),
    )


def output_is_safe(text: str) -> bool:
    if len(text) > settings.max_message_characters or contains_secret(text):
        return False
    normalized = _normalized_for_rules(text)
    leak_markers = (
        "systemprompt",
        "developerinstructions",
        "geminiapikey",
        "discordbottoken",
    )
    return not any(marker in normalized for marker in leak_markers)


class SlidingWindowRateLimiter:
    """In-process MVP limiter. Use Redis when the API has multiple replicas."""

    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str, limit: int) -> None:
        now = monotonic()
        cutoff = now - self.window_seconds
        async with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                raise RateLimitExceeded(
                    "Bạn đang gửi yêu cầu quá nhanh. Vui lòng thử lại sau khoảng 1 phút."
                )
            events.append(now)

    def reset(self) -> None:
        self._events.clear()


rate_limiter = SlidingWindowRateLimiter()


async def enforce_rate_limits(
    student_id: str | None,
    channel_id: str | None,
) -> None:
    if student_id:
        await rate_limiter.check(
            f"user:{student_id}",
            settings.user_requests_per_minute,
        )
    if channel_id:
        await rate_limiter.check(
            f"channel:{channel_id}",
            settings.channel_requests_per_minute,
        )
