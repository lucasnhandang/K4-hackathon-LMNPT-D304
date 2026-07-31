"""Application service coordinating guardrails, grounding, Gemini and storage."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from student_assistant.api.schemas.chat import ChatRequest, ChatResponse
from student_assistant.core.config import settings
from student_assistant.repositories.chat_repository import save_chat_exchange
from student_assistant.repositories.user_memory_repository import (
    delete_preferred_name,
    get_preferred_name,
    save_preferred_name,
)
from student_assistant.services.gemini import generate_chat_response
from student_assistant.services.grounding import (
    GroundingResult,
    build_grounding_context,
    retrieve_grounding,
)
from student_assistant.services.guardrails import (
    enforce_rate_limits,
    output_is_safe,
    redact_pii,
    sanitize_input,
)
from student_assistant.services.user_memory import (
    is_capabilities_question,
    parse_memory_command,
)


logger = logging.getLogger("student-assistant-api")


def build_conversation_id(payload: ChatRequest) -> str:
    if payload.guild_id and payload.channel_id and payload.discord_message_id:
        return (
            f"discord:{payload.guild_id}:{payload.channel_id}:"
            f"{payload.discord_message_id}"
        )
    return str(uuid4())


def _response(
    *,
    action: str,
    reply: str,
    reason: str,
    grounding: GroundingResult | None = None,
    layer: str,
    layer_name: str,
) -> ChatResponse:
    score = grounding.score if grounding else 0.0
    return ChatResponse(
        action=action,
        reply=reply,
        reason=reason,
        confidence=round(score * 100),
        grounding_score=score,
        matched_kb_ids=grounding.document_ids if grounding else [],
        layer=layer,
        layer_name=layer_name,
    )


def _is_social_message(message: str) -> bool:
    normalized = " ".join(message.casefold().split()).strip(" !?.")
    return normalized in {
        "hi",
        "hello",
        "xin chào",
        "chào",
        "chào bot",
        "cảm ơn",
        "thanks",
        "thank you",
    }


def _capabilities_reply(preferred_name: str | None = None) -> str:
    opening = f"{preferred_name} ơi, mình" if preferred_name else "Mình"
    return (
        f"{opening} hiện có thể tra cứu thông tin về deadline, lịch mentor, "
        "cách nộp bài, tiêu chí chấm, quy định khóa học và điều kiện chứng chỉ. "
        "Mình cũng có thể nhớ tên để trò chuyện tự nhiên hơn. "
        "Bạn cứ hỏi như đang nhắn với một người bạn nhé!"
    )


async def _handle_user_memory(
    message: str,
    payload: ChatRequest,
) -> ChatResponse | None:
    command = parse_memory_command(message)
    if command is None:
        return None
    if not payload.student_id:
        return _response(
            action="clarify",
            reply="Mình cần Discord user ID để ghi nhớ thông tin này.",
            reason="User memory requires student_id.",
            layer="user_memory",
            layer_name="Bộ nhớ người dùng",
        )

    if command.action == "remember_name":
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.user_memory_retention_days)
        await save_preferred_name(
            payload.student_id,
            payload.guild_id,
            command.value or "",
            updated_at=now,
            expires_at=expires_at,
        )
        if is_capabilities_question(message):
            reply = (
                f"Rất vui được biết bạn, {command.value}! "
                f"{_capabilities_reply()}"
            )
        else:
            reply = (
                f"Rất vui được biết bạn, {command.value}! "
                "Từ giờ mình sẽ gọi bạn như vậy nhé."
            )
        return _response(
            action="answer",
            reply=reply,
            reason="Người dùng chủ động yêu cầu lưu preferred_name.",
            layer="user_memory",
            layer_name="Ghi nhớ tên người dùng",
        )

    if command.action == "recall_name":
        preferred_name = await get_preferred_name(
            payload.student_id,
            payload.guild_id,
        )
        if preferred_name:
            return _response(
                action="answer",
                reply=f"Bạn là {preferred_name} nè. Mình vẫn nhớ nhé!",
                reason="Đọc preferred_name theo Discord user ID và guild ID.",
                layer="user_memory",
                layer_name="Đọc tên người dùng",
            )
        return _response(
            action="clarify",
            reply=(
                "Mình chưa biết bạn muốn được gọi là gì. "
                "Bạn chỉ cần nói, ví dụ: “Mình tên là Thịnh” nhé."
            ),
            reason="Không có preferred_name trong user_memories.",
            layer="user_memory",
            layer_name="Chưa có tên người dùng",
        )

    deleted = await delete_preferred_name(
        payload.student_id,
        payload.guild_id,
    )
    return _response(
        action="answer",
        reply=(
            "Được rồi, mình đã quên tên bạn nhé."
            if deleted
            else "Mình chưa lưu tên của bạn, nên hiện chưa có gì cần xóa nhé."
        ),
        reason="Người dùng chủ động yêu cầu xóa preferred_name.",
        layer="user_memory",
        layer_name="Xóa tên người dùng",
    )


async def _build_result(
    message: str,
    payload: ChatRequest,
) -> ChatResponse:
    memory_result = await _handle_user_memory(message, payload)
    if memory_result is not None:
        return memory_result

    if is_capabilities_question(message):
        preferred_name = None
        if payload.student_id:
            preferred_name = await get_preferred_name(
                payload.student_id,
                payload.guild_id,
            )
        return _response(
            action="answer",
            reply=_capabilities_reply(preferred_name),
            reason="Câu hỏi về khả năng của bot không cần truy xuất KB.",
            layer="safe_social",
            layer_name="Giới thiệu khả năng trợ lý",
        )

    if _is_social_message(message):
        preferred_name = None
        if payload.student_id:
            preferred_name = await get_preferred_name(
                payload.student_id,
                payload.guild_id,
            )
        greeting = (
            f"Xin chào {preferred_name}! Hôm nay mình có thể giúp gì cho bạn?"
            if preferred_name
            else "Xin chào! Hôm nay mình có thể giúp gì cho bạn?"
        )
        return _response(
            action="answer",
            reply=greeting,
            reason="Lời chào xã giao không cần truy xuất knowledge base.",
            layer="safe_social",
            layer_name="Phản hồi xã giao an toàn",
        )

    grounding = await retrieve_grounding(message)
    if grounding.score < settings.vector_clarify_threshold:
        return _response(
            action="clarify",
            reply=(
                "Mình chưa thấy thông tin này trong tài liệu của khóa học. "
                "Nếu bạn muốn, mình có thể nhờ Mod hỗ trợ thêm nhé?"
            ),
            reason=(
                f"Top vector score {grounding.score:.4f} thấp hơn ngưỡng "
                f"{settings.vector_clarify_threshold:.2f}."
            ),
            grounding=grounding,
            layer="grounding_low",
            layer_name="Đề nghị chuyển Mod",
        )

    if grounding.score < settings.vector_answer_threshold:
        return _response(
            action="clarify",
            reply=(
                "Mình thấy vài nội dung có liên quan nhưng chưa chắc bạn đang hỏi "
                "phần nào. Bạn nói thêm tên bài hoặc module giúp mình nhé?"
            ),
            reason=(
                f"Top vector score {grounding.score:.4f} nằm trong vùng cần làm rõ."
            ),
            grounding=grounding,
            layer="grounding_medium",
            layer_name="Thiếu ngữ cảnh",
        )

    generated = await generate_chat_response(
        message,
        payload.history,
        build_grounding_context(grounding),
    )
    if not (
        output_is_safe(generated.reply)
        and output_is_safe(generated.reasoning)
    ):
        logger.warning("Output scanner đã chặn phản hồi không an toàn.")
        return _response(
            action="clarify",
            reply=(
                "Mình chưa hiểu câu này theo cách đủ an toàn để trả lời. "
                "Bạn thử diễn đạt lại ngắn gọn hơn giúp mình nhé?"
            ),
            reason="Output scanner rejected the generated reply.",
            grounding=grounding,
            layer="output_guardrail",
            layer_name="Kiểm tra đầu ra",
        )

    return _response(
        action=generated.action,
        reply=redact_pii(generated.reply),
        reason=redact_pii(generated.reasoning),
        grounding=grounding,
        layer="grounded_generation",
        layer_name="Trả lời dựa trên tài liệu",
    )


async def process_chat(payload: ChatRequest) -> ChatResponse:
    await enforce_rate_limits(payload.student_id, payload.channel_id)
    sanitized = sanitize_input(payload.message)
    sanitized_history = [
        item.model_copy(update={"text": sanitize_input(item.text).redacted})
        for item in payload.history[-10:]
    ]
    safe_payload = payload.model_copy(update={"history": sanitized_history})
    result = await _build_result(sanitized.redacted, safe_payload)

    created_at = datetime.now(timezone.utc)
    conversation_id = build_conversation_id(payload)
    redacted_expires_at = created_at + timedelta(
        days=settings.redacted_retention_days
    )
    raw_expires_at = created_at + timedelta(days=settings.raw_retention_days)

    common = {
        "conversation_id": conversation_id,
        "guild_id": payload.guild_id,
        "channel_id": payload.channel_id,
        "created_at": created_at,
        "expires_at": redacted_expires_at,
    }
    conversation_document = {
        **common,
        "student_id": payload.student_id,
        "bot_id": payload.bot_id,
        "user_role_ids": payload.user_role_ids,
        "discord_message_id": payload.discord_message_id,
        "question": sanitized.redacted,
        "pii_types": list(sanitized.pii_types),
        "decision": result.action,
        "message": result.reply,
        "confidence": result.confidence / 100,
        "grounding_score": result.grounding_score,
        "matched_kb_ids": result.matched_kb_ids,
        "reason": result.reason,
        "layer": result.layer,
        "layer_name": result.layer_name,
        "retrieval_method": (
            "none"
            if result.layer in {"safe_social", "user_memory"}
            else "atlas_vector_search"
        ),
        "provider": "gemini",
        "model": settings.gemini_model,
    }
    user_message = {
        **common,
        "role": "user",
        "author_id": payload.student_id,
        "discord_role_ids": payload.user_role_ids,
        "content": sanitized.redacted,
        "discord_message_id": payload.discord_message_id,
        "reply_to_discord_message_id": None,
        "pii_types": list(sanitized.pii_types),
    }
    assistant_message = {
        **common,
        "role": "assistant",
        "author_id": payload.bot_id,
        "discord_role_ids": [],
        "content": result.reply,
        "discord_message_id": None,
        "reply_to_discord_message_id": payload.discord_message_id,
        "provider": "gemini",
        "model": settings.gemini_model,
        "decision": result.action,
        "confidence": result.confidence / 100,
        "grounding_score": result.grounding_score,
        "reason": result.reason,
    }
    raw_message = {
        "conversation_id": conversation_id,
        "author_id": payload.student_id,
        "content": sanitized.raw,
        "created_at": created_at,
        "expires_at": raw_expires_at,
    }

    await save_chat_exchange(
        conversation_document,
        user_message,
        assistant_message,
        raw_message,
    )
    logger.info(
        "Đã lưu MongoDB: conversation=%s user_id=%s score=%.4f pii=%s",
        conversation_id,
        payload.student_id,
        result.grounding_score,
        list(sanitized.pii_types),
    )
    return result
