"""MongoDB connection lifecycle và indexes."""

from motor.motor_asyncio import AsyncIOMotorClient

from student_assistant.core.config import settings


_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_db():
    return get_client()[settings.mongo_db_name]


async def ensure_indexes() -> None:
    db = get_db()
    await db.kb_documents.create_index("tags")
    await db.kb_documents.create_index(
        [("content_hash", 1), ("embedding_model", 1)],
        unique=True,
        sparse=True,
    )
    await db.kb_documents.create_index(
        [("source", 1), ("source_message_id", 1)],
        unique=True,
        partialFilterExpression={"source_message_id": {"$exists": True}},
    )
    await db.conversations.create_index("created_at")
    await db.conversations.create_index(
        "conversation_id",
        unique=True,
        sparse=True,
    )
    await db.chat_messages.create_index(
        [("conversation_id", 1), ("role", 1)],
        unique=True,
    )
    await db.chat_messages.create_index(
        [("author_id", 1), ("created_at", -1)]
    )
    await db.chat_messages.create_index(
        [("guild_id", 1), ("channel_id", 1), ("created_at", -1)]
    )
    await db.conversations.create_index("expires_at", expireAfterSeconds=0)
    await db.chat_messages.create_index("expires_at", expireAfterSeconds=0)
    await db.raw_chat_messages.create_index(
        "conversation_id",
        unique=True,
    )
    await db.raw_chat_messages.create_index("expires_at", expireAfterSeconds=0)
    await db.user_memories.create_index(
        [("student_id", 1), ("guild_id", 1)],
        unique=True,
    )
    await db.user_memories.create_index("expires_at", expireAfterSeconds=0)
    await db.golden_set.create_index("qid", unique=True)
    await db.eval_runs.create_index("run_id")


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
