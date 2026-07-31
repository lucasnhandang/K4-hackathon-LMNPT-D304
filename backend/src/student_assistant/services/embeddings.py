"""Gemini embedding adapter."""

from collections.abc import Sequence

from student_assistant.core.config import settings


async def embed_texts(
    texts: Sequence[str],
    *,
    task_type: str,
) -> list[list[float]]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY chưa được cấu hình trong .env")
    if not texts:
        return []

    from google import genai
    from google.genai import types

    config = types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=settings.embedding_dimensions,
    )
    vectors: list[list[float]] = []
    async with genai.Client(api_key=settings.gemini_api_key).aio as client:
        # Gemini Embedding 2 treats a list of strings as parts of one
        # multimodal Content, so each KB chunk must be embedded separately.
        for text in texts:
            response = await client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
                config=config,
            )
            embeddings = response.embeddings or []
            vector = list(embeddings[0].values or []) if embeddings else []
            if not vector:
                raise RuntimeError("Gemini không trả về embedding.")
            if len(vector) != settings.embedding_dimensions:
                raise RuntimeError(
                    "Embedding không đúng số chiều cấu hình: "
                    f"expected={settings.embedding_dimensions}, "
                    f"actual={len(vector)}."
                )
            vectors.append(vector)
    return vectors


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text], task_type="RETRIEVAL_QUERY"))[0]


async def embed_documents(texts: Sequence[str]) -> list[list[float]]:
    return await embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
