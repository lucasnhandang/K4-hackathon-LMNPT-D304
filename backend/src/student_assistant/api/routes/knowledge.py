"""Internal endpoint for Discord knowledge-channel ingestion."""

import logging

from fastapi import APIRouter, HTTPException

from student_assistant.api.schemas.knowledge import (
    DiscordKnowledgeIngestRequest,
    DiscordKnowledgeIngestResponse,
)
from student_assistant.services.discord_knowledge import (
    ingest_discord_knowledge,
)
from student_assistant.services.guardrails import (
    GuardrailViolation,
    RateLimitExceeded,
)


logger = logging.getLogger("student-assistant-api")
router = APIRouter()


@router.post(
    "/knowledge/discord",
    response_model=DiscordKnowledgeIngestResponse,
)
async def ingest_from_discord(
    payload: DiscordKnowledgeIngestRequest,
) -> DiscordKnowledgeIngestResponse:
    try:
        return await ingest_discord_knowledge(payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Lỗi ingest Discord knowledge")
        raise HTTPException(
            status_code=500,
            detail="Hệ thống chưa thể lưu knowledge lúc này.",
        ) from exc
