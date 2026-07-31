"""MongoDB writes for knowledge captured from a Discord channel."""

from student_assistant.repositories.mongo import get_db


async def upsert_discord_knowledge(document: dict) -> tuple[str, bool]:
    collection = get_db().kb_documents
    existing = await collection.find_one(
        {
            "source": "discord_channel",
            "source_message_id": document["source_message_id"],
        },
        {"_id": 1},
    )
    result = await collection.update_one(
        {
            "source": "discord_channel",
            "source_message_id": document["source_message_id"],
        },
        {
            "$set": document,
            "$setOnInsert": {"created_at": document["updated_at"]},
        },
        upsert=True,
    )
    if existing:
        return str(existing["_id"]), False
    return str(result.upserted_id), True
