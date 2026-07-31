"""Pure helpers cho Discord messages."""

import re

import discord


MAX_DISCORD_REPLY_LENGTH = 1_900


def parse_channel_ids(
    raw_value: str,
    setting_name: str = "DISCORD_ALLOWED_CHANNEL_IDS",
) -> set[int]:
    channel_ids: set[int] = set()
    for value in raw_value.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            channel_ids.add(int(value))
        except ValueError as exc:
            raise RuntimeError(
                f"{setting_name} chứa ID không hợp lệ: "
                f"{value!r}"
            ) from exc
    return channel_ids


def extract_question(content: str, bot_user_id: int) -> str:
    mention_pattern = rf"<@!?{bot_user_id}>"
    return re.sub(mention_pattern, " ", content).strip()


def is_allowed_channel(
    channel_id: int,
    allowed_channel_ids: set[int],
) -> bool:
    return not allowed_channel_ids or channel_id in allowed_channel_ids


def should_ingest_knowledge_message(
    channel_id: int,
    knowledge_channel_ids: set[int],
    *,
    bot_is_mentioned: bool,
) -> bool:
    return not bot_is_mentioned and channel_id in knowledge_channel_ids


def discord_safe_reply(message: str) -> str:
    message = discord.utils.escape_mentions(message.strip())
    if len(message) <= MAX_DISCORD_REPLY_LENGTH:
        return message
    return f"{message[:MAX_DISCORD_REPLY_LENGTH].rstrip()}…"


def discord_role_ids(member) -> list[str]:
    return [
        str(role.id)
        for role in getattr(member, "roles", [])
        if not role.is_default()
    ]
