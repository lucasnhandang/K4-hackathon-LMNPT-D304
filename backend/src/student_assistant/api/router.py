"""Router gốc của API."""

from fastapi import APIRouter

from student_assistant.api.routes import ask, chat, health, knowledge


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ask.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
