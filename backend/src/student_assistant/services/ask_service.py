"""Application service cho luồng ``/ask``."""

from datetime import datetime, timezone

from student_assistant.api.schemas.ask import AskRequest, AskResponse
from student_assistant.repositories.chat_repository import save_ask_exchange
from student_assistant.services.question_router import route_question


async def process_question(payload: AskRequest) -> AskResponse:
    result = await route_question(payload.question)
    await save_ask_exchange(payload, result, datetime.now(timezone.utc))
    return result
