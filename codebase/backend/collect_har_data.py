"""Script to parse Discord messages from docs/discord.com.har and insert into SQLite database.

Usage:
    python collect_har_data.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from discord_collector.privacy import PrivacyFilter
from discord_collector.storage import MessageRecord, MessageStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_har_data")


def parse_and_store_har(
    har_path: str | Path,
    db_path: str | Path,
    secret: str = "0123456789abcdef0123456789abcdef",
) -> int:
    har_file = Path(har_path)
    if not har_file.exists():
        logger.error("HAR file not found: %s", har_file)
        return 0

    logger.info("Reading HAR file: %s", har_file)
    with har_file.open("r", encoding="utf-8", errors="ignore") as f:
        har = json.load(f)

    entries = har.get("log", {}).get("entries", [])
    raw_messages = []

    for entry in entries:
        req = entry.get("request", {})
        url = req.get("url", "")
        if "/api/v9/channels/" in url and "/messages" in url:
            resp = entry.get("response", {})
            content = resp.get("content", {})
            text = content.get("text", "")
            if text:
                try:
                    payload = json.loads(text)
                    if isinstance(payload, list):
                        raw_messages.extend(payload)
                    elif isinstance(payload, dict) and "id" in payload:
                        raw_messages.append(payload)
                except Exception:
                    pass

    # Deduplicate by message ID
    unique_messages = {str(m["id"]): m for m in raw_messages if "id" in m}
    logger.info("Extracted %d unique messages from HAR", len(unique_messages))

    privacy = PrivacyFilter(secret=secret)

    saved_count = 0
    with MessageStore(db_path) as store:
        for msg_id_str, msg in unique_messages.items():
            try:
                message_id = int(msg["id"])
                channel_id = int(msg.get("channel_id", 0))
                guild_id = int(msg.get("guild_id", 1526532830627102781))

                author_dict = msg.get("author", {})
                author_id = author_dict.get("id", "0")
                is_bot = author_dict.get("bot", False)

                author_type = "bot" if is_bot else "student"
                author_hash = privacy.pseudonymize(author_id)

                content = msg.get("content", "")
                content_redacted = privacy.redact(content)

                # Determine tier
                if is_bot:
                    tier = "official"
                elif content.strip().startswith("/"):
                    tier = "command"
                else:
                    tier = "community"

                # Reply to message ID
                reply_to_id = None
                if msg.get("referenced_message") and isinstance(msg["referenced_message"], dict):
                    reply_to_id = int(msg["referenced_message"]["id"])
                elif msg.get("message_reference") and isinstance(msg["message_reference"], dict):
                    ref_id = msg["message_reference"].get("message_id")
                    if ref_id:
                        reply_to_id = int(ref_id)

                created_at = msg.get("timestamp", "")
                edited_at = msg.get("edited_timestamp")
                attachments = msg.get("attachments", [])
                attachment_count = len(attachments) if isinstance(attachments, list) else 0

                jump_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

                record = MessageRecord(
                    message_id=message_id,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    parent_channel_id=None,
                    tier=tier,
                    author_hash=author_hash,
                    author_type=author_type,
                    content_redacted=content_redacted,
                    reply_to_message_id=reply_to_id,
                    created_at=created_at,
                    edited_at=edited_at,
                    attachment_count=attachment_count,
                    jump_url=jump_url,
                )

                store.upsert(record)
                saved_count += 1
            except Exception as e:
                logger.warning("Failed to store message %s: %s", msg_id_str, e)

    logger.info("Successfully stored %d messages in SQLite database at %s", saved_count, db_path)
    return saved_count


def main() -> None:
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    backend_dir = Path(__file__).parent
    repo_root = backend_dir.parent.parent
    har_path = repo_root / "docs" / "discord.com.har"
    db_path = backend_dir / "runtime" / "discord_messages.sqlite3"

    count = parse_and_store_har(har_path, db_path)
    print(f"✅ Data collection complete: Imported {count} messages into {db_path}")


if __name__ == "__main__":
    main()
