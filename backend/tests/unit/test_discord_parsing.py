import unittest

from student_assistant.integrations.discord.parsing import (
    extract_question,
    is_allowed_channel,
    parse_channel_ids,
    should_ingest_knowledge_message,
)


class DiscordParsingTests(unittest.TestCase):
    def test_extracts_regular_mention(self) -> None:
        self.assertEqual(
            extract_question("<@123> xin chào", 123),
            "xin chào",
        )

    def test_extracts_nickname_mention(self) -> None:
        self.assertEqual(
            extract_question("<@!123> deadline là khi nào?", 123),
            "deadline là khi nào?",
        )

    def test_empty_allowlist_allows_every_channel(self) -> None:
        self.assertTrue(is_allowed_channel(123, set()))

    def test_allowlist_restricts_channels(self) -> None:
        allowed = parse_channel_ids("123, 456")
        self.assertTrue(is_allowed_channel(123, allowed))
        self.assertFalse(is_allowed_channel(789, allowed))

    def test_invalid_channel_id_fails_fast(self) -> None:
        with self.assertRaises(RuntimeError):
            parse_channel_ids("123,not-an-id")

    def test_ingests_non_mention_only_in_knowledge_channel(self) -> None:
        channels = {977644669326475311}
        self.assertTrue(
            should_ingest_knowledge_message(
                977644669326475311,
                channels,
                bot_is_mentioned=False,
            )
        )
        self.assertFalse(
            should_ingest_knowledge_message(
                977644669326475311,
                channels,
                bot_is_mentioned=True,
            )
        )
        self.assertFalse(
            should_ingest_knowledge_message(
                123,
                channels,
                bot_is_mentioned=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
