from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from chatbot_tools.conversation import ConversationSearchTools
from discord_collector.storage import MessageRecord, MessageStore


def record(
    message_id: int,
    content: str,
    *,
    author_type: str = "student",
    tier: str = "community",
    reply_to: int | None = None,
) -> MessageRecord:
    return MessageRecord(
        message_id=message_id,
        guild_id=10,
        channel_id=20,
        parent_channel_id=None,
        tier=tier,
        author_hash=f"usr_{message_id}",
        author_type=author_type,
        content_redacted=content,
        reply_to_message_id=reply_to,
        created_at=datetime.now(timezone.utc).isoformat(),
        edited_at=None,
        attachment_count=0,
        jump_url=f"https://discord.com/channels/10/20/{message_id}",
    )


class ConversationSearchTests(unittest.TestCase):
    def test_redirects_to_similar_prior_question(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "messages.sqlite3"
            with MessageStore(database) as store:
                store.upsert(record(101, "Deadline bài RAG tuần này là khi nào?"))
                store.upsert(
                    record(
                        102,
                        "Bạn xem lịch chính thức ở thông báo nhé.",
                        author_type="bot",
                        reply_to=101,
                    )
                )

            result = ConversationSearchTools(database).search_similar_questions(
                query="deadline bai RAG tuan nay khi nao",
            )

        self.assertEqual(result.status, "ok")
        self.assertTrue(result.data["redirect_suggested"])
        self.assertEqual(result.data["matches"][0]["message_id"], "101")
        self.assertEqual(result.data["matches"][0]["reply_count"], 1)
        self.assertFalse(
            result.data["matches"][0]["trusted_for_factual_answer"]
        )

    def test_does_not_match_the_current_message_to_itself(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "messages.sqlite3"
            with MessageStore(database) as store:
                store.upsert(record(201, "Cách nộp bài RAG như thế nào?"))

            result = ConversationSearchTools(database).search_similar_questions(
                query="Cách nộp bài RAG như thế nào?",
                current_message_id="201",
            )

        self.assertEqual(result.status, "not_found")
        self.assertFalse(result.data["redirect_suggested"])

    def test_ignores_official_messages_as_prior_community_questions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "messages.sqlite3"
            with MessageStore(database) as store:
                store.upsert(
                    record(
                        301,
                        "Deadline bài RAG tuần này là khi nào?",
                        tier="official",
                    )
                )

            result = ConversationSearchTools(database).search_similar_questions(
                query="Deadline bài RAG tuần này là khi nào?",
            )

        self.assertEqual(result.status, "not_found")

    def test_unrelated_question_continues_normal_answer_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "messages.sqlite3"
            with MessageStore(database) as store:
                store.upsert(record(401, "Mentor team 5 là ai?"))

            result = ConversationSearchTools(database).search_similar_questions(
                query="Làm sao sửa lỗi Docker build?",
            )

        self.assertEqual(result.status, "not_found")
        self.assertEqual(result.data["matches"], [])


if __name__ == "__main__":
    unittest.main()
