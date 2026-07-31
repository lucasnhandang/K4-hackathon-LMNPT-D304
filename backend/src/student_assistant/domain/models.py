"""Model dùng cho evaluation."""

from pydantic import BaseModel

from student_assistant.domain.enums import Decision


class GoldenCase(BaseModel):
    qid: str
    question: str
    expected_decision: Decision
    expected_kb_id: str | None = None
    notes: str | None = None


class EvalRow(BaseModel):
    qid: str
    question: str
    expected_decision: Decision
    actual_decision: Decision
    is_correct: bool
    actual_message: str
    confidence: float
