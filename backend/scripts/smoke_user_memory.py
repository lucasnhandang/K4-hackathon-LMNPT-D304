"""Create, recall and clean up one temporary MongoDB user memory."""

import asyncio
from datetime import datetime, timedelta, timezone

from student_assistant.repositories.mongo import (
    close_client,
    ensure_indexes,
    get_db,
)
from student_assistant.repositories.user_memory_repository import (
    get_preferred_name,
    save_preferred_name,
)


STUDENT_ID = "__smoke_user_memory__"
GUILD_ID = "__smoke_guild__"


async def main() -> None:
    try:
        await ensure_indexes()
        now = datetime.now(timezone.utc)
        await save_preferred_name(
            STUDENT_ID,
            GUILD_ID,
            "Thịnh",
            updated_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        recalled = await get_preferred_name(STUDENT_ID, GUILD_ID)
        if recalled != "Thịnh":
            raise RuntimeError(f"Unexpected recalled name: {recalled!r}")
        await save_preferred_name(
            STUDENT_ID,
            GUILD_ID,
            "Quang",
            updated_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        updated = await get_preferred_name(STUDENT_ID, GUILD_ID)
        if updated != "Quang":
            raise RuntimeError(f"Unexpected updated name: {updated!r}")
        print(
            "User memory smoke test passed: "
            f"created={recalled}, updated={updated}"
        )
    finally:
        await get_db().user_memories.delete_one(
            {"student_id": STUDENT_ID, "guild_id": GUILD_ID}
        )
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
