from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .models import Citation, ToolResult
from .retrieval import BM25Index, normalize_text
from .store import OfficialSourceStore, SourceRecord


def _citation(record: SourceRecord) -> Citation:
    return Citation(
        source_id=record.source_id,
        title=record.title,
        locator=record.locator,
        quote=record.text,
        updated_at=record.updated_at,
    )


def _missing(**fields: Any) -> list[str]:
    return [name for name, value in fields.items() if value in (None, "")]


class KnowledgeTools:
    def __init__(self, store: OfficialSourceStore):
        self.store = store
        self.index = BM25Index(store.records)

    def _structured_lookup(
        self,
        *,
        category: str,
        at: str | None = None,
        required: dict[str, Any],
        optional: dict[str, Any] | None = None,
    ) -> ToolResult:
        missing_fields = _missing(**required)
        if missing_fields:
            return ToolResult(
                status="ambiguous",
                missing_fields=missing_fields,
                message="Thiếu thông tin bắt buộc để tra cứu chính xác.",
            )

        filters = {**required, **(optional or {})}
        records = self.store.filter(category=category, at=at, **filters)
        if not records:
            return ToolResult(
                status="not_found",
                message="Không tìm thấy dữ liệu trong nguồn chính thức.",
            )

        conflicts = self._find_conflicts(records)
        if conflicts:
            return ToolResult(
                status="conflict",
                conflicts=conflicts,
                citations=[_citation(record) for record in records],
                message="Các nguồn chính thức đang có thông tin mâu thuẫn.",
            )

        if len(records) > 1:
            return ToolResult(
                status="ambiguous",
                data=[record.attributes for record in records],
                citations=[_citation(record) for record in records],
                message="Có nhiều kết quả phù hợp; cần thêm ngữ cảnh.",
            )

        record = records[0]
        return ToolResult(
            status="ok",
            data=record.attributes,
            citations=[_citation(record)],
            message="Đã tìm thấy dữ liệu từ nguồn chính thức.",
        )

    @staticmethod
    def _find_conflicts(records: list[SourceRecord]) -> list[dict[str, Any]]:
        if len(records) < 2:
            return []
        ignored = {"source_kind"}
        keys = set.intersection(*(set(record.attributes) for record in records)) - ignored
        conflicts = []
        for key in sorted(keys):
            values = {str(record.attributes[key]) for record in records}
            if len(values) > 1:
                conflicts.append(
                    {
                        "field": key,
                        "values": sorted(values),
                        "source_ids": [record.source_id for record in records],
                    }
                )
        return conflicts

    def lookup_deadline(
        self,
        *,
        assignment: str | None,
        module: str | None = None,
        cohort: str | None,
        at: str | None = None,
    ) -> ToolResult:
        # module is optional - only assignment and cohort are required
        return self._structured_lookup(
            category="deadline",
            at=at,
            required={"assignment": assignment, "cohort": cohort},
            optional={"module": module} if module else None,
        )

    def lookup_event(
        self,
        *,
        event_name: str | None,
        cohort: str | None,
        at: str | None = None,
    ) -> ToolResult:
        return self._structured_lookup(
            category="event",
            at=at,
            required={"event_name": event_name, "cohort": cohort},
        )

    def lookup_gate(
        self,
        *,
        gate_name: str | None,
        cohort: str | None,
        at: str | None = None,
    ) -> ToolResult:
        return self._structured_lookup(
            category="gate",
            at=at,
            required={"gate_name": gate_name, "cohort": cohort},
        )

    def lookup_exam_slot(
        self,
        *,
        exam_name: str | None,
        cohort: str | None,
        team: str | None,
        at: str | None = None,
    ) -> ToolResult:
        return self._structured_lookup(
            category="exam_slot",
            at=at,
            required={"exam_name": exam_name, "cohort": cohort, "team": team},
        )

    def lookup_xp(
        self,
        *,
        activity: str | None,
        cohort: str | None,
        at: str | None = None,
    ) -> ToolResult:
        return self._structured_lookup(
            category="xp",
            at=at,
            required={"activity": activity, "cohort": cohort},
        )

    def lookup_team_mentor(
        self,
        *,
        cohort: str | None,
        team: str | None,
        at: str | None = None,
    ) -> ToolResult:
        return self._structured_lookup(
            category="team_mentor",
            at=at,
            required={"cohort": cohort, "team": team},
        )

    def lookup_slash_command(self, *, command: str | None) -> ToolResult:
        return self._structured_lookup(
            category="slash_command",
            required={"command": command},
        )

    def search_official_sources(
        self,
        *,
        query: str,
        category: str | None = None,
        at: str | None = None,
        limit: int = 5,
        min_score: float = 0.0,
        required_terms: list[str] | None = None,
    ) -> ToolResult:
        if not query.strip():
            return ToolResult(
                status="ambiguous",
                missing_fields=["query"],
                message="Cần câu truy vấn để tìm nguồn.",
            )
        if limit < 1 or limit > 10:
            return ToolResult(status="rejected", message="limit phải nằm trong khoảng 1..10.")
        if min_score < 0:
            return ToolResult(status="rejected", message="min_score phải không âm.")

        hits = self.index.search(
            query,
            category=category,
            at=at,
            limit=limit,
            min_score=min_score,
            required_terms=required_terms,
        )
        if not hits:
            return ToolResult(
                status="not_found",
                message="Không tìm thấy đoạn nguồn chính thức phù hợp.",
            )
        return ToolResult(
            status="ok",
            data=[
                {
                    "source_id": record.source_id,
                    "category": record.category,
                    "score": score,
                    "attributes": record.attributes,
                }
                for record, score in hits
            ],
            citations=[_citation(record) for record, _ in hits],
            message="Đã tìm thấy nguồn chính thức phù hợp.",
        )

    def check_source_conflicts(self, *, source_ids: list[str]) -> ToolResult:
        records = [record for record in self.store.records if record.source_id in source_ids]
        missing_ids = sorted(set(source_ids) - {record.source_id for record in records})
        if missing_ids:
            return ToolResult(
                status="not_found",
                data={"missing_source_ids": missing_ids},
                message="Một hoặc nhiều source_id không tồn tại.",
            )
        conflicts = self._find_conflicts(records)
        return ToolResult(
            status="conflict" if conflicts else "ok",
            conflicts=conflicts,
            citations=[_citation(record) for record in records],
            message=(
                "Phát hiện mâu thuẫn giữa các nguồn."
                if conflicts
                else "Không phát hiện mâu thuẫn giữa các nguồn."
            ),
        )


class TicketGateway(Protocol):
    def send(self, target_channel: str, payload: dict[str, Any]) -> str: ...


class InMemoryTicketGateway:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def send(self, target_channel: str, payload: dict[str, Any]) -> str:
        ticket_id = f"TK-{len(self.sent) + 1:04d}"
        self.sent.append(
            {"ticket_id": ticket_id, "target_channel": target_channel, **payload}
        )
        return ticket_id


def analyze_sentiment_and_priority(text: str) -> dict[str, str]:
    """Feature 5: Analyze sentiment and priority from user question."""
    norm = normalize_text(text)
    urgent_keywords = [
        "gap", "khan cap", "trui", "quay roi", "quay roi em", "bi tru diem oan",
        "cham sai", "sos", "urgent", "help urgent", "gap lam", "xung dot",
        "nghi hoc", "bao luu", "khong chay duoc", "loi nang", "loi out of memory", "giai quyet"
    ]
    frustrated_keywords = ["cham sai", "tru diem oan", "bat cong", "buc xuc", "khieu nai"]
    stressed_keywords = ["gap", "khan cap", "cuu", "tre han", "lo han", "muon", "nghi hoc", "bao luu", "quay roi"]

    is_urgent = any(kw in norm for kw in urgent_keywords)
    priority = "URGENT" if is_urgent else "NORMAL"

    if any(kw in norm for kw in frustrated_keywords):
        sentiment = "frustrated"
    elif any(kw in norm for kw in stressed_keywords):
        sentiment = "stressed_or_urgent"
    else:
        sentiment = "neutral"

    return {"priority": priority, "sentiment": sentiment}


@dataclass(frozen=True)
class TicketDraft:
    request_id: str
    category: str
    target_channel: str
    question: str
    known_context: dict[str, Any]
    missing_information: list[str]
    clarification_attempts: int
    source_ids: list[str]
    created_at: str
    priority: str = "NORMAL"
    sentiment: str = "neutral"


class TicketTools:
    CHANNEL_ALLOWLIST = {
        "deadline": "assignment-support",
        "learning": "learning-support",
        "technical": "technical-support",
        "team_mentor": "mentor-support",
        "safety": "private-mod-support",
        "other": "student-support",
    }
    CONTEXT_ALLOWLIST = {
        "assignment",
        "module",
        "cohort",
        "team",
        "event_name",
        "exam_name",
        "activity",
        "command",
        "error_code",
        "platform",
    }

    def __init__(self, gateway: TicketGateway | None = None):
        self.gateway = gateway or InMemoryTicketGateway()
        self.drafts: dict[str, TicketDraft] = {}
        self.completed_requests: dict[str, str] = {}

    def offer_ticket(
        self,
        *,
        category: str,
        question: str,
        known_context: dict[str, Any],
        missing_information: list[str],
        clarification_attempts: int,
        source_ids: list[str] | None = None,
        priority: str | None = None,
        sentiment: str | None = None,
    ) -> ToolResult:
        if category not in self.CHANNEL_ALLOWLIST:
            return ToolResult(status="rejected", message="Loại ticket không được phép.")
        if (
            not isinstance(clarification_attempts, int)
            or isinstance(clarification_attempts, bool)
            or clarification_attempts < 2
        ):
            return ToolResult(
                status="rejected",
                message="Chỉ đề xuất ticket sau ít nhất hai lần hỏi làm rõ.",
            )
        if not question.strip():
            return ToolResult(status="ambiguous", missing_fields=["question"])
        if not isinstance(known_context, dict):
            return ToolResult(status="rejected", message="known_context phải là object.")
        forbidden_context = sorted(set(known_context) - self.CONTEXT_ALLOWLIST)
        if forbidden_context:
            return ToolResult(
                status="rejected",
                data={"forbidden_context_fields": forbidden_context},
                message="Context chứa trường không được phép đưa vào ticket.",
            )

        analysis = analyze_sentiment_and_priority(question)
        final_priority = priority or analysis["priority"]
        final_sentiment = sentiment or analysis["sentiment"]

        request_id = f"REQ-{uuid4().hex[:10].upper()}"
        draft = TicketDraft(
            request_id=request_id,
            category=category,
            target_channel=self.CHANNEL_ALLOWLIST[category],
            question=question.strip(),
            known_context=known_context,
            missing_information=missing_information,
            clarification_attempts=clarification_attempts,
            source_ids=source_ids or [],
            created_at=datetime.now(timezone.utc).isoformat(),
            priority=final_priority,
            sentiment=final_sentiment,
        )
        self.drafts[request_id] = draft
        return ToolResult(
            status="ok",
            data={
                **asdict(draft),
                "requires_user_consent": True,
                "sent": False,
            },
            message="Đã tạo bản nháp ticket; chưa gửi đến kênh hỗ trợ.",
        )

    def create_ticket(self, *, request_id: str, user_consent: bool) -> ToolResult:
        if user_consent is not True:
            return ToolResult(
                status="rejected",
                data={"request_id": request_id, "sent": False},
                message="Người dùng không đồng ý; không có ticket nào được gửi.",
            )
        if request_id in self.completed_requests:
            return ToolResult(
                status="ok",
                data={
                    "request_id": request_id,
                    "ticket_id": self.completed_requests[request_id],
                    "sent": True,
                    "idempotent_replay": True,
                },
                message="Ticket đã được gửi trước đó; không gửi trùng.",
            )

        draft = self.drafts.get(request_id)
        if not draft:
            return ToolResult(status="not_found", message="Không tìm thấy bản nháp ticket.")

        payload = {
            "request_id": draft.request_id,
            "category": draft.category,
            "question": draft.question,
            "known_context": draft.known_context,
            "missing_information": draft.missing_information,
            "clarification_attempts": draft.clarification_attempts,
            "source_ids": draft.source_ids,
        }
        ticket_id = self.gateway.send(draft.target_channel, payload)
        self.completed_requests[request_id] = ticket_id
        return ToolResult(
            status="ok",
            data={
                "request_id": request_id,
                "ticket_id": ticket_id,
                "target_channel": draft.target_channel,
                "sent": True,
                "idempotent_replay": False,
            },
            message="Đã gửi ticket sau khi nhận xác nhận của người dùng.",
        )
