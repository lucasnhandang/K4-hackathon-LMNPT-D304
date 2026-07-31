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
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .intent_classifier import (
    REQUESTED_FACT_PATTERNS,
    IntentResult,
    classify_intent,
    normalize_vietnamese,
)
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
    "ask_attendance_policy": "policy_attendance",
    "ask_online_learning_availability": "policy_online",
    "ask_laptop_requirements": "policy_laptop",
    "ask_submission_channel": "submission_channel",
    "ask_learning_material": "learning_material",
    "ask_team_naming": "team_naming",
    "ask_topic_availability": "topic_availability",
    "ask_holiday_schedule": "holiday_schedule",
    "ask_scholarship_info": "scholarship_info",
}

AUTHORITY_INTENTS = {
    "request_deadline_exception",
    "request_leave_of_absence",
    "request_grade_review",
    "request_team_change",
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

AGENT_ROUTABLE_INTENTS = {
    "greeting",
    "thanks",
    "help",
    "ask_datetime",
    "out_of_domain",
    "ask_attendance_policy",
    "ask_online_learning_availability",
    "ask_laptop_requirements",
    "ask_submission_channel",
    "ask_learning_material",
    "ask_team_naming",
    "ask_topic_availability",
    "ask_holiday_schedule",
    "ask_scholarship_info",
    "ask_deadline",
    "ask_event_schedule",
    "ask_gate",
    "ask_exam_slot",
    "ask_xp",
    "ask_team_mentor",
    "ask_slash_command",
    "request_deadline_exception",
    "request_leave_of_absence",
    "request_grade_review",
    "request_team_change",
    "report_issue",
    "report_harassment",
    "reject_answer_key_request",
    "reject_do_assignment_for_user",
    "in_scope_unknown",
}

AGENT_SLOT_ALLOWLIST = {
    "assignment",
    "module",
    "event_name",
    "gate_name",
    "requested_fact",
    "exam_name",
    "team",
    "activity",
    "command",
    "operation",
}

COURSE_RELEVANCE_TERMS = {
    "ai20k",
    "khoa hoc",
    "lop hoc",
    "hoc vien",
    "mentor",
    "mod",
    "deadline",
    "bai tap",
    "bai nop",
    "nop bai",
    "workshop",
    "office hour",
    "mentoring",
    "gate",
    "checkpoint",
    "xp",
    "team",
    "nhom",
    "ca thi",
    "lich thi",
    "chuyen can",
    "nghi hoc",
    "hoc bong",
    "tai lieu hoc",
    "slide",
    "codelab",
    "jira",
    "discord",
    "kenh ho tro",
    "weekly",
    "demo day",
    "project",
    "do an",
    "giang vien",
    "truong",
    "phong lab",
    "campus",
    "lich hoc",
}

AGENT_ROUTER_TOOL = {
    "type": "function",
    "function": {
        "name": "route_student_request",
        "description": (
            "Classify a student message by course relevance and choose exactly "
            "one supported intent. This tool only proposes a route; application "
            "code enforces policy and executes knowledge tools."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["in_scope", "out_of_scope"],
                },
                "intent": {
                    "type": "string",
                    "enum": sorted(AGENT_ROUTABLE_INTENTS),
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "slots": {
                    "type": "object",
                    "properties": {
                        name: {"type": ["string", "null"]}
                        for name in sorted(AGENT_SLOT_ALLOWLIST)
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["scope", "intent", "confidence", "slots"],
            "additionalProperties": False,
        },
    },
}

AGENT_ROUTER_PROMPT = """\
Bạn là semantic router cho trợ lý học viên AI20K.

Phạm vi in_scope gồm: lịch/deadline/gate/XP/team/mentor/thi; nội quy và vận hành
khóa học; tài liệu học; nộp bài; công cụ học tập; lỗi kỹ thuật khi học; yêu cầu
ngoại lệ cần Mod/TA; câu hỏi có liên quan rõ ràng tới khóa học nhưng kho tri thức
có thể chưa có.

Phạm vi out_of_scope gồm: thời tiết, tin tức, giải trí, chính trị, mua sắm, kiến
thức đời sống hoặc câu hỏi kỹ thuật/lập trình chung không gắn với khóa học.

Quy tắc:
- out_of_scope phải dùng intent=out_of_domain.
- Câu hỏi liên quan khóa học nhưng chưa khớp intent cụ thể dùng
  intent=in_scope_unknown; không đánh dấu out_of_scope chỉ vì có thể thiếu dữ liệu.
- Chọn intent cụ thể khi có thể. Trích slot chỉ từ nội dung người dùng.
- Với gate/checkpoint, luôn dùng intent=ask_gate và tách thuộc tính cần hỏi vào
  requested_fact: requirements, deadline, submission_method, grading hoặc general.
  Ví dụ "deadline gate 3" => gate_name=cp3, requested_fact=deadline.
- Hiểu tiếng chat theo ngữ cảnh: "gate nộp bao h" nghĩa là hỏi deadline nhưng
  còn thiếu gate_name; "gate 3 nộp ở đâu" hỏi submission_method.
- Tin nhắn sửa ý như "tôi hỏi deadline cơ mà" phải cập nhật requested_fact và giữ
  gate_name từ lịch sử nếu lịch sử đã xác định gate.
- Không trả lời câu hỏi và không tự gọi Mod; chỉ gọi route_student_request.

Nhóm intent chính:
- ask_deadline/event_schedule/gate/exam_slot/xp/team_mentor/slash_command:
  tra thông tin vận hành có cấu trúc.
- ask_attendance_policy/online_learning_availability/laptop_requirements/
  submission_channel/learning_material/team_naming/topic_availability/
  holiday_schedule/scholarship_info: tra tài liệu chính thức.
- request_deadline_exception/leave_of_absence/grade_review/team_change và
  report_issue/report_harassment: cần quy trình hoặc thẩm quyền hỗ trợ.
- greeting/thanks/help/ask_datetime: hội thoại đơn giản.
"""


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
        llm_client: LLMClient | None = None,
    ):
        self.registry = registry or build_default_registry()
        self._clarification_state: dict[str, dict[str, Any]] = {}
        self.default_cohort = default_cohort or os.environ.get("DEFAULT_COHORT", "k4")

        # LLM / RAG integration
        self.llm_client = (
            llm_client
            or (LLMClient(llm_config) if llm_config else LLMClient())
        )
        self.rag = (
            RAGGenerator(self.llm_client)
            if self.llm_client.is_available()
            else None
        )
        if self.rag:
            logger.info(
                "Hybrid agent router initialized with OpenRouter model=%s",
                self.llm_client.config.model,
            )

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
        """Route with OpenRouter when available, then enforce local policy/tools."""
        deterministic = classify_intent(message)
        routed_intent, agent_metadata = self._route_with_agent(
            message=message,
            deterministic=deterministic,
            conversation_history=conversation_history,
        )
        routed_intent = self._normalize_gate_frame(routed_intent, deterministic)
        if agent_metadata and isinstance(agent_metadata.get("decision"), dict):
            agent_metadata["decision"].update(
                {
                    "intent": routed_intent.intent,
                    "confidence": routed_intent.confidence,
                    "slots": routed_intent.slots,
                }
            )
        result = self._process_message_core(
            message=message,
            user_id=user_id,
            session_id=session_id,
            channel_id=channel_id,
            pending_clarification=pending_clarification,
            conversation_history=conversation_history,
            cohort=cohort,
            at=at,
            intent_result_override=routed_intent,
        )
        if agent_metadata:
            result["llm"] = self._merge_llm_metadata(
                agent_metadata,
                result.get("llm"),
            )
        return result

    def _process_message_core(
        self,
        message: str,
        user_id: str = "anonymous",
        session_id: str | None = None,
        channel_id: str = "support_general",
        pending_clarification: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        cohort: str | None = None,
        at: str | None = None,
        intent_result_override: IntentResult | None = None,
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
        intent_result = intent_result_override or classify_intent(message)

        # Inherit context slots from conversation history if present
        if conversation_history:
            history_slots = self._extract_history_slots(conversation_history)
            for k, v in history_slots.items():
                if k not in intent_result.slots and v:
                    intent_result.slots[k] = v

        # A correction can mention only the fact ("tôi hỏi deadline cơ mà")
        # while relying on the gate identified in the previous turn.
        normalized_current = intent_result.normalized_query
        is_correction = bool(
            re.search(
                r"\b(?:toi|minh|em)\s*hoi\b.*\bco\s*ma\b|"
                r"\b(?:y\s*(?:toi|minh|em)\s*la|sua\s*lai|khong\s*phai)\b",
                normalized_current,
            )
        )
        if (
            is_correction
            and intent_result.intent == "ask_deadline"
            and intent_result.slots.get("gate_name")
        ):
            intent_result = IntentResult(
                intent="ask_gate",
                confidence=max(intent_result.confidence, 0.7),
                slots={**intent_result.slots, "requested_fact": "deadline"},
                normalized_query=normalized_current,
            )

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

        # An unclassified statement is too weak a retrieval query. Asking for a
        # topic prevents common words from producing an unrelated BM25 answer.
        if intent_result.intent == "unknown":
            return self._build_clarification_response(
                intent_result=IntentResult(
                    intent="unknown",
                    confidence=intent_result.confidence,
                    slots=intent_result.slots,
                    normalized_query=intent_result.normalized_query,
                ),
                missing_fields=["query"],
                message_id=message_id,
                trace_id=trace_id,
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
                "required_terms": self._retrieval_anchor_terms(
                    intent_result.normalized_query
                ),
            },
        )

        return self._handle_search_fallback(
            search_result=search_result,
            intent_result=intent_result,
            message=message,
            message_id=message_id,
            trace_id=trace_id,
        )

    def _route_with_agent(
        self,
        *,
        message: str,
        deterministic: IntentResult,
        conversation_history: list[dict[str, str]] | None,
    ) -> tuple[IntentResult, dict[str, Any] | None]:
        """Use a forced OpenRouter tool call for semantic routing.

        Prompt-injection and academic-integrity refusals stay entirely local.
        All model output is treated as an untrusted proposal and validated
        against explicit intent/slot allowlists before it can affect routing.
        """
        protected_intents = {
            "reject_prompt_injection",
            "report_harassment",
            "report_issue",
            *AUTHORITY_INTENTS,
            *REFUSAL_INTENTS,
        }
        if (
            not self.llm_client.is_available()
            or deterministic.intent in protected_intents
        ):
            return deterministic, None

        history_lines: list[str] = []
        for item in (conversation_history or [])[-4:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                history_lines.append(f"{role}: {content[:500]}")

        user_content = f"Tin nhắn hiện tại:\n{message[:2000]}"
        if history_lines:
            user_content = (
                "Lịch sử gần nhất:\n"
                + "\n".join(history_lines)
                + "\n\n"
                + user_content
            )

        try:
            response = self.llm_client.chat(
                [
                    {"role": "system", "content": AGENT_ROUTER_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.0,
                max_tokens=300,
                tools=[AGENT_ROUTER_TOOL],
                tool_choice={
                    "type": "function",
                    "function": {"name": "route_student_request"},
                },
                parallel_tool_calls=False,
            )
            arguments = self._extract_agent_route_arguments(response)
            routed = self._validated_agent_intent(arguments, deterministic)
            metadata = {
                "called": True,
                "provider": "openrouter",
                "status": "success",
                "model": response.model,
                "usage": response.usage,
                "stage": "agent_router",
                "decision": {
                    "scope": arguments["scope"],
                    "intent": routed.intent,
                    "confidence": routed.confidence,
                    "slots": routed.slots,
                },
            }
            return routed, metadata
        except Exception as error:
            logger.warning(
                "OpenRouter agent routing failed; using deterministic fallback: %s",
                error,
            )
            return deterministic, {
                "called": True,
                "provider": "openrouter",
                "status": "error",
                "model": self.llm_client.config.model,
                "usage": {},
                "stage": "agent_router",
            }

    @staticmethod
    def _normalize_gate_frame(
        routed: IntentResult,
        deterministic: IntentResult,
    ) -> IntentResult:
        """Preserve the gate subject and requested fact across hybrid routing."""
        if deterministic.intent != "ask_gate":
            return routed
        if routed.intent not in {
            "ask_gate",
            "ask_deadline",
            "ask_submission_channel",
        }:
            return routed

        # When the subject is a gate, discard slots from the competing deadline
        # frame (for example assignment="gate"). Only the two gate dimensions
        # may survive semantic reconciliation.
        slots = {
            key: value
            for key, value in routed.slots.items()
            if key in {"gate_name", "requested_fact"}
        }
        slots.update(
            {
                key: value
                for key, value in deterministic.slots.items()
                if value and key in {"gate_name", "requested_fact"}
            }
        )
        return IntentResult(
            intent="ask_gate",
            confidence=max(routed.confidence, deterministic.confidence),
            slots=slots,
            normalized_query=deterministic.normalized_query,
        )

    @staticmethod
    def _extract_agent_route_arguments(response: Any) -> dict[str, Any]:
        """Extract the forced routing tool arguments from an LLM response."""
        for call in response.tool_calls:
            function = call.get("function") if isinstance(call, dict) else None
            if not isinstance(function, dict):
                continue
            if function.get("name") != "route_student_request":
                continue
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if isinstance(arguments, dict):
                return arguments

        # A few providers return valid JSON content even with a forced tool.
        content = (response.content or "").strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Agent router response is not an object")
        return parsed

    @staticmethod
    def _validated_agent_intent(
        arguments: dict[str, Any],
        deterministic: IntentResult,
    ) -> IntentResult:
        """Validate and reconcile an untrusted semantic route proposal."""
        scope = arguments.get("scope")
        intent = arguments.get("intent")
        confidence_raw = arguments.get("confidence", 0.0)
        slots_raw = arguments.get("slots", {})

        if scope not in {"in_scope", "out_of_scope"}:
            raise ValueError("Agent returned an invalid scope")
        if intent not in AGENT_ROUTABLE_INTENTS:
            raise ValueError("Agent returned an unsupported intent")
        try:
            confidence = min(1.0, max(0.0, float(confidence_raw)))
        except (TypeError, ValueError) as error:
            raise ValueError("Agent returned invalid confidence") from error

        if scope == "out_of_scope":
            return IntentResult(
                intent="out_of_domain",
                confidence=max(confidence, 0.8),
                slots={},
                normalized_query=deterministic.normalized_query,
            )

        if intent == "out_of_domain":
            intent = "in_scope_unknown"

        if (
            intent == "in_scope_unknown"
            and not any(
                term in deterministic.normalized_query
                for term in COURSE_RELEVANCE_TERMS
            )
        ):
            # A bare semantic claim without any course anchor is insufficient
            # evidence for handing a question to Mod. Ask the user to clarify
            # instead; a follow-up can establish the missing course context.
            return IntentResult(
                intent="unknown",
                confidence=min(confidence, 0.4),
                slots={},
                normalized_query=deterministic.normalized_query,
            )

        # Human-authority and technical-support patterns are safety-sensitive;
        # keep a strong deterministic result even when the model disagrees.
        if (
            deterministic.intent in AUTHORITY_INTENTS | {"report_issue"}
            and deterministic.confidence >= 0.5
        ):
            return deterministic

        # Explicit structured anchors such as "deadline", "gate" or "XP" are
        # stronger routing evidence than a semantic proposal. In particular,
        # never let the agent turn an incomplete structured question into a
        # broad search intent: the structured branch must validate its required
        # slots and clarify instead of letting BM25 guess an unrelated record.
        if (
            deterministic.intent in INTENT_TOOL_MAP
            and deterministic.confidence >= CONFIDENCE_MEDIUM
        ):
            intent = deterministic.intent
            confidence = max(confidence, deterministic.confidence)

        slots = dict(deterministic.slots)
        if isinstance(slots_raw, dict):
            for key, value in slots_raw.items():
                # Direct extraction from the current message is stronger
                # evidence than an agent proposal. Never overwrite it.
                if slots.get(key):
                    continue
                if (
                    key in AGENT_SLOT_ALLOWLIST
                    and (isinstance(value, str) or value is None)
                    and value
                ):
                    sanitized = ChatbotOrchestrator._sanitize_agent_slot(
                        intent=intent,
                        key=key,
                        value=value,
                        normalized_query=deterministic.normalized_query,
                    )
                    if sanitized:
                        slots[key] = sanitized

        return IntentResult(
            intent=intent,
            confidence=round(confidence, 2),
            slots=slots,
            normalized_query=deterministic.normalized_query,
        )

    @staticmethod
    def _sanitize_agent_slot(
        *,
        intent: str,
        key: str,
        value: str,
        normalized_query: str,
    ) -> str | None:
        """Canonicalize agent slots and reject generic or invented values."""
        cleaned = normalize_vietnamese(value)[:200]
        if key == "requested_fact":
            fact = cleaned.replace(" ", "_")
            pattern = REQUESTED_FACT_PATTERNS.get(fact)
            return fact if pattern and re.search(pattern, normalized_query) else None

        if intent == "ask_gate" and key == "gate_name":
            gate_match = re.fullmatch(
                r"(?:gate|checkpoint)\s*(?:so\s*)?([1-4])",
                cleaned,
            )
            cp_match = re.fullmatch(r"cp\s*([1-4])", cleaned)
            if gate_match or cp_match:
                number = (gate_match or cp_match).group(1)
                evidence_patterns = (
                    rf"\bcp\s*{number}\b",
                    rf"\bgate\s*{number}\b",
                    rf"\bgate\s*so\s*{number}\b",
                    rf"\bcheckpoint\s*{number}\b",
                    rf"\bcheckpoint\s*so\s*{number}\b",
                )
                if any(re.search(pattern, normalized_query) for pattern in evidence_patterns):
                    return f"cp{number}"
                return None

            if cleaned in {"final", "final gate", "gate cuoi", "checkpoint cuoi"}:
                if re.search(
                    r"\bfinal(?:\s*gate)?\b|\bgate\s*cuoi\b|\bcheckpoint\s*cuoi\b",
                    normalized_query,
                ):
                    return "final"
                return None

            # Values such as "gate", "checkpoint", "yêu cầu" are topics, not IDs.
            return None

        # All other model-proposed slots are untrusted as well. Only accept a
        # value explicitly evidenced by the current message. Canonical aliases
        # such as WA3 remain handled by the deterministic slot extractor.
        normalized_value = normalize_vietnamese(value.replace("_", " "))[:200]
        if normalized_value and normalized_value in normalized_query:
            return value.strip()[:200]
        return None

    @staticmethod
    def _merge_llm_metadata(
        router: dict[str, Any],
        generator: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Combine routing and answer-generation calls for one trace."""
        if not generator:
            return router

        stages = []
        for item in (router, generator):
            stages.append(
                {
                    "stage": item.get("stage", "answer_generator"),
                    "status": item.get("status", "unknown"),
                    "model": item.get("model"),
                    "usage": item.get("usage", {}),
                }
            )

        usage_keys = ("prompt_tokens", "completion_tokens", "total_tokens")
        usage = {
            key: sum(
                int((item.get("usage") or {}).get(key, 0) or 0)
                for item in (router, generator)
            )
            for key in usage_keys
        }
        statuses = {item.get("status") for item in (router, generator)}
        status = "success" if statuses == {"success"} else "partial"
        return {
            "called": True,
            "provider": "openrouter",
            "status": status,
            "model": generator.get("model") or router.get("model"),
            "usage": usage,
            "stage": "hybrid_pipeline",
            "stages": stages,
            "decision": router.get("decision"),
        }

    @staticmethod
    def _retrieval_anchor_terms(normalized_query: str) -> list[str]:
        """Keep named resources from being dropped by broad lexical matching."""
        anchors: list[str] = []
        for named_resource in ("jira", "codelab", "codelabs", "hackathon"):
            if named_resource in normalized_query:
                anchors.append(named_resource)

        workshop_match = re.search(r"\bworkshop\s*(\d+)\b", normalized_query)
        if workshop_match:
            anchors.extend(["workshop", workshop_match.group(1)])
        return anchors

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
            "question": self._generate_clarification(
                intent_result.intent,
                missing_fields,
                intent_result.slots,
            ),
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
            "request_team_change": "learning",
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
                elif norm_a in {
                    "weekly_submit",
                    "/weekly_submit",
                    "weekly_report",
                    "weekly_assignment",
                    "bao_cao_tuan",
                }:
                    assignment = "weekly_report"
                elif "deliverable" in norm_a:
                    assignment = "demo_day_deliverables"
                elif norm_a in {"demo", "demo_day"}:
                    assignment = "demo_day"
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
                "requested_fact": slots.get("requested_fact") or "requirements",
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
            activity = slots.get("activity")
            if activity and "tong diem kinh nghiem" in normalize_vietnamese(activity):
                activity = "rank"
            elif activity and "mentor" in normalize_vietnamese(activity):
                activity = "mentoring_duty"
            return {
                "activity": activity,
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
            command = slots.get("command")
            if command and normalize_vietnamese(command) == "bao cao tuan":
                command = "/weekly"
            return {
                "command": command,
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

        # A record about the right gate can still lack the exact fact asked
        # for. This is a related knowledge gap, not a grounded answer.
        if status == "unsupported":
            requested_fact = intent_result.slots.get("requested_fact", "information")
            gate_name = intent_result.slots.get("gate_name", "gate này")
            fact_labels = {
                "deadline": "deadline",
                "requirements": "yêu cầu",
                "submission_method": "cách nộp",
                "grading": "cách chấm điểm",
                "general": "thông tin",
            }
            fact_label = fact_labels.get(requested_fact, "thông tin")
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ESCALATE",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.7),
                grounding_status="no_source",
                response=(
                    f"Mình hiểu bạn đang hỏi {fact_label} của {str(gate_name).upper()}. "
                    "Nguồn hiện tại có thông tin về gate này nhưng chưa có dữ liệu "
                    f"{fact_label} chính thức. Bạn có thể nhờ Mod/TA xác nhận."
                ),
                # The checked record does not support the requested claim, so
                # it must not be presented as an answer citation.
                citations=[],
                escalation={
                    "reason_code": "related_knowledge_gap",
                    "target": "MOD",
                    "summary": message,
                    "required_information": [requested_fact],
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
                response=(
                    "Có thông tin mâu thuẫn giữa các nguồn chính thức. "
                    "Bạn có thể nhờ Mod/TA xác nhận trước khi sử dụng thông tin này."
                ),
                escalation={
                    "reason_code": "conflicting_sources",
                    "target": "MOD",
                    "summary": "Nguồn chính thức có thông tin mâu thuẫn.",
                    "required_information": [],
                },
            )

        # Success - format response
        if data:
            template_result = generate_response(
                intent=intent_result.intent,
                route="ANSWER",
                tool_result=tool_result,
                confidence=intent_result.confidence,
            )
            response_text = template_result["response"]
            llm_metadata: dict[str, Any] | None = None

            # Structured tools remain the source of truth, while OpenRouter turns
            # their machine-readable result into a natural Vietnamese answer.
            if self.rag:
                data_items = data if isinstance(data, list) else [data]
                context_chunks = []
                for index, item in enumerate(data_items):
                    if not isinstance(item, dict):
                        continue
                    citation = citations[index] if index < len(citations) else {}
                    context_chunks.append(
                        {
                            "source_id": citation.get("source_id", f"structured_tool_{index + 1}"),
                            "category": intent_result.intent,
                            "score": 1.0,
                            "attributes": item,
                            "quote": citation.get("quote", ""),
                        }
                    )

                rag_result = self.rag.generate(
                    query=message,
                    context_chunks=context_chunks,
                    intent=intent_result.intent,
                    extra_instructions=(
                        "Diễn đạt tự nhiên kết quả từ công cụ có cấu trúc. "
                        "Giữ nguyên tuyệt đối mọi số liệu, thời gian, tên và kênh."
                    ),
                )
                llm_status = (
                    "success"
                    if rag_result.get("model") not in ("none", "error")
                    else "error"
                )
                llm_metadata = {
                    "called": True,
                    "provider": "openrouter",
                    "status": llm_status,
                    "model": rag_result.get("model", "unknown"),
                    "usage": rag_result.get("usage", {}),
                    "stage": "answer_generator",
                }
                if llm_status == "success" and rag_result.get("response"):
                    response_text = rag_result["response"]

            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ANSWER",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.8),
                grounding_status="grounded",
                response=response_text,
                citations=citations,
                llm=llm_metadata,
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
        if category == "other" and ("assignment" in missing or "assignment" in known_context or "deadline" in intent):
            category = "deadline"
            topic_name = "Hạn nộp bài / Deadline"
        else:
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
        priority = ticket_data.get("priority", "NORMAL")
        priority_tag = "🔴 URGENT (Ưu tiên cao - Xử lý ngay)" if priority == "URGENT" else "🔵 NORMAL (Bình thường)"

        response_text = (
            f"Gợi ý gửi ticket hỗ trợ tới Mod/TA:\n\n"
            f"🚨 **Độ ưu tiên**: {priority_tag}\n"
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
                    "question": self._generate_clarification(
                        original_intent,
                        still_missing,
                        merged_slots,
                    ),
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
            llm_status = (
                "success"
                if rag_result.get("model") not in ("none", "error")
                else "error"
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
                llm={
                    "called": True,
                    "provider": "openrouter",
                    "status": llm_status,
                    "model": rag_result.get("model", "unknown"),
                    "usage": rag_result.get("usage", {}),
                    "stage": "answer_generator",
                },
            )

        # Fallback: template-based response (no LLM or no search results)
        if status == "ok" and data:
            top_score = max(float(item.get("score", 0.0)) for item in data)
            retrieval_confidence = min(
                0.95,
                max(intent_result.confidence, 0.7 + top_score / 30),
            )
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
                confidence=retrieval_confidence,
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

        # The semantic agent confirmed course relevance, but retrieval found no
        # official source. This is a genuine knowledge gap for Mod/TA, not an
        # out-of-domain request.
        if intent_result.intent == "in_scope_unknown":
            return self._build_response(
                message_id=message_id,
                trace_id=trace_id,
                route="ESCALATE",
                intent=intent_result.intent,
                confidence=max(intent_result.confidence, 0.7),
                grounding_status="no_source",
                response=(
                    "Câu hỏi này có liên quan tới khóa học nhưng mình chưa tìm "
                    "thấy căn cứ trong kho tri thức. Bạn có thể nhờ Mod/TA "
                    "xác nhận; hệ thống chưa tự động gửi câu hỏi."
                ),
                escalation={
                    "reason_code": "related_knowledge_gap",
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

    def _generate_clarification(
        self,
        intent: str,
        missing_fields: list[str],
        known_slots: dict[str, Any] | None = None,
    ) -> str:
        """Generate clarification question based on missing fields."""
        if (
            intent == "ask_gate"
            and "gate_name" in missing_fields
            and (known_slots or {}).get("requested_fact") == "deadline"
        ):
            return "Bạn muốn hỏi deadline của gate nào? (CP1, CP2, CP3 hay Final Gate?)"

        field_questions = {
            "assignment": "Bạn đang hỏi deadline của nội dung nào? (VD: Weekly Report qua /weekly submit, AI Log, Demo Day...)",
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
                "assignment": ["Weekly Report", "AI Log", "Demo Day"],
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
        llm: dict[str, Any] | None = None,
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
            "llm": llm,
        }
