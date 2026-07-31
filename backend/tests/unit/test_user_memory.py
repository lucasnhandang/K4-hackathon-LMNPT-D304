import unittest
from unittest.mock import AsyncMock, patch

from student_assistant.api.schemas.chat import ChatRequest
from student_assistant.services.chat_service import process_chat
from student_assistant.services.guardrails import rate_limiter
from student_assistant.services.user_memory import (
    is_capabilities_question,
    parse_memory_command,
)


class UserMemoryParserTests(unittest.TestCase):
    def test_parses_remember_name(self) -> None:
        command = parse_memory_command("tôi tên là Thịnh")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "remember_name")
        self.assertEqual(command.value, "Thịnh")

    def test_parses_recall_name_with_chat_abbreviation(self) -> None:
        command = parse_memory_command("tôi tên là j")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "recall_name")

    def test_parses_natural_remember_sentence_with_typo_in_suffix(self) -> None:
        command = parse_memory_command(
            "tôi tên là Thịnh từ giờ hãy gọi tooiu như vậy"
        )
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "remember_name")
        self.assertEqual(command.value, "Thịnh")

    def test_parses_remember_name_plus_capabilities_question(self) -> None:
        message = "tôi tên là Thịnh bạn có thể làm những j"
        command = parse_memory_command(message)
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "remember_name")
        self.assertEqual(command.value, "Thịnh")
        self.assertTrue(is_capabilities_question(message))

    def test_parses_change_name(self) -> None:
        command = parse_memory_command("đổi lại tôi tên là Quang")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "remember_name")
        self.assertEqual(command.value, "Quang")

    def test_parses_recall_name_inside_greeting(self) -> None:
        command = parse_memory_command("xin chào tôi tên là j")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "recall_name")

    def test_recognizes_information_scope_question(self) -> None:
        self.assertTrue(
            is_capabilities_question("bạn có những thông tin j")
        )
        self.assertTrue(is_capabilities_question("bot biết những gì?"))
        self.assertTrue(
            is_capabilities_question("bạn hỗ trợ được những gì?")
        )

    def test_parses_forget_name(self) -> None:
        command = parse_memory_command("hãy quên tên tôi")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "forget_name")

    def test_does_not_store_arbitrary_profile_fact(self) -> None:
        self.assertIsNone(parse_memory_command("tôi là sinh viên backend"))


class UserMemoryChatTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        rate_limiter.reset()

    async def test_remember_name_bypasses_vector_search(self) -> None:
        payload = ChatRequest(
            message="tôi tên là Thịnh",
            student_id="memory-user",
            guild_id="memory-guild",
            channel_id="memory-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.save_preferred_name",
                new=AsyncMock(),
            ) as memory_save_mock,
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "answer")
        self.assertIn("Rất vui được biết bạn, Thịnh!", result.reply)
        memory_save_mock.assert_awaited_once()
        retrieval_mock.assert_not_awaited()

    async def test_recalls_name_by_discord_identity(self) -> None:
        payload = ChatRequest(
            message="tôi tên là j",
            student_id="memory-user",
            guild_id="memory-guild",
            channel_id="memory-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.get_preferred_name",
                new=AsyncMock(return_value="Thịnh"),
            ) as memory_get_mock,
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "answer")
        self.assertIn("Bạn là Thịnh", result.reply)
        memory_get_mock.assert_awaited_once_with(
            "memory-user",
            "memory-guild",
        )
        retrieval_mock.assert_not_awaited()

    async def test_social_greeting_uses_remembered_name(self) -> None:
        payload = ChatRequest(
            message="xin chào",
            student_id="memory-user",
            guild_id="memory-guild",
            channel_id="memory-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.get_preferred_name",
                new=AsyncMock(return_value="Thịnh"),
            ),
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(
            result.reply,
            "Xin chào Thịnh! Hôm nay mình có thể giúp gì cho bạn?",
        )
        retrieval_mock.assert_not_awaited()

    async def test_remembers_name_and_answers_capabilities_in_one_turn(
        self,
    ) -> None:
        payload = ChatRequest(
            message="tôi tên là Thịnh bạn có thể làm những j",
            student_id="memory-user",
            guild_id="memory-guild",
            channel_id="memory-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.save_preferred_name",
                new=AsyncMock(),
            ) as memory_save_mock,
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertIn("Rất vui được biết bạn, Thịnh!", result.reply)
        self.assertIn("deadline", result.reply)
        memory_save_mock.assert_awaited_once()
        retrieval_mock.assert_not_awaited()

    async def test_change_name_updates_existing_memory(self) -> None:
        payload = ChatRequest(
            message="đổi lại tôi tên là Quang",
            student_id="memory-user",
            guild_id="memory-guild",
            channel_id="memory-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.save_preferred_name",
                new=AsyncMock(),
            ) as memory_save_mock,
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        saved_name = memory_save_mock.await_args.args[2]
        self.assertEqual(saved_name, "Quang")
        self.assertIn("Quang", result.reply)
        retrieval_mock.assert_not_awaited()

    async def test_information_scope_bypasses_vector_search(self) -> None:
        payload = ChatRequest(
            message="bạn có những thông tin j",
            student_id="memory-user",
            guild_id="memory-guild",
            channel_id="memory-channel",
        )
        with (
            patch(
                "student_assistant.services.chat_service.get_preferred_name",
                new=AsyncMock(return_value="Thịnh"),
            ),
            patch(
                "student_assistant.services.chat_service.retrieve_grounding",
                new=AsyncMock(),
            ) as retrieval_mock,
            patch(
                "student_assistant.services.chat_service.save_chat_exchange",
                new=AsyncMock(),
            ),
        ):
            result = await process_chat(payload)

        self.assertEqual(result.action, "answer")
        self.assertIn("deadline", result.reply)
        self.assertIn("lịch mentor", result.reply)
        retrieval_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
