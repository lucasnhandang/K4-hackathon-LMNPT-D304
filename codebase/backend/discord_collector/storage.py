from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class MessageRecord:
    message_id: int
    guild_id: int
    channel_id: int
    parent_channel_id: int | None
    tier: str
    author_hash: str
    author_type: str
    content_redacted: str
    reply_to_message_id: int | None
    created_at: str
    edited_at: str | None
    attachment_count: int
    jump_url: str


class MessageStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                parent_channel_id INTEGER,
                tier TEXT NOT NULL CHECK (tier IN ('official', 'community', 'command')),
                author_hash TEXT,
                author_type TEXT NOT NULL CHECK (author_type IN ('student', 'bot', 'webhook')),
                content_redacted TEXT,
                reply_to_message_id INTEGER,
                created_at TEXT NOT NULL,
                edited_at TEXT,
                attachment_count INTEGER NOT NULL DEFAULT 0,
                jump_url TEXT NOT NULL,
                deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1)),
                collected_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_channel_created
                ON messages(channel_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_messages_tier_created
                ON messages(tier, created_at);
            CREATE INDEX IF NOT EXISTS idx_messages_reply
                ON messages(reply_to_message_id);

            CREATE TABLE IF NOT EXISTS sync_state (
                channel_id INTEGER PRIMARY KEY,
                last_message_id INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def upsert(self, record: MessageRecord) -> None:
        collected_at = datetime.now(timezone.utc).isoformat()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO messages (
                    message_id, guild_id, channel_id, parent_channel_id, tier,
                    author_hash, author_type, content_redacted, reply_to_message_id,
                    created_at, edited_at, attachment_count, jump_url, deleted,
                    collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    tier = excluded.tier,
                    author_hash = excluded.author_hash,
                    author_type = excluded.author_type,
                    content_redacted = excluded.content_redacted,
                    reply_to_message_id = excluded.reply_to_message_id,
                    edited_at = excluded.edited_at,
                    attachment_count = excluded.attachment_count,
                    jump_url = excluded.jump_url,
                    deleted = 0,
                    collected_at = excluded.collected_at
                """,
                (
                    record.message_id,
                    record.guild_id,
                    record.channel_id,
                    record.parent_channel_id,
                    record.tier,
                    record.author_hash,
                    record.author_type,
                    record.content_redacted,
                    record.reply_to_message_id,
                    record.created_at,
                    record.edited_at,
                    record.attachment_count,
                    record.jump_url,
                    collected_at,
                ),
            )
            self.connection.execute(
                """
                INSERT INTO sync_state(channel_id, last_message_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    last_message_id = MAX(last_message_id, excluded.last_message_id),
                    updated_at = excluded.updated_at
                """,
                (record.channel_id, record.message_id, collected_at),
            )

    def last_message_id(self, channel_id: int) -> int | None:
        row = self.connection.execute(
            "SELECT last_message_id FROM sync_state WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()
        return int(row["last_message_id"]) if row else None

    def mark_deleted(self, message_id: int) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE messages
                SET deleted = 1, content_redacted = NULL, author_hash = NULL,
                    collected_at = ?
                WHERE message_id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), message_id),
            )
        return cursor.rowcount > 0

    def purge_expired(self, retention_days: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
        with self.connection:
            cursor = self.connection.execute(
                "DELETE FROM messages WHERE created_at < ?",
                (cutoff,),
            )
        return cursor.rowcount

    def count_messages(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "MessageStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
