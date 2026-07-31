"""Đọc tài liệu knowledge base từ MongoDB."""

from student_assistant.repositories.mongo import get_db


async def fetch_kb_documents(limit: int = 1_000) -> list[dict]:
    projection = {"_id": 1, "content": 1, "tags": 1, "title": 1}
    cursor = get_db().kb_documents.find({}, projection)
    return await cursor.to_list(length=limit)


async def vector_search_kb(
    query_vector: list[float],
    *,
    top_k: int,
    num_candidates: int,
    index_name: str,
) -> list[dict]:
    pipeline = [
        {
            "$vectorSearch": {
                "index": index_name,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": max(num_candidates, top_k),
                "limit": top_k,
                "filter": {"is_active": True},
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "content": 1,
                "source": 1,
                "source_message_id": 1,
                "source_channel_id": 1,
                "version": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    return await get_db().kb_documents.aggregate(pipeline).to_list(length=top_k)
