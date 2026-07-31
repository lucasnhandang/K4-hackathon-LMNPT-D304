from __future__ import annotations

import math
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .models import ToolResult
from .retrieval import normalize_text, tokenize


QUESTION_SIGNALS = {
    "ai",
    "bao gio",
    "bao nhieu",
    "cach",
    "co duoc",
    "deadline",
    "gi",
    "khi nao",
    "lam sao",
    "link",
    "loi",
    "nop",
    "o dau",
    "tai sao",
    "the nao",
}


def _looks_like_question(content: str) -> bool:
    normalized = normalize_text(content)
    return "?" in content or any(signal in normalized for signal in QUESTION_SIGNALS)


def _cosine_similarity(left: list[str], right: list[str]) -> float:
    left_counts = Counter(left)
    right_counts = Counter(right)
    common = set(left_counts) & set(right_counts)
    numerator = sum(left_counts[token] * right_counts[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _similarity(query: str, candidate: str) -> float:
    normalized_query = normalize_text(query)
    normalized_candidate = normalize_text(candidate)
    if not normalized_query or not normalized_candidate:
        return 0.0
    cosine = _cosine_similarity(tokenize(query), tokenize(candidate))
    sequence = SequenceMatcher(None, normalized_query, normalized_candidate).ratio()
    return round(0.75 * cosine + 0.25 * sequence, 6)


class ConversationSearchTools:
    """Searches previously collected community questions.

    Results are navigation hints, never authoritative citations.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def search_similar_questions(
        self,
        *,
        query: str,
        current_message_id: str | None = None,
        limit: int = 3,
        min_score: float = 0.68,
        max_age_days: int = 90,
    ) -> ToolResult:
        if not query.strip():
            return ToolResult(
                status="ambiguous",
                missing_fields=["query"],
                message="Cần câu hỏi hiện tại để tìm hội thoại tương tự.",
            )
        if not 1 <= limit <= 5:
            return ToolResult(status="rejected", message="limit phải nằm trong khoảng 1..5.")
        if not 0.0 <= min_score <= 1.0:
            return ToolResult(status="rejected", message="min_score phải nằm trong khoảng 0..1.")
        if max_age_days < 1 or max_age_days > 365:
            return ToolResult(
                status="rejected",
                message="max_age_days phải nằm trong khoảng 1..365.",
            )
        if not self.database_path.exists():
            return ToolResult(
                status="not_found",
                data={"redirect_suggested": False, "matches": []},
                message="Chưa có database hội thoại để tìm kiếm.",
            )

        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                    """
                    SELECT
                        message_id, content_redacted, created_at, jump_url,
                        (
                            SELECT COUNT(*)
                            FROM messages AS replies
                            WHERE replies.reply_to_message_id = messages.message_id
                              AND replies.deleted = 0
                        ) AS reply_count
                    FROM messages
                    WHERE tier = 'community'
                      AND author_type = 'student'
                      AND deleted = 0
                      AND content_redacted IS NOT NULL
                      AND content_redacted != ''
                      AND created_at >= ?
                    ORDER BY created_at DESC
                    LIMIT 3000
                    """,
                    (cutoff,),
            ).fetchall()
        except sqlite3.Error:
            return ToolResult(
                status="error",
                data={"redirect_suggested": False, "matches": []},
                message="Không thể đọc lịch sử hội thoại.",
            )
        finally:
            if connection is not None:
                connection.close()

        matches: list[dict[str, Any]] = []
        for row in rows:
            message_id = str(row["message_id"])
            if current_message_id is not None and message_id == str(current_message_id):
                continue
            content = str(row["content_redacted"])
            if not _looks_like_question(content):
                continue
            score = _similarity(query, content)
            if score < min_score:
                continue
            matches.append(
                {
                    "message_id": message_id,
                    "question_preview": content[:240],
                    "jump_url": row["jump_url"],
                    "created_at": row["created_at"],
                    "reply_count": int(row["reply_count"]),
                    "score": score,
                    "trusted_for_factual_answer": False,
                }
            )

        matches.sort(
            key=lambda item: (item["score"], item["reply_count"], item["created_at"]),
            reverse=True,
        )
        selected = matches[:limit]
        if not selected:
            return ToolResult(
                status="not_found",
                data={"redirect_suggested": False, "matches": []},
                message="Không tìm thấy câu hỏi cũ đủ tương đồng; tiếp tục luồng trả lời.",
            )
        return ToolResult(
            status="ok",
            data={
                "redirect_suggested": True,
                "matches": selected,
                "notice": (
                    "Đây là hội thoại cộng đồng để tham khảo, không phải nguồn chính thức."
                ),
            },
            message="Đã tìm thấy câu hỏi tương tự trong lịch sử.",
        )
