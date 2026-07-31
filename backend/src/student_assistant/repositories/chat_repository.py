"""Ghi lịch sử hỏi đáp và từng message vào MongoDB."""

from datetime import datetime

from student_assistant.api.schemas.ask import AskRequest, AskResponse
from student_assistant.repositories.mongo import get_db


async def save_ask_exchange(
    payload: AskRequest,
    result: AskResponse,
    created_at: datetime,
) -> None:
    await get_db().conversations.insert_one({
        "student_id": payload.student_id,
        "channel_id": payload.channel_id,
        "question": payload.question,
        "decision": result.decision.value,
        "message": result.message,
        "confidence": result.confidence,
        "matched_kb_ids": result.matched_kb_ids,
        "reason": result.reason,
        "created_at": created_at,
    })


async def save_chat_exchange(
    conversation_document: dict,
    user_message: dict,
    assistant_message: dict,
    raw_message: dict | None = None,
) -> None:
    db = get_db()
    conversation_id = conversation_document["conversation_id"]

    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$setOnInsert": conversation_document},
        upsert=True,
    )
    await db.chat_messages.update_one(
        {"conversation_id": conversation_id, "role": "user"},
        {"$setOnInsert": user_message},
        upsert=True,
    )
    await db.chat_messages.update_one(
        {"conversation_id": conversation_id, "role": "assistant"},
        {"$setOnInsert": assistant_message},
        upsert=True,
    )
    if raw_message is not None:
        await db.raw_chat_messages.update_one(
            {"conversation_id": conversation_id},
            {"$setOnInsert": raw_message},
            upsert=True,
        )
