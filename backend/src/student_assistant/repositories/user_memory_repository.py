"""Persistence for explicit, allowlisted user memories."""

from datetime import datetime, timezone

from student_assistant.repositories.mongo import get_db


def _identity_filter(student_id: str, guild_id: str | None) -> dict:
    return {
        "student_id": student_id,
        "guild_id": guild_id,
    }


async def get_preferred_name(
    student_id: str,
    guild_id: str | None,
) -> str | None:
    document = await get_db().user_memories.find_one(
        _identity_filter(student_id, guild_id),
        {"_id": 0, "preferred_name": 1},
    )
    if not document:
        return None
    value = document.get("preferred_name")
    return str(value) if value else None


async def save_preferred_name(
    student_id: str,
    guild_id: str | None,
    preferred_name: str,
    *,
    updated_at: datetime,
    expires_at: datetime,
) -> None:
    await get_db().user_memories.update_one(
        _identity_filter(student_id, guild_id),
        {
            "$set": {
                "preferred_name": preferred_name,
                "updated_at": updated_at,
                "expires_at": expires_at,
            },
            "$setOnInsert": {"created_at": updated_at},
        },
        upsert=True,
    )


async def delete_preferred_name(
    student_id: str,
    guild_id: str | None,
) -> bool:
    result = await get_db().user_memories.update_one(
        _identity_filter(student_id, guild_id),
        {
            "$unset": {"preferred_name": ""},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    return result.modified_count > 0
