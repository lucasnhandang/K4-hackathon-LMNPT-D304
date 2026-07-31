"""Temporarily ingest and retrieve one Discord KB message, then clean it up."""

import asyncio
from datetime import datetime, timezone

from student_assistant.api.schemas.knowledge import (
    DiscordKnowledgeIngestRequest,
)
from student_assistant.core.config import settings
from student_assistant.repositories.mongo import (
    close_client,
    ensure_indexes,
    get_db,
)
from student_assistant.repositories.knowledge_repository import vector_search_kb
from student_assistant.services.discord_knowledge import (
    ingest_discord_knowledge,
)
from student_assistant.services.embeddings import embed_query


MESSAGE_ID = "__smoke_discord_knowledge__"
CONTENT = (
    "Mã kiểm thử kiến thức Discord là ZETA-731. "
    "Mã này chỉ dùng để xác nhận luồng ingest."
)


async def main() -> None:
    channel_id = next(
        (
            value.strip()
            for value in settings.discord_kb_channel_ids.split(",")
            if value.strip()
        ),
        None,
    )
    if not channel_id:
        raise RuntimeError("DISCORD_KB_CHANNEL_IDS chưa được cấu hình.")

    collection = get_db().kb_documents
    try:
        await ensure_indexes()
        result = await ingest_discord_knowledge(
            DiscordKnowledgeIngestRequest(
                content=CONTENT,
                author_id="__smoke_author__",
                guild_id="__smoke_guild__",
                channel_id=channel_id,
                discord_message_id=MESSAGE_ID,
                discord_created_at=datetime.now(timezone.utc),
            )
        )
        stored = await collection.find_one(
            {
                "source": "discord_channel",
                "source_message_id": MESSAGE_ID,
            }
        )
        if not stored:
            raise RuntimeError("Discord knowledge document was not stored.")

        query_vector = await embed_query("Mã kiểm thử ZETA-731 là gì?")
        matched = False
        score = 0.0
        for _ in range(10):
            documents = await vector_search_kb(
                query_vector,
                top_k=settings.vector_top_k,
                num_candidates=settings.vector_num_candidates,
                index_name=settings.vector_search_index,
            )
            score = float(documents[0].get("score", 0.0)) if documents else 0.0
            matched = any(
                document.get("source_message_id") == MESSAGE_ID
                for document in documents
            )
            if matched:
                break
            await asyncio.sleep(2)
        print(
            f"Discord KB smoke: status={result.status}, "
            f"score={score:.4f}, matched={matched}"
        )
        if not matched:
            raise RuntimeError("Vector Search did not retrieve the smoke document.")
    finally:
        await collection.delete_one(
            {
                "source": "discord_channel",
                "source_message_id": MESSAGE_ID,
            }
        )
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
