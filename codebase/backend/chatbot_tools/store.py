from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    locator: str
    category: str
    text: str
    updated_at: str
    valid_from: str | None
    valid_to: str | None
    attributes: dict[str, Any]
    official: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SourceRecord":
        return cls(**raw)

    def is_valid_at(self, at: str | None) -> bool:
        if not at:
            return True
        point = datetime.fromisoformat(at)
        if self.valid_from and point < datetime.fromisoformat(self.valid_from):
            return False
        if self.valid_to and point > datetime.fromisoformat(self.valid_to):
            return False
        return True


class OfficialSourceStore:
    def __init__(self, records: Iterable[SourceRecord]):
        self.records = tuple(records)

    @classmethod
    def from_json(cls, path: str | Path) -> "OfficialSourceStore":
        with Path(path).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(SourceRecord.from_dict(item) for item in payload["records"])

    def filter(
        self,
        *,
        category: str | None = None,
        at: str | None = None,
        official_only: bool = True,
        **attributes: Any,
    ) -> list[SourceRecord]:
        matches: list[SourceRecord] = []
        for record in self.records:
            if official_only and not record.official:
                continue
            if category and record.category != category:
                continue
            if not record.is_valid_at(at):
                continue
            if any(
                value is not None and record.attributes.get(key) != value
                for key, value in attributes.items()
            ):
                continue
            matches.append(record)
        return matches
