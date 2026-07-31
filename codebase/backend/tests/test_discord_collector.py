from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from discord_collector.config import ConfigError, load_config
from discord_collector.privacy import PrivacyFilter
from discord_collector.storage import MessageRecord, MessageStore


IDS = [str(10000000000000000 + index) for index in range(1, 12)]


def write_env(path: Path, *, collect_override: str | None = None) -> None:
    official = ",".join(IDS[0:3])
    community = ",".join(IDS[3:6])
    command = IDS[6]
    collect = collect_override or ",".join(IDS[0:7])
    path.write_text(
        "\n".join(
            [
                "DISCORD_TOKEN=test-token",
                f"DISCORD_GUILD_ID={IDS[7]}",
                f"OFFICIAL_SOURCE_CHANNEL_IDS={official}",
                f"COMMUNITY_CHANNEL_IDS={community}",
                f"COMMAND_CHANNEL_IDS={command}",
                f"COLLECT_CHANNEL_IDS={collect}",
                "PSEUDONYM_SECRET=" + "a" * 64,
                "DATABASE_PATH=runtime/test.sqlite3",
                "BACKFILL_ON_START=true",
                "BACKFILL_LIMIT_PER_CHANNEL=0",
                "DATA_RETENTION_DAYS=30",
            ]
        ),
        encoding="utf-8",
    )


class CollectorConfigTests(unittest.TestCase):
    def test_config_has_exact_seven_channel_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            write_env(env_path)
            config = load_config(env_path)

        self.assertEqual(len(config.collect_channel_ids), 7)
        self.assertEqual(config.collect_channel_ids, (
            config.official_channel_ids
            | config.community_channel_ids
            | config.command_channel_ids
        ))
        self.assertIsNone(config.backfill_limit_per_channel)

    def test_channel_tier_supports_threads_by_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            write_env(env_path)
            config = load_config(env_path)

        self.assertEqual(config.tier_for(int(IDS[0])), "official")
        self.assertEqual(
            config.tier_for(int(IDS[9]), parent_channel_id=int(IDS[4])),
            "community",
        )
        self.assertIsNone(config.tier_for(int(IDS[10])))

    def test_collect_list_cannot_include_unapproved_channel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            write_env(env_path, collect_override=",".join(IDS[0:8]))
            with self.assertRaises(ConfigError):
                load_config(env_path)


class PrivacyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.privacy = PrivacyFilter("s" * 64)

    def test_pseudonym_is_stable_and_secret_dependent(self) -> None:
        first = self.privacy.pseudonymize("123456789012345678")
        second = self.privacy.pseudonymize("123456789012345678")
        other_secret = PrivacyFilter("x" * 64).pseudonymize("123456789012345678")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other_secret)
        self.assertNotIn("123456789012345678", first)

    def test_redacts_common_personal_and_secret_values(self) -> None:
        content = (
            "Mail me@example.com phone 0912 345 678, <@123456789012345678>, "
            "token=super-secret and https://discord.gg/privateInvite"
        )
        redacted = self.privacy.redact(content)
        self.assertNotIn("me@example.com", redacted)
        self.assertNotIn("0912 345 678", redacted)
        self.assertNotIn("123456789012345678", redacted)
        self.assertNotIn("super-secret", redacted)
        self.assertNotIn("privateInvite", redacted)


class StorageTests(unittest.TestCase):
    def _record(self, *, message_id: int = 1, content: str = "hello") -> MessageRecord:
        return MessageRecord(
            message_id=message_id,
            guild_id=2,
            channel_id=3,
            parent_channel_id=None,
            tier="community",
            author_hash="usr_abc",
            author_type="student",
            content_redacted=content,
            reply_to_message_id=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            edited_at=None,
            attachment_count=0,
            jump_url="https://discord.com/channels/2/3/1",
        )

    def test_upsert_is_idempotent_and_tracks_latest_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with MessageStore(Path(directory) / "messages.sqlite3") as store:
                store.upsert(self._record(content="first"))
                store.upsert(self._record(content="edited"))
                row = store.connection.execute(
                    "SELECT content_redacted FROM messages WHERE message_id = 1"
                ).fetchone()
                self.assertEqual(store.count_messages(), 1)
                self.assertEqual(row["content_redacted"], "edited")
                self.assertEqual(store.last_message_id(3), 1)

    def test_deleted_message_loses_content_and_author_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with MessageStore(Path(directory) / "messages.sqlite3") as store:
                store.upsert(self._record())
                self.assertTrue(store.mark_deleted(1))
                row = store.connection.execute(
                    "SELECT deleted, content_redacted, author_hash FROM messages"
                ).fetchone()
                self.assertEqual(row["deleted"], 1)
                self.assertIsNone(row["content_redacted"])
                self.assertIsNone(row["author_hash"])

    def test_retention_permanently_removes_expired_messages(self) -> None:
        old_record = self._record(message_id=2)
        old_record = MessageRecord(
            **{
                **old_record.__dict__,
                "created_at": (
                    datetime.now(timezone.utc) - timedelta(days=31)
                ).isoformat(),
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            with MessageStore(Path(directory) / "messages.sqlite3") as store:
                store.upsert(old_record)
                self.assertEqual(store.purge_expired(30), 1)
                self.assertEqual(store.count_messages(), 0)


if __name__ == "__main__":
    unittest.main()
