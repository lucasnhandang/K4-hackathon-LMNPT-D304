import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from student_assistant.api.schemas.knowledge import (
    DiscordKnowledgeIngestRequest,
)
from student_assistant.services.discord_knowledge import (
    ingest_discord_knowledge,
)
from student_assistant.services.guardrails import (
    SecretDetected,
    rate_limiter,
)


def _payload(
    content: str = "Buổi mentor diễn ra lúc 20h.",
    channel_id: str = "977644669326475311",
) -> DiscordKnowledgeIngestRequest:
    return DiscordKnowledgeIngestRequest(
        content=content,
        author_id="user-1",
        author_role_ids=["role-1"],
        guild_id="guild-1",
        channel_id=channel_id,
        discord_message_id="message-1",
        discord_created_at=datetime.now(timezone.utc),
    )


class DiscordKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        rate_limiter.reset()

    async def test_ingest_masks_pii_embeds_and_keeps_provenance(self) -> None:
        payload = _payload(
            "Email hỗ trợ là support@example.com, mentor bắt đầu lúc 20h."
        )
        with (
            patch(
                "student_assistant.services.discord_knowledge.embed_documents",
                new=AsyncMock(return_value=[[0.1] * 768]),
            ),
            patch(
                "student_assistant.services.discord_knowledge."
                "upsert_discord_knowledge",
                new=AsyncMock(return_value=("doc-1", True)),
            ) as upsert_mock,
        ):
            result = await ingest_discord_knowledge(payload)

        self.assertEqual(result.status, "stored")
        self.assertEqual(result.document_id, "doc-1")
        document = upsert_mock.await_args.args[0]
        self.assertIn("[REDACTED_EMAIL]", document["content"])
        self.assertNotIn("support@example.com", document["content"])
        self.assertEqual(document["source"], "discord_channel")
        self.assertEqual(document["source_message_id"], "message-1")
        self.assertEqual(document["source_author_id"], "user-1")
        self.assertTrue(document["is_active"])
        self.assertEqual(len(document["embedding"]), 768)

    async def test_rejects_channel_outside_ingest_allowlist(self) -> None:
        with self.assertRaises(PermissionError):
            await ingest_discord_knowledge(_payload(channel_id="123"))

    async def test_rejects_secret_before_embedding(self) -> None:
        with (
            patch(
                "student_assistant.services.discord_knowledge.embed_documents",
                new=AsyncMock(),
            ) as embedding_mock,
            self.assertRaises(SecretDetected),
        ):
            await ingest_discord_knowledge(
                _payload("GEMINI_API_KEY=AIza123456789012345678901234567890")
            )
        embedding_mock.assert_not_awaited()

    async def test_retry_returns_updated_status(self) -> None:
        with (
            patch(
                "student_assistant.services.discord_knowledge.embed_documents",
                new=AsyncMock(return_value=[[0.1] * 768]),
            ),
            patch(
                "student_assistant.services.discord_knowledge."
                "upsert_discord_knowledge",
                new=AsyncMock(return_value=("doc-1", False)),
            ),
        ):
            result = await ingest_discord_knowledge(_payload())
        self.assertEqual(result.status, "updated")


if __name__ == "__main__":
    unittest.main()
