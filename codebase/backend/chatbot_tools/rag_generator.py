"""RAG response generator for the Discord student assistant.

Generates natural Vietnamese responses by combining retrieved context
(BM25 official sources + community questions) with an LLM via OpenRouter.
"""

from __future__ import annotations

import logging
from typing import Any

from .llm_client import LLMClient, LLMConfig, LLMResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Bạn là trợ lý AI của khóa học AI20K Build Phase (trường FPT Arena).

NHIỆM VỤ: Trả lời câu hỏi của học viên bằng tiếng Việt, ngắn gọn, thân thiện.

QUY TẮC BẮT BUỘC:
1. CHỈ dùng thông tin từ [CONTEXT] được cung cấp bên dưới.
2. Nếu không có thông tin phù hợp trong context, trả lời: "Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha!"
3. KHÔNG tự tạo thông tin ngoài context.
4. KHÔNG sửa đổi số liệu, deadline, tên sự kiện trong context.
5. Luôn trích dẫn nguồn (nếu có trong context).
6. Trả lời bằng tiếng Việt, thân thiện, sử dụng emoji适量.

PHONG CÁCH:
- Ngắn gọn, đi thẳng vào vấn đề
- Dùng markdown formatting (**bold**, bullet points)
- Thêm emoji cho thân thiện 😊
- Nếu context có deadline, highlight thời gian bằng **bold**
"""

# Maximum context length (characters) to avoid token overflow
MAX_CONTEXT_CHARS = 3000


# ---------------------------------------------------------------------------
# RAG Generator
# ---------------------------------------------------------------------------


class RAGGenerator:
    """Generates responses using retrieved context + OpenRouter LLM."""

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    def generate(
        self,
        *,
        query: str,
        context_chunks: list[dict[str, Any]] | None = None,
        community_matches: list[dict[str, Any]] | None = None,
        intent: str | None = None,
        extra_instructions: str = "",
    ) -> dict[str, Any]:
        """Generate a RAG response.

        Args:
            query: The user's original question.
            context_chunks: Official source chunks from BM25 search.
                Each dict should have: source_id, category, score, attributes, quote (optional).
            community_matches: Community Q&A matches from conversation search.
                Each dict should have: question_preview, jump_url, score.
            intent: Classified intent (for context).
            extra_instructions: Additional instructions for the LLM.

        Returns:
            Dict with keys: response, model, usage, grounded, sources.
        """
        if not self.client.is_available():
            return {
                "response": (
                    "Mình chưa thể trả lời câu hỏi này lúc này. "
                    "Bạn vui lòng thử lại sau hoặc gửi ticket hỗ trợ nha! 🎫"
                ),
                "model": "none",
                "usage": {},
                "grounded": False,
                "sources": [],
            }

        # Build context string
        context_str = self._build_context(context_chunks, community_matches)
        if not context_str:
            context_str = "(Không có thông tin từ nguồn chính thức)"

        # Build user message
        user_message = self._build_user_message(
            query=query,
            context=context_str,
            intent=intent,
            extra_instructions=extra_instructions,
        )

        # Call LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        try:
            llm_response = self.client.chat(messages)
        except Exception as error:
            logger.error("RAG generation failed: %s", error)
            return {
                "response": (
                    "Mình gặp lỗi khi xử lý câu hỏi. "
                    "Bạn vui lòng thử lại hoặc gửi ticket hỗ trợ nha! 🎫"
                ),
                "model": "error",
                "usage": {},
                "grounded": False,
                "sources": [],
            }

        # Build sources list
        sources = self._collect_sources(context_chunks, community_matches)

        return {
            "response": llm_response.content.strip(),
            "model": llm_response.model,
            "usage": llm_response.usage,
            "grounded": bool(context_chunks),
            "sources": sources,
        }

    def _build_context(
        self,
        context_chunks: list[dict[str, Any]] | None,
        community_matches: list[dict[str, Any]] | None,
    ) -> str:
        """Build context string from retrieved chunks."""
        parts: list[str] = []

        # Official sources (highest priority)
        if context_chunks:
            parts.append("[CONTEXT - NGUỒN CHÍNH THỨC]")
            for i, chunk in enumerate(context_chunks[:5], 1):
                source_id = chunk.get("source_id", "")
                category = chunk.get("category", "")
                quote = chunk.get("quote", "")
                attributes = chunk.get("attributes", {})
                score = chunk.get("score", 0)

                parts.append(f"\n--- Nguồn {i} ({source_id}, loại: {category}, score: {score}) ---")
                if quote:
                    parts.append(f"Nội dung: {quote}")
                if attributes:
                    attr_str = ", ".join(f"{k}: {v}" for k, v in attributes.items())
                    parts.append(f"Thuộc tính: {attr_str}")

        # Community matches (lower priority, reference only)
        if community_matches:
            parts.append("\n[CONTEXT - HỘI THOẠI CỘNG ĐỒNG (chỉ tham khảo)]")
            for i, match in enumerate(community_matches[:3], 1):
                preview = match.get("question_preview", "")
                jump_url = match.get("jump_url", "")
                parts.append(f"\n--- Câu hỏi cộng đồng {i} ---")
                parts.append(f"Câu hỏi: {preview}")
                if jump_url:
                    parts.append(f"Link: {jump_url}")

        context = "\n".join(parts)

        # Truncate if too long
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n... (đã cắt ngắn)"

        return context

    def _build_user_message(
        self,
        *,
        query: str,
        context: str,
        intent: str | None,
        extra_instructions: str,
    ) -> str:
        """Build the user message for the LLM."""
        parts = []

        if intent:
            parts.append(f"[Intent được phân loại: {intent}]")

        parts.append(f"[CONTEXT]\n{context}\n[/CONTEXT]")
        parts.append(f"\nCâu hỏi của học viên: {query}")

        if extra_instructions:
            parts.append(f"\n[HƯỚNG DẪN BỔ SUNG]\n{extra_instructions}")

        return "\n".join(parts)

    def _collect_sources(
        self,
        context_chunks: list[dict[str, Any]] | None,
        community_matches: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        """Collect source references for citation."""
        sources: list[dict[str, str]] = []

        if context_chunks:
            for chunk in context_chunks[:3]:
                sources.append({
                    "type": "official",
                    "source_id": chunk.get("source_id", ""),
                    "category": chunk.get("category", ""),
                })

        if community_matches:
            for match in community_matches[:2]:
                sources.append({
                    "type": "community",
                    "question_preview": match.get("question_preview", "")[:100],
                    "jump_url": match.get("jump_url", ""),
                })

        return sources
