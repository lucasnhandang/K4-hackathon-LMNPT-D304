from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Iterable

from .store import SourceRecord


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    no_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", no_marks)).strip()


def tokenize(text: str) -> list[str]:
    return [token for token in normalize_text(text).split() if len(token) > 1]


class BM25Index:
    """Small in-memory BM25 index suitable for the hackathon fixture."""

    def __init__(self, records: Iterable[SourceRecord], *, k1: float = 1.5, b: float = 0.75):
        self.records = tuple(records)
        self.k1 = k1
        self.b = b
        self.documents = [
            tokenize(
                " ".join(
                    [
                        record.title,
                        record.locator,
                        record.category,
                        record.text,
                        " ".join(str(value) for value in record.attributes.values()),
                    ]
                )
            )
            for record in self.records
        ]
        self.term_frequencies = [Counter(document) for document in self.documents]
        self.document_frequencies = Counter(
            token for document in self.documents for token in set(document)
        )
        self.average_length = (
            sum(map(len, self.documents)) / len(self.documents) if self.documents else 0.0
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        category: str | None = None,
        at: str | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[SourceRecord, float]]:
        query_terms = tokenize(query)
        if not query_terms or not self.records:
            return []

        candidates: list[tuple[SourceRecord, float]] = []
        total = len(self.records)
        for index, record in enumerate(self.records):
            if not record.official or (category and record.category != category):
                continue
            if not record.is_valid_at(at):
                continue

            document_length = len(self.documents[index])
            score = 0.0
            for term in query_terms:
                frequency = self.term_frequencies[index][term]
                if not frequency:
                    continue
                document_frequency = self.document_frequencies[term]
                inverse_frequency = math.log(
                    1 + (total - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                denominator = frequency + self.k1 * (
                    1 - self.b
                    + self.b * document_length / max(self.average_length, 1.0)
                )
                score += inverse_frequency * frequency * (self.k1 + 1) / denominator

            if score > 0 and score >= min_score:
                candidates.append((record, round(score, 6)))

        return sorted(candidates, key=lambda item: item[1], reverse=True)[:limit]
