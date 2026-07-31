"""Schema cho endpoint Gemini ``/chat``."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: Literal["user", "model"]
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = Field(default_factory=list)
    student_id: str | None = None
    channel_id: str | None = None
    guild_id: str | None = None
    discord_message_id: str | None = None
    bot_id: str | None = None
    user_role_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    action: Literal["answer", "clarify", "escalate"]
    reply: str
    reason: str
    confidence: int = Field(
        ge=0,
        le=100,
        description="Deprecated compatibility field; derived from grounding_score.",
    )
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_kb_ids: list[str] = Field(default_factory=list)
    layer: str
    layer_name: str
