"""Adapter between the NiceGUI chat and the codebase chatbot orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter
from typing import Any


CODEBASE_BACKEND_DIR = Path(__file__).resolve().parents[1] / "codebase" / "backend"
if str(CODEBASE_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(CODEBASE_BACKEND_DIR))

from chatbot_tools import build_chat_orchestrator, build_default_registry


def _build_tracepath(backend_data: dict[str, Any], latency_ms: int) -> dict[str, Any]:
    route = backend_data.get("route", "ANSWER")
    intent = backend_data.get("intent", "unknown")
    grounding_status = backend_data.get("grounding_status", "not_required")
    runtime = backend_data.get("runtime") or {}
    engine = runtime.get("engine")

    if engine == "openrouter":
        tools = [
            {
                "name": f"OpenRouter · {runtime.get('model', 'LLM')}",
                "icon": "✨",
                "status": "success",
            }
        ]
        tools.extend(
            {"name": str(name), "icon": "🔧", "status": "success"}
            for name in runtime.get("tool_calls", [])
        )
        steps = [
            "Đã gọi LLM qua OpenRouter",
            f"LLM phân loại ý định: {intent}",
            f"Chọn luồng xử lý: {route}",
        ]
    elif engine == "rules_fallback":
        tools = [
            {"name": "OpenRouter", "icon": "⚠️", "status": "fallback"},
            {"name": "Rule-based fallback", "icon": "⚙️", "status": route.lower()},
        ]
        steps = [
            "Đã gọi LLM nhưng provider/response gặp lỗi",
            f"Fallback cục bộ xử lý intent: {intent}",
            f"Chọn luồng xử lý: {route}",
        ]
    else:
        tools = [
            {"name": "Intent Classifier", "icon": "🔍", "status": "success"},
            {"name": "Chatbot Orchestrator", "icon": "⚙️", "status": route.lower()},
        ]
        steps = [f"Phân loại ý định: {intent}", f"Chọn luồng xử lý: {route}"]

    if grounding_status == "grounded":
        tools.append({"name": "Official Source Lookup", "icon": "📚", "status": "found"})
        steps.append("Đối chiếu dữ liệu với nguồn chính thức")
    elif grounding_status == "no_source":
        tools.append({"name": "Official Source Lookup", "icon": "📚", "status": "not_found"})
        steps.append("Không tìm thấy căn cứ phù hợp trong nguồn chính thức")

    return {
        "latency_ms": latency_ms,
        "confidence": backend_data.get("confidence", 0.0),
        "intent": intent,
        "tools_used": tools,
        "steps": steps,
    }


def transform_backend_response_to_ui(
    backend_data: dict[str, Any],
    latency_ms: int = 0,
) -> dict[str, Any]:
    """Map the codebase I/O contract to the payload rendered by NiceGUI."""
    route = backend_data.get("route", "ANSWER")
    response_message = backend_data.get("response", "")
    citations = backend_data.get("citations") or []
    tracepath = _build_tracepath(backend_data, latency_ms)

    if route == "CLARIFY":
        clarification = backend_data.get("clarification") or {}
        suggestions = clarification.get("suggested_replies") or []
        return {
            "type": "AMBIGUOUS",
            "message": response_message or clarification.get("question", ""),
            "embed_type": "warning-embed",
            "title": "Mình cần bạn làm rõ thêm",
            "options": [
                {
                    "label": str(suggestion),
                    "value": f"CLARIFY::{suggestion}",
                    "class": "disc-btn",
                }
                for suggestion in suggestions
            ],
            "tracepath": tracepath,
        }

    if route == "ESCALATE":
        escalation = backend_data.get("escalation") or {}
        target = escalation.get("target") or escalation.get("target_channel") or "MOD"
        detail = (
            escalation.get("summary")
            or escalation.get("reason_code")
            or "Cần người phụ trách xác nhận."
        )
        return {
            "type": "NO_SOURCE_ESCALATE",
            "message": response_message,
            "embed_type": "escalate-embed",
            "title": "Cần chuyển cho người phụ trách",
            "escalate_tag": f"@{target}" if not str(target).startswith("@") else str(target),
            "escalate_detail": detail,
            "options": [],
            "tracepath": tracepath,
        }

    source_info = ""
    if citations:
        first_citation = citations[0]
        source_info = first_citation.get("title") or first_citation.get("source_id", "")
        locator = first_citation.get("locator")
        if locator:
            source_info = f"{source_info} — {locator}" if source_info else str(locator)

    options = [
        {
            "label": "Đã giải quyết",
            "value": "FEEDBACK_RESOLVED",
            "class": "disc-btn-success",
        },
        {
            "label": "✕ Bot hiểu sai",
            "value": "FEEDBACK_WRONG",
            "class": "disc-btn-danger",
        },
    ]
    if citations:
        options.append({"label": "Xem nguồn", "value": "VIEW_SOURCE", "class": "disc-btn"})

    payload = {
        "type": "DIRECT_ANSWER",
        "message": response_message,
        "embed_type": "success-embed",
        "options": options,
        "citations": citations,
        "tracepath": tracepath,
    }
    if source_info:
        payload["source_info"] = source_info
    return payload


class BackendChatSession:
    """Own one orchestrator and clarification state for one UI session."""

    def __init__(
        self,
        user_id: str = "student_demo",
        session_id: str = "nicegui_session",
        channel_id: str = "go-vuong-hoc-tap",
    ) -> None:
        self.orchestrator = build_chat_orchestrator(build_default_registry())
        self.user_id = user_id
        self.session_id = session_id
        self.channel_id = channel_id
        self.pending_clarification: dict[str, Any] | None = None
        self.history: list[dict[str, str]] = []

    def send_message(self, message: str) -> dict[str, Any]:
        started_at = perf_counter()
        backend_data = self.orchestrator.process_message(
            message=message,
            user_id=self.user_id,
            session_id=self.session_id,
            channel_id=self.channel_id,
            pending_clarification=self.pending_clarification,
            conversation_history=self.history,
        )
        latency_ms = max(1, round((perf_counter() - started_at) * 1000))

        if backend_data.get("route") == "CLARIFY":
            self.pending_clarification = backend_data.get("clarification")
        else:
            self.pending_clarification = None

        self.history.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": backend_data.get("response", "")},
            ]
        )
        return transform_backend_response_to_ui(backend_data, latency_ms)

    def select_option(self, option_value: str, option_label: str) -> dict[str, Any]:
        if option_value == "FEEDBACK_RESOLVED":
            return {
                "type": "CHAT_REPLY",
                "message": "Tuyệt vời! Chúc bạn học tốt nhé 🚀",
                "options": [],
            }
        if option_value == "FEEDBACK_WRONG":
            return {
                "type": "AMBIGUOUS",
                "message": "Xin lỗi bạn. Hãy mô tả phần mình hiểu sai để mình tra cứu lại nhé.",
                "embed_type": "warning-embed",
                "title": "Cần thêm thông tin",
                "options": [{"label": "Nhập phản hồi", "value": "FOCUS_INPUT", "class": "disc-btn"}],
            }

        if option_value.startswith("CLARIFY::"):
            return self.send_message(option_value.partition("::")[2])
        return self.send_message(option_label)
