import unittest
from unittest.mock import AsyncMock, patch

from student_assistant.api.schemas.chat import ChatRequest
from student_assistant.services.chat_service import (
    build_conversation_id,
    process_chat,
)
from student_assistant.services.gemini import GeminiGroundedResponse
from student_assistant.services.grounding import GroundingResult
from student_assistant.services.guardrails import rate_limiter


class ChatServiceTests(unittest.TestCase):
    def test_discord_message_has_deterministic_conversation_id(self) -> None:
        payload = ChatRequest(
            message="xin chào",
            guild_id="guild-1",
            channel_id="channel-1",
            discord_message_id="message-1",
        )
        self.assertEqual(
            build_conversation_id(payload),
            "discord:guild-1:channel-1:message-1",
        )

    def test_non_discord_message_gets_uuid(self) -> None:
        first = build_conversation_id(ChatRequest(message="one"))
        second = build_conversation_id(ChatRequest(message="two"))
        self.assertNotEqual(first, second)


class ChatStorageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        rate_limiter.reset()

    async def test_process_chat_uses_vector_score_and_stores_redacted_data(
        self,
    ) -> None:
        payload = ChatRequest(
            message="Deadline của email student@example.com là khi nào?",
            student_id="user-1",
            bot_id="bot-1",
            user_role_ids=["role-1"],
            guild_id="guild-1",
            channel_id="channel-1",
            discord_message_id="message-1",
        )
        grounding = GroundingResult(
            documents=[
                {
                    "_id": "kb-1",
                    "title": "Deadline",
                    "content": "Deadline là 12h.",
                    "score": 0.91,
                }
            ],
            score=0.91,
        )
        generated = GeminiGroundedResponse(
            action="answer",
            reply="Deadline là 12h.",
            reasoning="Tài liệu nêu rõ deadline.",
        )

        with (
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(return_value=grounding),
            ),
            patch(
                "student_assistant.services.chat_service."
                "generate_chat_response",
                new=AsyncMock(return_value=generated),
            ),
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ) as save_mock,
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "answer")
        self.assertEqual(result.grounding_score, 0.91)
        self.assertEqual(result.confidence, 91)
        self.assertEqual(result.matched_kb_ids, ["kb-1"])

        conversation, user_message, assistant_message, raw_message = (
            save_mock.await_args.args
        )
        self.assertEqual(
            conversation["conversation_id"],
            "discord:guild-1:channel-1:message-1",
        )
        self.assertIn("[REDACTED_EMAIL]", conversation["question"])
        self.assertIn("[REDACTED_EMAIL]", user_message["content"])
        self.assertIn("student@example.com", raw_message["content"])
        self.assertEqual(user_message["role"], "user")
        self.assertEqual(user_message["author_id"], "user-1")
        self.assertEqual(assistant_message["role"], "assistant")
        self.assertEqual(assistant_message["author_id"], "bot-1")

    async def test_low_score_offers_mod_without_calling_gemini(self) -> None:
        payload = ChatRequest(
            message="Cho tôi hỏi chuyện không có trong khóa học",
            student_id="low-score-user",
            channel_id="low-score-channel",
        )
        grounding = GroundingResult(documents=[], score=0.20)

        with (
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(return_value=grounding),
            ),
            patch(
                "student_assistant.services.chat_service."
                "generate_chat_response",
                new=AsyncMock(),
            ) as generate_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "clarify")
        self.assertIn("Mod", result.reply)
        generate_mock.assert_not_awaited()

    async def test_medium_score_asks_for_more_context(self) -> None:
        payload = ChatRequest(
            message="Deadline là bao nhiêu?",
            student_id="medium-score-user",
            channel_id="medium-score-channel",
        )
        grounding = GroundingResult(
            documents=[
                {
                    "_id": "kb-medium",
                    "title": "Deadline",
                    "content": "Có nhiều deadline.",
                    "score": 0.81,
                }
            ],
            score=0.81,
        )

        with (
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(return_value=grounding),
            ),
            patch(
                "student_assistant.services.chat_service."
                "generate_chat_response",
                new=AsyncMock(),
            ) as generate_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "clarify")
        self.assertIn("nói thêm", result.reply)
        generate_mock.assert_not_awaited()

    async def test_social_message_does_not_require_grounding(self) -> None:
        payload = ChatRequest(
            message="xin chào",
            student_id="social-user",
            channel_id="social-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.get_preferred_name",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "answer")
        retrieval_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
