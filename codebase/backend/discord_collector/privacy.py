from __future__ import annotations

import hashlib
import hmac
import re


class PrivacyFilter:
    EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
    PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.-]?\d){8,10}(?!\d)")
    USER_MENTION = re.compile(r"<@!?\d{17,20}>")
    DISCORD_INVITE = re.compile(
        r"https?://(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/[A-Za-z0-9-]+",
        re.IGNORECASE,
    )
    SECRET_ASSIGNMENT = re.compile(
        r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[:=]\s*[^\s,;]+"
    )
    DISCORD_TOKEN = re.compile(
        r"(?<![A-Za-z0-9_-])(?:mfa\.[A-Za-z0-9_-]{20,}|"
        r"[A-Za-z0-9_-]{20,30}\.[A-Za-z0-9_-]{6,8}\.[A-Za-z0-9_-]{20,50})"
    )

    def __init__(self, secret: str):
        if len(secret) < 32:
            raise ValueError("Pseudonym secret must contain at least 32 characters.")
        self.secret = secret.encode("utf-8")

    def pseudonymize(self, discord_user_id: int | str) -> str:
        digest = hmac.new(
            self.secret,
            str(discord_user_id).encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        return f"usr_{digest[:24]}"

    def redact(self, content: str) -> str:
        value = self.DISCORD_TOKEN.sub("[DISCORD_TOKEN]", content)
        value = self.SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        value = self.EMAIL.sub("[EMAIL]", value)
        value = self.PHONE.sub("[PHONE]", value)
        value = self.USER_MENTION.sub("[USER_MENTION]", value)
        value = self.DISCORD_INVITE.sub("[DISCORD_INVITE]", value)
        return value.strip()
