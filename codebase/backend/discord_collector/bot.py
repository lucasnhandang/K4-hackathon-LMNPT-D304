from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

import discord

from .config import CollectorConfig
from .privacy import PrivacyFilter
from .storage import MessageRecord, MessageStore


LOGGER = logging.getLogger("discord_collector")


class DiscordCollector(discord.Client):
    def __init__(self, config: CollectorConfig):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.config = config
        self.privacy = PrivacyFilter(config.pseudonym_secret)
        self.store = MessageStore(config.database_path)
        self._backfill_lock = asyncio.Lock()
        self._backfill_finished = False

    async def setup_hook(self) -> None:
        removed = self.store.purge_expired(self.config.retention_days)
        LOGGER.info("Retention cleanup removed %d expired messages.", removed)

    async def on_ready(self) -> None:
        LOGGER.info("Connected as %s.", self.user)
        guild = self.get_guild(self.config.guild_id)
        if guild is None:
            LOGGER.error("Configured guild is unavailable to this bot.")
            return
        if self.config.backfill_on_start and not self._backfill_finished:
            async with self._backfill_lock:
                if not self._backfill_finished:
                    await self.backfill_guild(guild)
                    self._backfill_finished = True

    async def _target_and_threads(
        self,
        channel: discord.abc.GuildChannel,
    ) -> AsyncIterator[discord.abc.Messageable]:
        seen: set[int] = set()
        if hasattr(channel, "history"):
            seen.add(channel.id)
            yield channel  # type: ignore[misc]

        for thread in getattr(channel, "threads", []):
            if thread.id not in seen:
                seen.add(thread.id)
                yield thread

        archived_threads = getattr(channel, "archived_threads", None)
        if archived_threads:
            try:
                async for thread in archived_threads(limit=None):
                    if thread.id not in seen:
                        seen.add(thread.id)
                        yield thread
            except discord.Forbidden:
                LOGGER.warning("No permission to read archived threads in %s.", channel.name)

    async def backfill_guild(self, guild: discord.Guild) -> None:
        LOGGER.info("Starting backfill for %d allowlisted channels.", len(self.config.collect_channel_ids))
        for channel_id in sorted(self.config.collect_channel_ids):
            channel = guild.get_channel(channel_id)
            if channel is None:
                try:
                    fetched = await guild.fetch_channel(channel_id)
                    channel = fetched if isinstance(fetched, discord.abc.GuildChannel) else None
                except (discord.Forbidden, discord.NotFound):
                    channel = None
            if channel is None:
                LOGGER.error("An allowlisted channel is missing or inaccessible.")
                continue

            tier = self.config.tier_for(channel.id)
            if tier is None:
                continue
            async for target in self._target_and_threads(channel):
                await self.sync_history(target, tier)
        LOGGER.info("Backfill complete. Stored messages: %d.", self.store.count_messages())

    async def sync_history(self, target: discord.abc.Messageable, tier: str) -> None:
        channel_id = target.id  # type: ignore[attr-defined]
        last_id = self.store.last_message_id(channel_id)
        after = discord.Object(id=last_id) if last_id else None
        stored = 0
        try:
            async for message in target.history(  # type: ignore[attr-defined]
                limit=self.config.backfill_limit_per_channel,
                after=after,
                oldest_first=True,
            ):
                self._store_message(message, tier)
                stored += 1
        except discord.Forbidden:
            LOGGER.warning("Missing Read Message History for one allowlisted channel/thread.")
            return
        LOGGER.info("Synced %d new messages from %s.", stored, getattr(target, "name", channel_id))

    def _store_message(self, message: discord.Message, tier: str) -> None:
        parent_id = getattr(message.channel, "parent_id", None)
        if message.webhook_id is not None:
            author_type = "webhook"
        elif message.author.bot:
            author_type = "bot"
        else:
            author_type = "student"

        record = MessageRecord(
            message_id=message.id,
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            parent_channel_id=parent_id,
            tier=tier,
            author_hash=self.privacy.pseudonymize(message.author.id),
            author_type=author_type,
            content_redacted=self.privacy.redact(message.content or ""),
            reply_to_message_id=(
                message.reference.message_id if message.reference else None
            ),
            created_at=message.created_at.isoformat(),
            edited_at=message.edited_at.isoformat() if message.edited_at else None,
            attachment_count=len(message.attachments),
            jump_url=message.jump_url,
        )
        self.store.upsert(record)

    def _tier_for_message(self, message: discord.Message) -> str | None:
        if message.guild is None or message.guild.id != self.config.guild_id:
            return None
        return self.config.tier_for(
            message.channel.id,
            getattr(message.channel, "parent_id", None),
        )

    async def on_message(self, message: discord.Message) -> None:
        tier = self._tier_for_message(message)
        if tier:
            self._store_message(message, tier)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if payload.guild_id != self.config.guild_id:
            return
        channel = self.get_channel(payload.channel_id)
        parent_id = getattr(channel, "parent_id", None) if channel else None
        tier = self.config.tier_for(payload.channel_id, parent_id)
        if not tier or channel is None or not hasattr(channel, "fetch_message"):
            return
        try:
            message = await channel.fetch_message(payload.message_id)  # type: ignore[attr-defined]
        except (discord.Forbidden, discord.NotFound):
            return
        self._store_message(message, tier)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if payload.guild_id == self.config.guild_id:
            self.store.mark_deleted(payload.message_id)

    async def on_raw_bulk_message_delete(
        self,
        payload: discord.RawBulkMessageDeleteEvent,
    ) -> None:
        if payload.guild_id == self.config.guild_id:
            for message_id in payload.message_ids:
                self.store.mark_deleted(message_id)

    async def close(self) -> None:
        self.store.close()
        await super().close()
