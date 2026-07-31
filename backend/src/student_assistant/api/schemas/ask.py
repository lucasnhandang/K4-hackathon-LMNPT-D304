"""Schema cho endpoint ``/ask``."""

from pydantic import BaseModel, Field

from student_assistant.domain.enums import Decision


class AskRequest(BaseModel):
    student_id: str = Field(..., description="ID Discord của học viên")
    question: str = Field(..., min_length=1, description="Câu hỏi thô")
    channel_id: str | None = None


class AskResponse(BaseModel):
    decision: Decision
    message: str
    confidence: float
    matched_kb_ids: list[str] = Field(default_factory=list)
    reason: str
