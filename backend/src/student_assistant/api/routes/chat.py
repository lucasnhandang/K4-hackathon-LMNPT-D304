"""Endpoint hỏi đáp Gemini."""

import logging

from fastapi import APIRouter, HTTPException

from student_assistant.api.schemas.chat import ChatRequest, ChatResponse
from student_assistant.core.config import settings
from student_assistant.services.chat_service import process_chat
from student_assistant.services.guardrails import (
    GuardrailViolation,
    RateLimitExceeded,
)


logger = logging.getLogger("student-assistant-api")
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn rỗng.")
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY chưa được cấu hình trong .env",
        )

    try:
        return await process_chat(payload)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Lỗi xử lý /chat")
        raise HTTPException(
            status_code=500,
            detail="Hệ thống chưa thể xử lý câu hỏi lúc này.",
        ) from exc
