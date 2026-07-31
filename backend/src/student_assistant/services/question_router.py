"""Routing ``TRA_LOI / HOI_LAI / CHUYEN_MOD`` cho endpoint ``/ask``."""

import json

from anthropic import Anthropic

from student_assistant.api.schemas.ask import AskResponse
from student_assistant.core.config import settings
from student_assistant.domain.enums import Decision
from student_assistant.services.knowledge import (
    best_similarity,
    search_kb,
)


CLARITY_SYSTEM_PROMPT = """Bạn là bộ lọc ngữ cảnh cho trợ lý học viên trên Discord.
Nhiệm vụ: đọc câu hỏi thô (có thể viết tắt, thiếu chủ ngữ, gõ tắt kiểu chat) và
quyết định câu hỏi ĐÃ ĐỦ ngữ cảnh để tra cứu tài liệu trả lời hay chưa.

Thiếu ngữ cảnh nghĩa là: không rõ đang hỏi về cái gì (VD: "deadline bao nhiêu z"
mà không rõ deadline của bài nào/tuần nào).

Trả lời CHỈ bằng JSON, không thêm chữ nào khác, đúng format:
{"is_clear": true/false, "clarifying_question": "câu hỏi làm rõ (chỉ điền nếu is_clear=false, nếu không thì để rỗng)"}
"""

ANSWER_SYSTEM_PROMPT = """Bạn là trợ lý học viên, trả lời DỰA HOÀN TOÀN vào các đoạn
tài liệu được cung cấp bên dưới. Không được bịa thông tin ngoài tài liệu.
Nếu tài liệu không đủ để trả lời chắc chắn, hãy tự chấm confidence thấp.

Trả lời CHỈ bằng JSON, đúng format:
{"answer": "câu trả lời ngắn gọn, đúng trọng tâm", "confidence": 0.0-1.0}
"""


def _call_llm_json(system: str, user: str) -> dict:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "Chưa cấu hình ANTHROPIC_API_KEY trong .env — cần key thật để "
            "chạy AI thật, không dùng mock."
        )

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    text = (
        text.removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    return json.loads(text)


async def route_question(question: str) -> AskResponse:
    clarity = _call_llm_json(CLARITY_SYSTEM_PROMPT, question)

    if not clarity.get("is_clear", False):
        return AskResponse(
            decision=Decision.HOI_LAI,
            message=clarity.get("clarifying_question")
            or (
                "Bạn có thể nói rõ hơn câu hỏi liên quan tới phần nào "
                "của khóa không?"
            ),
            confidence=1.0,
            matched_kb_ids=[],
            reason="LLM đánh giá câu hỏi thiếu ngữ cảnh (is_clear=false).",
        )

    kb_results = await search_kb(question, top_k=3)
    similarity = best_similarity(kb_results)

    if similarity < settings.min_kb_similarity:
        return AskResponse(
            decision=Decision.CHUYEN_MOD,
            message=(
                "Câu hỏi này nằm ngoài phạm vi tài liệu khóa học hiện có, "
                "mình đã chuyển cho Mod hỗ trợ nhé."
            ),
            confidence=similarity,
            matched_kb_ids=[],
            reason=(
                f"Similarity cao nhất chỉ {similarity:.2f} "
                f"< ngưỡng {settings.min_kb_similarity}."
            ),
        )

    context_text = "\n\n".join(
        f"[{document['title']}]: {document['content']}"
        for document in kb_results
    )
    llm_answer = _call_llm_json(
        ANSWER_SYSTEM_PROMPT,
        f"Câu hỏi: {question}\n\nTài liệu liên quan:\n{context_text}",
    )
    confidence = float(llm_answer.get("confidence", 0.0))

    if confidence < settings.min_confidence_to_answer:
        return AskResponse(
            decision=Decision.CHUYEN_MOD,
            message=(
                "Mình chưa đủ chắc chắn để trả lời chính xác câu này, "
                "đã chuyển cho Mod nhé."
            ),
            confidence=confidence,
            matched_kb_ids=[document["_id"] for document in kb_results],
            reason=(
                f"LLM tự chấm confidence {confidence:.2f} "
                f"< ngưỡng {settings.min_confidence_to_answer}."
            ),
        )

    return AskResponse(
        decision=Decision.TRA_LOI,
        message=llm_answer.get("answer", ""),
        confidence=confidence,
        matched_kb_ids=[document["_id"] for document in kb_results],
        reason=(
            f"Tìm được tài liệu liên quan (sim={similarity:.2f}) và "
            f"LLM tự tin (confidence={confidence:.2f})."
        ),
    )
