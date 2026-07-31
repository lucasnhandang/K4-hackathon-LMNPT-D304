"""Endpoint hỏi đáp dựa trên knowledge base."""

from fastapi import APIRouter, HTTPException

from student_assistant.api.schemas.ask import AskRequest, AskResponse
from student_assistant.services.ask_service import process_question


router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> AskResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi rỗng.")
    return await process_question(payload)
