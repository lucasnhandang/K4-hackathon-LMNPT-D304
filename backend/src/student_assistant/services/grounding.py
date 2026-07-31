"""Retrieve trusted course context and expose the retrieval score."""

from dataclasses import dataclass
from html import escape

from student_assistant.core.config import settings
from student_assistant.repositories.knowledge_repository import vector_search_kb
from student_assistant.services.embeddings import embed_query


@dataclass(frozen=True)
class GroundingResult:
    documents: list[dict]
    score: float
    method: str = "atlas_vector_search"

    @property
    def document_ids(self) -> list[str]:
        return [str(document["_id"]) for document in self.documents]


async def retrieve_grounding(query: str) -> GroundingResult:
    query_vector = await embed_query(query)
    documents = await vector_search_kb(
        query_vector,
        top_k=settings.vector_top_k,
        num_candidates=settings.vector_num_candidates,
        index_name=settings.vector_search_index,
    )
    normalized = [
        {
            **document,
            "_id": str(document["_id"]),
            "score": float(document.get("score", 0.0)),
        }
        for document in documents
    ]
    return GroundingResult(
        documents=normalized,
        score=normalized[0]["score"] if normalized else 0.0,
    )


def build_grounding_context(result: GroundingResult) -> str:
    return "\n\n".join(
        (
            f"<document id=\"{document['_id']}\" "
            f"score=\"{document['score']:.4f}\">\n"
            f"Tiêu đề: {escape(str(document.get('title', '')))}\n"
            f"Nội dung: {escape(str(document.get('content', '')))}\n"
            "</document>"
        )
        for document in result.documents
    )
