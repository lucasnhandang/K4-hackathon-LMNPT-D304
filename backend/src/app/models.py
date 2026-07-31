"""Compatibility shim cho model imports cũ."""

from student_assistant.api.schemas.ask import AskRequest, AskResponse
from student_assistant.domain.enums import Decision
from student_assistant.domain.models import EvalRow, GoldenCase


__all__ = [
    "AskRequest",
    "AskResponse",
    "Decision",
    "EvalRow",
    "GoldenCase",
]
