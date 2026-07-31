from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable

from .models import ToolResult
from .store import OfficialSourceStore
from .tools import KnowledgeTools


def _object_schema(properties: dict[str, dict[str, Any]], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


# ---------------------------------------------------------------------------
# 7 core tools (removed: check_source_conflicts, search_similar_questions,
#                 offer_ticket, create_ticket — redundant or handled by orchestrator)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "lookup_deadline": _object_schema(
        {
            "assignment": {"type": ["string", "null"]},
            "module": {"type": ["string", "null"]},
            "cohort": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"], "description": "ISO 8601 timestamp"},
        },
        ["assignment", "cohort"],  # module is optional
    ),
    "lookup_event": _object_schema(
        {
            "event_name": {"type": ["string", "null"]},
            "cohort": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"]},
        },
        ["event_name", "cohort"],
    ),
    "lookup_gate": _object_schema(
        {
            "gate_name": {"type": ["string", "null"]},
            "cohort": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"]},
        },
        ["gate_name", "cohort"],
    ),
    "lookup_exam_slot": _object_schema(
        {
            "exam_name": {"type": ["string", "null"]},
            "cohort": {"type": ["string", "null"]},
            "team": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"]},
        },
        ["exam_name", "cohort", "team"],
    ),
    "lookup_xp": _object_schema(
        {
            "activity": {"type": ["string", "null"]},
            "cohort": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"]},
        },
        ["activity", "cohort"],
    ),
    "lookup_team_mentor": _object_schema(
        {
            "cohort": {"type": ["string", "null"]},
            "team": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"]},
        },
        ["cohort", "team"],
    ),
    "lookup_slash_command": _object_schema(
        {"command": {"type": ["string", "null"]}},
        ["command"],
    ),
    "search_official_sources": _object_schema(
        {
            "query": {"type": "string"},
            "category": {"type": ["string", "null"]},
            "at": {"type": ["string", "null"]},
            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            "min_score": {"type": "number", "minimum": 0},
        },
        ["query"],
    ),
    "offer_ticket": _object_schema(
        {
            "category": {"type": "string"},
            "question": {"type": "string"},
            "known_context": {"type": "object"},
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "clarification_attempts": {"type": "integer"},
            "source_ids": {"type": ["array", "null"], "items": {"type": "string"}},
            "priority": {"type": ["string", "null"]},
            "sentiment": {"type": ["string", "null"]},
        },
        ["category", "question", "known_context", "missing_information", "clarification_attempts"],
    ),
    "create_ticket": _object_schema(
        {
            "request_id": {"type": "string"},
            "user_consent": {"type": "boolean"},
        },
        ["request_id", "user_consent"],
    ),
}


DESCRIPTIONS = {
    "lookup_deadline": "Tra deadline chính thức; không đoán khi thiếu assignment/module/cohort.",
    "lookup_event": "Tra lịch sự kiện chính thức.",
    "lookup_gate": "Tra điều kiện hoặc thời hạn gate.",
    "lookup_exam_slot": "Tra ca thi theo kỳ thi, khóa và team.",
    "lookup_xp": "Tra quy tắc XP của một hoạt động.",
    "lookup_team_mentor": "Tra mentor và kênh hỗ trợ của team.",
    "lookup_slash_command": "Tra hướng dẫn slash command chính thức.",
    "search_official_sources": "Tìm kiếm BM25 trong nguồn chính thức có lọc loại và thời gian.",
    "offer_ticket": "Gợi ý tạo bản nháp ticket hỗ trợ tới kênh phù hợp (chỉ đề xuất khi cần Mod/TA hỗ trợ).",
    "create_ticket": "Gửi ticket hỗ trợ tới kênh Discord phù hợp sau khi nhận xác nhận của người dùng.",
}


class ToolRegistry:
    def __init__(
        self,
        knowledge: KnowledgeTools,
        tickets: Any | None = None,
    ):
        from .tools import TicketTools
        self.knowledge = knowledge
        self.tickets = tickets or TicketTools()
        self._handlers: dict[str, Callable[..., ToolResult]] = {}
        for name in TOOL_SCHEMAS:
            if hasattr(self.knowledge, name):
                self._handlers[name] = getattr(self.knowledge, name)
            elif hasattr(self.tickets, name):
                self._handlers[name] = getattr(self.tickets, name)

    def definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "name": name,
                "description": DESCRIPTIONS[name],
                "parameters": schema,
                "strict": True,
            }
            for name, schema in TOOL_SCHEMAS.items()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if not handler:
            return ToolResult(status="not_found", message=f"Tool không tồn tại: {name}").to_dict()
        try:
            signature = inspect.signature(handler)
            accepted = set(signature.parameters)
            unknown = sorted(set(arguments) - accepted)
            if unknown:
                return ToolResult(
                    status="rejected",
                    message=f"Tham số không được hỗ trợ: {', '.join(unknown)}",
                ).to_dict()
            return handler(**arguments).to_dict()
        except TypeError as error:
            return ToolResult(status="rejected", message=f"Input tool không hợp lệ: {error}").to_dict()
        except Exception:
            return ToolResult(
                status="error",
                message="Tool gặp lỗi nội bộ; không dùng kết quả để trả lời học viên.",
            ).to_dict()


def build_default_registry(
    data_path: str | Path | None = None,
    ticket_tools: Any | None = None,
) -> ToolRegistry:
    from .tools import TicketTools
    path = Path(data_path) if data_path else Path(__file__).parent / "data" / "official_sources.json"
    store = OfficialSourceStore.from_json(path)
    tickets = ticket_tools or TicketTools()
    return ToolRegistry(KnowledgeTools(store), tickets)
