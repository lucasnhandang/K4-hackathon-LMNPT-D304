"""Sanitize, embed and persist knowledge posted in a configured Discord channel."""

import hashlib
from datetime import datetime, timezone

from student_assistant.api.schemas.knowledge import (
    DiscordKnowledgeIngestRequest,
    DiscordKnowledgeIngestResponse,
)
from student_assistant.core.config import settings
from student_assistant.repositories.discord_knowledge_repository import (
    upsert_discord_knowledge,
)
from student_assistant.services.embeddings import embed_documents
from student_assistant.services.guardrails import rate_limiter, sanitize_input


def _allowed_kb_channels() -> set[int]:
    return {
        int(value.strip())
        for value in settings.discord_kb_channel_ids.split(",")
        if value.strip()
    }


def _document_title(content: str) -> str:
    first_line = content.splitlines()[0].strip()
    if len(first_line) <= 100:
        return first_line
    return f"{first_line[:97].rstrip()}..."


async def ingest_discord_knowledge(
    payload: DiscordKnowledgeIngestRequest,
) -> DiscordKnowledgeIngestResponse:
    try:
        channel_id = int(payload.channel_id)
    except ValueError as exc:
        raise ValueError("Discord channel ID không hợp lệ.") from exc
    if channel_id not in _allowed_kb_channels():
        raise PermissionError("Channel không được phép ghi vào knowledge base.")

    await rate_limiter.check(
        f"kb-user:{payload.author_id}",
        settings.knowledge_ingest_user_per_minute,
    )
    await rate_limiter.check(
        f"kb-channel:{payload.channel_id}",
        settings.knowledge_ingest_channel_per_minute,
    )

    sanitized = sanitize_input(payload.content)
    title = _document_title(sanitized.redacted)
    embedding_text = f"Tiêu đề: {title}\nNội dung: {sanitized.redacted}"
    vector = (await embed_documents([embedding_text]))[0]
    now = datetime.now(timezone.utc)
    identity = (
        f"discord:{payload.guild_id}:{payload.channel_id}:"
        f"{payload.discord_message_id}"
    )
    content_hash = hashlib.sha256(
        f"{identity}\n{sanitized.redacted}".encode("utf-8")
    ).hexdigest()
    document = {
        "title": title,
        "content": sanitized.redacted,
        "tags": ["discord", "community-knowledge"],
        "source": "discord_channel",
        "source_message_id": payload.discord_message_id,
        "source_guild_id": payload.guild_id,
        "source_channel_id": payload.channel_id,
        "source_author_id": payload.author_id,
        "source_author_role_ids": payload.author_role_ids,
        "source_created_at": payload.discord_created_at,
        "trust_level": "configured_channel",
        "pii_types": list(sanitized.pii_types),
        "version": 1,
        "is_active": True,
        "embedding": vector,
        "embedding_model": settings.gemini_embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "content_hash": content_hash,
        "updated_at": now,
    }
    document_id, created = await upsert_discord_knowledge(document)
    return DiscordKnowledgeIngestResponse(
        status="stored" if created else "updated",
        document_id=document_id,
    )
