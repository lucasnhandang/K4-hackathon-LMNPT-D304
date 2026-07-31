"""Main chatbot orchestrator for the Discord student assistant.

Ties together intent classification, tool execution, response generation,
and confidence checking. This is the core entry point for the chatbot.

Architecture:
    User message
        ↓
    Normalize Vietnamese, fix typos
        ↓
    Classify intent + extract slots
        ↓
    Split multi-part questions
        ↓
    Execute tools (structured data + RAG search)
        ↓
    Check confidence and conflicts
        ↓
    Generate short response + source + timestamp
        ↓
    Feedback / transfer to Mod when needed
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .intent_classifier import IntentResult, classify_intent, normalize_vietnamese
from .llm_client import LLMClient, LLMConfig
from .models import ToolResult
from .rag_generator import RAGGenerator
from .registry import ToolRegistry, build_default_registry
from .response_generator import generate_response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------

CONFIDENCE_HIGH = 0.7    # >= this: answer directly
CONFIDENCE_MEDIUM = 0.4  # >= this: answer with caveat or clarify
CONFIDENCE_LOW = 0.0     # < this: escalate or ask for clarification

# ---------------------------------------------------------------------------
# Intent-to-tool mapping
# ---------------------------------------------------------------------------

INTENT_TOOL_MAP: dict[str, str] = {
    "ask_deadline": "lookup_deadline",
    "ask_event_schedule": "lookup_event",
    "ask_gate": "lookup_gate",
    "ask_exam_slot": "lookup_exam_slot",
    "ask_xp": "lookup_xp",
    "ask_team_mentor": "lookup_team_mentor",
    "ask_slash_command": "lookup_slash_command",
}

SEARCH_CATEGORY_BY_INTENT: dict[str, str] = {
    "ask_attendance_policy": "policy",
    "ask_online_learning_availability": "policy",
    "ask_laptop_requirements": "policy",
    "ask_submission_channel": "slash_command",
    "ask_learning_material": "learning_material",
    "ask_team_naming": "team_mentor",
    "ask_topic_availability": "team_mentor",
    "ask_holiday_schedule": "policy",
    "ask_scholarship_info": "policy",
}

AUTHORITY_INTENTS = {
    "request_deadline_exception",
    "request_leave_of_absence",
    "request_grade_review",
    "report_harassment",
}

REFUSAL_INTENTS = {
    "reject_answer_key_request": (
        "Mình không thể cung cấp đáp án bài kiểm tra. "
        "Bạn có thể gửi phần kiến thức hoặc bước làm đang vướng để mình hướng dẫn."
    ),
    "reject_do_assignment_for_user": (
        "Mình không thể làm hoặc nộp bài thay bạn. "
        "Bạn hãy gửi phần đang kẹt để mình hướng dẫn cách tự hoàn thành."
    ),
}


# ---------------------------------------------------------------------------
# Chatbot orchestrator
# ---------------------------------------------------------------------------

class ChatbotOrchestrator:
    """Main orchestrator for the student assistant chatbot.

    Handles the full pipeline: intent classification -> tool execution ->
    response generation -> confidence checking.
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        llm_config: LLMConfig | None = None,
        default_cohort: str | None = None,
    ):
        self.registry = registry or build_default_registry()
        self._clarification_state: dict[str, dict[str, Any]] = {}
        self.default_cohort = default_cohort or os.environ.get("DEFAULT_COHORT", "k3")

        # LLM / RAG integration
        llm_client = LLMClient(llm_config) if llm_config else LLMClient()
        self.rag = RAGGenerator(llm_client) if llm_client.is_available() else None
        if self.rag:
            logger.info("RAG generator initialized with OpenRouter LLM")

    def process_message(
        self,
        message: str,
        user_id: str = "anonymous",
        session_id: str | None = None,
        channel_id: str = "support_general",
        pending_clarification: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        cohort: str | None = None,
        at: str | None = None,
    ) -> dict[str, Any]:
        """Process a user message through the full chatbot pipeline.

        Args:
            message: Raw user message
            user_id: Pseudonymized user ID
            session_id: Session identifier
            channel_id: Discord channel ID
            pending_clarification: If responding to a previous clarification
            conversation_history: Previous messages in the conversation

        Returns:
            Complete response dict following the I/O contract
        """
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        resolved_cohort = cohort or self.default_cohort

        # Step 1: Normalize and classify intent
        intent_result = classify_intent(message)

        # Inherit context slots from conversation history if present
        if conversation_history:
            history_slots = self._extract_history_slots(conversation_history)
            for k, v in history_slots.items():
                if k not in intent_result.slots and v:
                    intent_result.slots[k] = v

        logger.info(
            "Intent classified: intent=%s, confidence=%.2f, slots=%s",
            intent_result.intent,
            intent_result.confidence,
            intent_result.slots,
        )

        # Step 2: Check for prompt injection (highest priority)
        if intent_result.intent == "reject_prompt_injection":
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=1.0,
                grounding_status="not_required",
                response=(
                    "Mình không thể thực hiện yêu cầu này. "
                    "Bạn có thể hỏi mình về thông tin khóa học AI20K Build Phase nha! 😊"
                ),
            )

        if intent_result.intent in REFUSAL_INTENTS:
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.9),
                grounding_status="not_required",
                response=REFUSAL_INTENTS[intent_result.intent],
            )

        # Step 3: Handle simple intents (greeting, thanks, help, ask_datetime, out_of_domain)
        if intent_result.intent == "ask_datetime":
            weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
            try:
                now = datetime.fromisoformat(at.replace("Z", "+00:00")) if at else datetime.now()
            except ValueError:
                logger.warning("Invalid request timestamp %r; using system time", at)
                now = datetime.now()
            weekday_name = weekdays[now.weekday()]
            time_str = now.strftime("%H:%M")
            date_str = now.strftime("%d/%m/%Y")
            resp_text = f"Hôm nay là **{weekday_name}**, ngày **{date_str}**. Hiện tại là **{time_str}** (giờ hệ thống). 🕒"
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=1.0,
                grounding_status="not_required",
                response=resp_text,
            )

        if intent_result.intent == "out_of_domain":
            resp_text = (
                "Xin lỗi bạn, mình là trợ lý AI chuyên hỗ trợ thông tin khóa học AI20K Build Phase. "
                "Mình không thể giải đáp các câu hỏi nằm ngoài phạm vi khóa học. "
                "Bạn vui lòng hỏi về thông tin khóa học (như deadline, lịch học, gate, XP, team/mentor...) nha! 😊"
            )
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=1.0,
                grounding_status="no_source",
                response=resp_text,
            )

        if intent_result.intent in ("greeting", "thanks", "help"):
            result = generate_response(intent=intent_result.intent, route="ANSWER")
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.9),
                grounding_status="not_required",
                response=result["response"],
            )

        # Step 4: Continue an existing clarification before routing a new intent.
        if pending_clarification:
            return self._handle_clarification_response(
                message=message,
                intent_result=intent_result,
                pending_clarification=pending_clarification,
                message_id=message_id,
                trace_id=trace_id,
                user_id=user_id,
                channel_id=channel_id,
                cohort=resolved_cohort,
                at=at,
            )

        # Step 5: Vague technical reports need one useful detail before handoff.
        if intent_result.intent == "report_issue":
            missing_fields = [
                field
                for field in self._get_required_slots(intent_result.intent)
                if not intent_result.slots.get(field)
            ]
            if missing_fields:
                return self._build_clarification_response(
                    intent_result=intent_result,
                    missing_fields=missing_fields,
                    message_id=message_id,
                    trace_id=trace_id,
                )
            return self._build_authority_escalation(
                intent=intent_result.intent,
                message=message,
                known_context=intent_result.slots,
                message_id=message_id,
                trace_id=trace_id,
            )

        if intent_result.intent in AUTHORITY_INTENTS:
            return self._build_authority_escalation(
                intent=intent_result.intent,
                message=message,
                known_context=intent_result.slots,
                message_id=message_id,
                trace_id=trace_id,
            )

        # Step 6: Execute tool for structured lookup
        if intent_result.intent in INTENT_TOOL_MAP:
            tool_name = INTENT_TOOL_MAP[intent_result.intent]
            tool_args = self._build_tool_args(
                intent_result,
                cohort=resolved_cohort,
                at=at,
            )

            tool_result = self.registry.execute(tool_name, tool_args)

            return self._handle_tool_result(
                tool_result=tool_result,
                intent_result=intent_result,
                message_id=message_id,
                trace_id=trace_id,
                message=message,
            )

        # Step 7: Fallback - search official sources + RAG
        search_result = self.registry.execute(
            "search_official_sources",
            {
                "query": message,
                "category": SEARCH_CATEGORY_BY_INTENT.get(intent_result.intent),
                "at": at,
                "limit": 5,
                "min_score": 2.5,
            },
        )

        return self._handle_search_fallback(
            search_result=search_result,
            intent_result=intent_result,
            message=message,
            message_id=message_id,
            trace_id=trace_id,
        )

    def _build_clarification_response(
        self,
        *,
        intent_result: IntentResult,
        missing_fields: list[str],
        message_id: str,
        trace_id: str,
        attempt_count: int = 1,
        known_slots: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clarification = {
            "missing_field": missing_fields[0],
            "question": self._generate_clarification(intent_result.intent, missing_fields),
            "suggested_replies": self._generate_suggestions(
                intent_result.intent,
                missing_fields,
            ),
            "original_intent": intent_result.intent,
            "attempt_count": attempt_count,
            "known_slots": known_slots if known_slots is not None else intent_result.slots,
        }
        return self._build_response(
            message_id=message_id,
            trace_id=trace_id,
            route="CLARIFY",
            intent=intent_result.intent,
            confidence=max(intent_result.confidence, 0.6),
            grounding_status="no_source",
            response=clarification["question"],
            clarification=clarification,
        )

    def _build_authority_escalation(
        self,
        *,
        intent: str,
        message: str,
        known_context: dict[str, Any],
        message_id: str,
        trace_id: str,
    ) -> dict[str, Any]:
        category_map = {
            "request_deadline_exception": "deadline",
            "request_leave_of_absence": "learning",
            "request_grade_review": "learning",
            "report_issue": "technical",
            "report_harassment": "safety",
        }
        category = category_map.get(intent, "other")

        from .tools import TicketTools
        clean_context = {
            key: value
            for key, value in known_context.items()
            if key in TicketTools.CONTEXT_ALLOWLIST and value
        }
        ticket_tool_result = self.registry.execute(
            "offer_ticket",
            {
                "category": category,
                "question": message,
                "known_context": clean_context,
                "missing_information": [],
                "clarification_attempts": 2,
                "source_ids": [],
            },
        )
        ticket_data = (
            ticket_tool_result.get("data", {})
            if ticket_tool_result.get("status") == "ok"
            else {}
        )
        target_channel = ticket_data.get(
            "target_channel",
            TicketTools.CHANNEL_ALLOWLIST[category],
        )
        response_text = (
            "Yêu cầu này cần Mod/TA có thẩm quyền xử lý.\n\n"
            f"📢 **Kênh gửi ticket**: `#{target_channel}` (dùng lệnh `/ticket`)\n"
            f"📝 **Nội dung đề xuất**: {message.strip()} 🎫"
        )
        return self._build_response(
            message_id=message_id,
            trace_id=trace_id,
            route="ESCALATE",
            intent=intent,
            confidence=0.8,
            grounding_status="no_source",
            response=response_text,
            escalation={
                "reason_code": "requires_human_authority",
                "target": "MOD",
                "target_channel": target_channel,
                "ticket_draft": ticket_data,
                "summary": f"Yêu cầu: {intent}",
                "required_information": [],
            },
        )

    def _extract_history_slots(self, history: list[dict[str, str]]) -> dict[str, Any]:
        """Extract slots from recent conversation history."""
        extracted: dict[str, Any] = {}
        for item in reversed(history):
            if isinstance(item, dict) and item.get("role") == "user":
                res = classify_intent(item.get("content", ""))
                for k, v in res.slots.items():
                    if k not in extracted and v:
                        extracted[k] = v
        return extracted

    def _get_required_slots(self, intent: str) -> list[str]:
        """Get required slots for each intent that needs clarification.

        Only include slots that users are EXPECTED to know or can reasonably provide.
        module is optional for deadline since users typically don't know their module.
        """
        required = {
            "ask_deadline": ["assignment"],  # module is optional
            "ask_event_schedule": ["event_name"],
            "ask_gate": ["gate_name"],
            "ask_exam_slot": ["exam_name"],
            "ask_xp": ["activity"],
            "ask_team_mentor": ["team"],
            "ask_slash_command": ["command"],
            "report_issue": ["operation"],
        }
        return required.get(intent, [])

    def _build_tool_args(
        self,
        intent_result: IntentResult,
        *,
        cohort: str,
        at: str | None,
    ) -> dict[str, Any]:
        """Build tool arguments from intent classification result."""
        slots = intent_result.slots

        if intent_result.intent == "ask_deadline":
            assignment = slots.get("assignment")
            if assignment:
                norm_a = assignment.replace(" ", "_").lower()
                if "ai_log" in norm_a or "ai" in norm_a and "log" in norm_a:
                    assignment = "ai_log"
                elif "demo" in norm_a or "deliverable" in norm_a:
                    assignment = "demo_day_deliverables"
                else:
                    assignment = norm_a
            return {
                "assignment": assignment,
                "module": slots.get("module"),
                "cohort": cohort,
                "at": at,
            }

        if intent_result.intent == "ask_event_schedule":
            return {
                "event_name": slots.get("event_name"),
                "cohort": cohort,
                "at": at,
            }

        if intent_result.intent == "ask_gate":
            gate_name = slots.get("gate_name")
            if gate_name and gate_name.isdigit():
                gate_name = f"cp{gate_name}"
            return {
                "gate_name": gate_name,
                "cohort": cohort,
                "at": at,
            }

        if intent_result.intent == "ask_exam_slot":
            return {
                "exam_name": slots.get("exam_name"),
                "cohort": cohort,
                "team": slots.get("team"),
                "at": at,
            }

        if intent_result.intent == "ask_xp":
            return {
                "activity": slots.get("activity"),
                "cohort": cohort,
                "at": at,
            }

        if intent_result.intent == "ask_team_mentor":
            return {
                "cohort": cohort,
                "team": slots.get("team"),
                "at": at,
            }

        if intent_result.intent == "ask_slash_command":
            return {
                "command": slots.get("command"),
            }

        return {}

    def _handle_tool_result(
        self,
        tool_result: dict[str, Any],
        intent_result: IntentResult,
        message_id: str,
        trace_id: str,
        message: str,
    ) -> dict[str, Any]:
        """Handle the result from tool execution."""
        status = tool_result.get("status", "")
        data = tool_result.get("data")
        citations = tool_result.get("citations", [])
        missing_fields = tool_result.get("missing_fields", [])

        # Missing a required slot always wins over retrieval: never let RAG guess it.
        if status == "ambiguous":
            fields = missing_fields or ["query"]
            return self._build_clarification_response(
                intent_result=intent_result,
                missing_fields=fields,
                message_id=message_id,
                trace_id=trace_id,
            )

        # A complete structured query with no official record must not be rescued
        # by a broad lexical search. Explain the source gap and hand off.
        if status == "not_found":
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ESCALATE",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.7),
                grounding_status="no_source",
                response=(
                    "Mình chưa tìm thấy thông tin này trong nguồn chính thức, "
                    "nên không thể trả lời chắc chắn. Bạn có thể nhờ Mod/TA xác nhận."
                ),
                escalation={
                    "reason_code": "official_source_not_found",
                    "target": "MOD",
                    "summary": message,
                    "required_information": [],
                },
            )

        # Conflict - escalate
        if status == "conflict":
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ESCALATE",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.7),
                grounding_status="no_source",
                response="Có thông tin mâu thuẫn giữa các nguồn. Mình sẽ chuyển cho Mod để xác nhận.",
                escalation={
                    "reason_code": "conflicting_sources",
                    "target": "MOD",
                    "summary": "Nguồn chính thức có thông tin mâu thuẫn.",
                    "required_information": [],
                },
            )

        # Success - format response
        if data:
            result = generate_response(
                intent=intent_result.intent,
                route="ANSWER",
                tool_result=tool_result,
                confidence=intent_result.confidence,
            )
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.8),
                grounding_status="grounded",
                response=result["response"],
                citations=citations,
            )

        # Fallback
        return self._build_response(
            message_id=message_id,
            trace_id=trace_id,
            route="ANSWER",
            intent=intent_result.intent,
            confidence=max(intent_result.confidence, 0.3),
            grounding_status="no_source",
            response="Mình chưa hiểu rõ câu hỏi. Bạn có thể hỏi lại hoặc thử từ khóa khác nha! 😊",
        )

    def _suggest_ticket_response(
        self,
        intent: str,
        message_id: str,
        trace_id: str,
        attempts: int,
        known_context: dict[str, Any],
        missing: list[str],
    ) -> dict[str, Any]:
        """Suggest creating a ticket and provide target ticket channel and ticket question content."""
        cat_map = {
            "ask_deadline": "deadline",
            "ask_event_schedule": "learning",
            "ask_gate": "learning",
            "ask_exam_slot": "learning",
            "ask_xp": "learning",
            "ask_team_mentor": "team_mentor",
            "ask_slash_command": "learning",
            "report_issue": "technical",
            "report_harassment": "safety",
        }
        topic_map = {
            "ask_deadline": "Hạn nộp bài / Deadline",
            "ask_event_schedule": "Lịch sự kiện / Workshop",
            "ask_gate": "Điều kiện Gate / Checkpoint",
            "ask_exam_slot": "Lịch thi / Ca thi",
            "ask_xp": "Quy tắc XP / Thứ hạng",
            "ask_team_mentor": "Thông tin Team / Mentor",
            "ask_slash_command": "Lệnh Discord / Slash Command",
            "report_issue": "Báo lỗi kỹ thuật",
            "report_harassment": "Báo cáo vi phạm",
        }
        category = cat_map.get(intent, "other")
        topic_name = topic_map.get(intent, f"thắc mắc về {intent}")

        # Execute offer_ticket tool in registry
        from .tools import TicketTools
        clean_context = {k: v for k, v in known_context.items() if k in TicketTools.CONTEXT_ALLOWLIST}

        # Build proposed question content for the ticket
        context_parts = [f"{k}: {v}" for k, v in clean_context.items() if v]
        question_content = f"Cần hỗ trợ về {topic_name}"
        if context_parts:
            question_content += f" ({', '.join(context_parts)})"
        if missing:
            question_content += f" — Thông tin cần làm rõ thêm: {', '.join(missing)}"

        ticket_tool_result = self.registry.execute(
            "offer_ticket",
            {
                "category": category,
                "question": question_content,
                "known_context": clean_context,
                "missing_information": missing,
                "clarification_attempts": max(attempts, 2),
                "source_ids": [],
            },
        )

        ticket_data = ticket_tool_result.get("data", {}) if ticket_tool_result.get("status") == "ok" else {}
        target_channel = ticket_data.get("target_channel", "student-support")

        response_text = (
            f"Gợi ý gửi ticket hỗ trợ tới Mod/TA:\n\n"
            f"📢 **Kênh gửi ticket**: `#{target_channel}` (dùng lệnh `/ticket`)\n"
            f"📝 **Nội dung câu hỏi đề xuất**: {question_content} 🎫"
        )

        escalation_info = {
            "reason_code": "unresolved_after_clarifications",
            "target": "MOD",
            "target_channel": target_channel,
            "clarification_attempts": attempts,
            "known_context": known_context,
            "missing_information": missing,
            "ticket_draft": ticket_data,
            "summary": f"Không tìm thấy câu trả lời sau {attempts} lần hỏi làm rõ.",
        }

        return self._build_response(
            message_id=message_id,
            trace_id=trace_id,
            route="ESCALATE",
            intent=intent,
            confidence=0.9,
            grounding_status="no_source",
            response=response_text,
            escalation=escalation_info,
        )

    def _handle_clarification_response(
        self,
        message: str,
        intent_result: IntentResult,
        pending_clarification: dict[str, Any],
        message_id: str,
        trace_id: str,
        user_id: str,
        channel_id: str,
        cohort: str,
        at: str | None,
    ) -> dict[str, Any]:
        """Handle user response to a clarification question."""
        current_attempt = pending_clarification.get("attempt_count", 1)
        original_intent = pending_clarification.get("original_intent", intent_result.intent)

        # Merge new slots with existing known slots from pending clarification
        merged_slots = dict(pending_clarification.get("known_slots", {}))
        merged_slots.update(intent_result.slots)

        # Handle correction phrases (e.g. "không phải, là WA3")
        normalized_msg = normalize_vietnamese(message)
        clean_msg = normalized_msg
        for prefix in ["khong phai", "sai roi", "sua lai", "y minh la", "y em la", "chinh lai"]:
            if clean_msg.startswith(prefix):
                clean_msg = clean_msg[len(prefix):].strip()
                break

        # Try to fill the missing field from user response
        missing_field = pending_clarification.get("missing_field")
        non_answers = {
            "khong biet",
            "khong biet nua",
            "van khong biet",
            "van khong biet ne",
            "khong ro",
            "chịu",
            "chiu",
        }
        is_non_answer = clean_msg in non_answers or len(clean_msg) < 2
        if (
            missing_field
            and not is_non_answer
            and (missing_field not in merged_slots or clean_msg != normalized_msg)
        ):
            merged_slots[missing_field] = clean_msg

        # Check if required slots are now satisfied
        required_slots = self._get_required_slots(original_intent)
        still_missing = [s for s in required_slots if not merged_slots.get(s)]

        new_intent = IntentResult(
            intent=original_intent,
            confidence=max(intent_result.confidence, 0.7),
            slots=merged_slots,
            normalized_query=intent_result.normalized_query,
        )

        if still_missing:
            if current_attempt >= 2:
                # Ask back >= 2 times with no resolution -> offer ticket & channel
                return self._suggest_ticket_response(
                    intent=original_intent,
                    message_id=message_id,
                    trace_id=trace_id,
                    attempts=current_attempt,
                    known_context=merged_slots,
                    missing=still_missing,
                )
            else:
                clarification = {
                    "missing_field": still_missing[0],
                    "question": self._generate_clarification(original_intent, still_missing),
                    "suggested_replies": self._generate_suggestions(original_intent, still_missing),
                    "original_intent": original_intent,
                    "attempt_count": current_attempt + 1,
                    "known_slots": merged_slots,
                }
                return self._build_response(
                    message_id=message_id,
                    trace_id=trace_id,
                    route="CLARIFY",
                    intent=original_intent,
                    confidence=max(intent_result.confidence, 0.6),
                    grounding_status="no_source",
                    response=clarification["question"],
                    clarification=clarification,
                )

        if new_intent.intent == "report_issue":
            return self._build_authority_escalation(
                intent=new_intent.intent,
                message=message,
                known_context=merged_slots,
                message_id=message_id,
                trace_id=trace_id,
            )

        # Execute tool with merged slots
        if new_intent.intent in INTENT_TOOL_MAP:
            tool_name = INTENT_TOOL_MAP[new_intent.intent]
            tool_args = self._build_tool_args(
                new_intent,
                cohort=cohort,
                at=at,
            )

            tool_result = self.registry.execute(tool_name, tool_args)

            return self._handle_tool_result(
                tool_result=tool_result,
                intent_result=new_intent,
                message_id=message_id,
                trace_id=trace_id,
                message=message,
            )

        if current_attempt >= 2:
            return self._suggest_ticket_response(
                intent=original_intent,
                message_id=message_id,
                trace_id=trace_id,
                attempts=current_attempt,
                known_context=merged_slots,
                missing=still_missing,
            )

        return self._build_response(
            message_id=message_id,
            trace_id=trace_id,
            route="ANSWER",
            intent=new_intent.intent,
            confidence=new_intent.confidence,
            grounding_status="no_source",
            response="Mình cần thêm thông tin để hỗ trợ bạn. Bạn có thể hỏi lại được không?",
        )

    def _handle_search_fallback(
        self,
        search_result: dict[str, Any],
        intent_result: IntentResult,
        message: str,
        message_id: str,
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle fallback search when no specific intent matches.

        Uses RAG generator when available for natural language responses.
        Falls back to template-based response when LLM is unavailable.
        """
        status = search_result.get("status", "")
        data = search_result.get("data")
        citations = search_result.get("citations", [])

        # Try RAG generation when we have search results and LLM is available
        if status == "ok" and data and self.rag:
            # Build context chunks from BM25 results
            context_chunks = []
            for i, item in enumerate(data):
                chunk = {
                    "source_id": item.get("source_id", ""),
                    "category": item.get("category", ""),
                    "score": item.get("score", 0),
                    "attributes": item.get("attributes", {}),
                }
                if i < len(citations):
                    chunk["quote"] = citations[i].get("quote", "")
                context_chunks.append(chunk)

            rag_result = self.rag.generate(
                query=message,
                context_chunks=context_chunks,
                intent=intent_result.intent,
            )

            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent="search_fallback",
                confidence=max(intent_result.confidence, 0.5),
                grounding_status="grounded" if rag_result.get("grounded") else "partial",
                response=rag_result["response"],
                citations=citations,
            )

        # Fallback: template-based response (no LLM or no search results)
        if status == "ok" and data:
            response_parts = ["Mình tìm thấy thông tin liên quan từ tài liệu khóa học:\n"]
            for i, item in enumerate(data[:3], 1):
                title = citations[i - 1].get("title") if i - 1 < len(citations) else item.get("source_id", "")
                quote = citations[i - 1].get("quote", "") if i - 1 < len(citations) else ""
                if quote:
                    response_parts.append(f"📌 **{title}**:\n{quote}\n")
                else:
                    response_parts.append(f"📌 **{title}**\n")

            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent="search_fallback",
                confidence=0.5,
                grounding_status="grounded",
                response="\n".join(response_parts),
                citations=citations,
            )

        # A recognized, specific topic with no matching official category is a
        # source gap, not an invitation for the model to guess.
        if intent_result.intent in SEARCH_CATEGORY_BY_INTENT:
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ESCALATE",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.7),
                grounding_status="no_source",
                response=(
                    "Mình chưa tìm thấy thông tin này trong nguồn chính thức, "
                    "nên không thể trả lời chắc chắn. Bạn có thể nhờ Mod/TA xác nhận."
                ),
                escalation={
                    "reason_code": "official_source_not_found",
                    "target": "MOD",
                    "summary": message,
                    "required_information": [],
                },
            )

        # Unknown topic with no results: ask the user to narrow the query.
        clarification = {
            "missing_field": "query",
            "question": "Mình chưa hiểu rõ câu hỏi hoặc chưa tìm thấy thông tin phù hợp trong nguồn chính thức. Bạn có thể nói rõ hơn chủ đề bạn đang cần không? (VD: deadline bài nộp, lịch workshop, XP/rank, team/mentor...)",
            "suggested_replies": ["Deadline bài nộp", "Lịch sự kiện / Workshop", "XP & Rank", "Kênh hỗ trợ / Ticket"],
            "original_intent": "unknown",
            "attempt_count": 1,
            "known_slots": {},
        }
        return self._build_response(
            message_id=message_id,
            trace_id=trace_id,
            route="CLARIFY",
            intent="unknown",
            confidence=0.2,
            grounding_status="no_source",
            response=clarification["question"],
            clarification=clarification,
        )

    def _generate_clarification(self, intent: str, missing_fields: list[str]) -> str:
        """Generate clarification question based on missing fields."""
        field_questions = {
            "assignment": "Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...)",
            "module": "Bạn đang học module nào?",
            "event_name": "Bạn muốn biết về sự kiện nào? (Workshop, Office Hours, Mentoring...)",
            "gate_name": "Bạn muốn biết về gate nào? (CP1, CP2, CP3...)",
            "exam_name": "Bạn muốn biết về kỳ thi nào?",
            "team": "Bạn thuộc team nào?",
            "activity": "Bạn muốn biết XP của hoạt động nào?",
            "command": "Bạn muốn biết về lệnh nào?",
            "operation": (
                "Bạn gặp lỗi khi đang làm thao tác nào? "
                "(VD: đăng nhập, nộp bài, tải slide hoặc mở link)"
            ),
            "query": "Bạn có thể nói rõ hơn về vấn đề cần hỗ trợ không?",
        }

        for field in missing_fields:
            if field in field_questions:
                return field_questions[field]

        return "Bạn có thể cung cấp thêm thông tin được không?"

    def _generate_suggestions(self, intent: str, missing_fields: list[str]) -> list[str]:
        """Generate suggested replies."""
        suggestions = {
            "ask_deadline": {
                "assignment": ["Weekly Assignment", "AI Log", "Demo Day deliverables"],
            },
            "ask_event_schedule": {
                "event_name": ["Workshop", "Office Hours", "Menting Duty", "Demo Day"],
            },
            "ask_gate": {
                "gate_name": ["CP1", "CP2", "CP3", "Final Gate"],
            },
            "ask_xp": {
                "activity": ["Daily checkin", "Weekly submit", "Peer review", "Gate pass"],
            },
            "ask_slash_command": {
                "command": ["/daily", "/weekly", "/exam", "/gate", "/myteam", "/rank", "/ticket", "/ask"],
            },
            "report_issue": {
                "operation": ["Đăng nhập", "Nộp bài", "Tải tài liệu", "Mở link"],
            },
        }

        if intent in suggestions:
            for field in missing_fields:
                if field in suggestions[intent]:
                    return suggestions[intent][field]

        return []

    def _build_response(
        self,
        message_id: str,
        trace_id: str,
        route: str,
        intent: str,
        confidence: float,
        grounding_status: str,
        response: str,
        citations: list[dict[str, Any]] | None = None,
        clarification: dict[str, Any] | None = None,
        escalation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the final response dict following the I/O contract."""
        return {
            "schema_version": "1.0",
            "message_id": message_id,
            "route": route,
            "intent": intent,
            "confidence": confidence,
            "grounding_status": grounding_status,
            "response": response,
            "clarification": clarification,
            "citations": citations or [],
            "escalation": escalation,
            "trace_id": trace_id,
        }
