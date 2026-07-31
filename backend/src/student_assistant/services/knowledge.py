"""Fuzzy retrieval trên tài liệu MongoDB."""

from rapidfuzz import fuzz

from student_assistant.repositories.knowledge_repository import (
    fetch_kb_documents,
)


async def search_kb(query: str, top_k: int = 3) -> list[dict]:
    documents = await fetch_kb_documents()
    scored: list[dict] = []

    for document in documents:
        content_score = (
            fuzz.token_set_ratio(query, document["content"]) / 100.0
        )
        title_score = (
            fuzz.token_set_ratio(query, document.get("title", "")) / 100.0
        )
        scored.append({
            **document,
            "_id": str(document["_id"]),
            "score": max(content_score, title_score),
        })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def best_similarity(results: list[dict]) -> float:
    return results[0]["score"] if results else 0.0
