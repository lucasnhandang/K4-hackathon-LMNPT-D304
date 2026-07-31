"""Schemas for trusted Discord-channel knowledge ingestion."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DiscordKnowledgeIngestRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2_000)
    author_id: str
    author_role_ids: list[str] = Field(default_factory=list)
    guild_id: str
    channel_id: str
    discord_message_id: str
    discord_created_at: datetime


class DiscordKnowledgeIngestResponse(BaseModel):
    status: Literal["stored", "updated"]
    document_id: str
