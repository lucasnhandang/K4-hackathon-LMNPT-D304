from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ToolStatus = Literal["ok", "not_found", "ambiguous", "conflict", "rejected", "error"]


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    locator: str
    quote: str
    updated_at: str


@dataclass
class ToolResult:
    status: ToolStatus
    data: Any = None
    citations: list[Citation] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
