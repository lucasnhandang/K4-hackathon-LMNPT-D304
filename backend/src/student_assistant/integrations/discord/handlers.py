"""Discord Gateway event handlers."""

import logging

import discord
import httpx

from student_assistant.integrations.discord.client import BackendChatClient
from student_assistant.integrations.discord.parsing import (
    discord_role_ids,
    discord_safe_reply,
    extract_question,
    is_allowed_channel,
    should_ingest_knowledge_message,
)


logger = logging.getLogger("student-assistant-discord")


class StudentAssistantClient(discord.Client):
    def __init__(
        self,
        backend_client: BackendChatClient,
        allowed_channel_ids: set[int],
        knowledge_channel_ids: set[int],
    ) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.backend_client = backend_client
        self.allowed_channel_ids = allowed_channel_ids
        self.knowledge_channel_ids = knowledge_channel_ids

    async def setup_hook(self) -> None:
        await self.backend_client.start()

    async def close(self) -> None:
        await self.backend_client.close()
        await super().close()

    async def on_ready(self) -> None:
        if self.user is None:
            return
        logger.info(
            "Bot đã online: %s (id=%s), đang ở %s server",
            self.user,
            self.user.id,
            len(self.guilds),
        )
        logger.info(
            "Kênh tự thu thập knowledge: %s",
            sorted(self.knowledge_channel_ids),
        )

    async def _ingest_knowledge_message(
        self,
        message: discord.Message,
    ) -> None:
        content = message.content.strip()
        if not content:
            logger.info(
                "Bỏ qua knowledge message không có text: channel=%s message=%s",
                message.channel.id,
                message.id,
            )
            return

        payload = {
            "content": content,
            "author_id": str(message.author.id),
            "author_role_ids": discord_role_ids(message.author),
            "guild_id": str(message.guild.id),
            "channel_id": str(message.channel.id),
            "discord_message_id": str(message.id),
            "discord_created_at": message.created_at.isoformat(),
        }
        try:
            data = await self.backend_client.ingest_knowledge(payload)
            logger.info(
                "Đã lưu knowledge từ Discord: guild=%s channel=%s "
                "user=%s message=%s status=%s document=%s",
                message.guild.id,
                message.channel.id,
                message.author.id,
                message.id,
                data.get("status", "unknown"),
                data.get("document_id", "unknown"),
            )
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Bỏ qua Discord knowledge message=%s vì backend trả HTTP %s",
                message.id,
                exc.response.status_code,
            )
        except (httpx.RequestError, RuntimeError, ValueError):
            logger.exception(
                "Không thể lưu Discord knowledge message=%s",
                message.id,
            )

    async def on_message(self, message: discord.Message) -> None:
        if self.user is None:
            return
        if message.guild is None or message.author.bot:
            return
        mentioned = self.user in message.mentions
        if not mentioned:
            if should_ingest_knowledge_message(
                message.channel.id,
                self.knowledge_channel_ids,
                bot_is_mentioned=False,
            ):
                await self._ingest_knowledge_message(message)
            return

        logger.info(
            "Discord đã giao tin nhắn mention bot: guild=%s channel=%s "
            "user=%s message=%s",
            message.guild.id,
            message.channel.id,
            message.author.id,
            message.id,
        )

        if not is_allowed_channel(
            message.channel.id,
            self.allowed_channel_ids,
        ):
            logger.info(
                "Bỏ qua mention vì channel không được phép: channel=%s",
                message.channel.id,
            )
            return

        question = extract_question(message.content, self.user.id)
        if not question:
            logger.info(
                "Nhận mention rỗng: guild=%s channel=%s user=%s message=%s",
                message.guild.id,
                message.channel.id,
                message.author.id,
                message.id,
            )
            await message.reply(
                "Bạn hãy mention mình kèm câu hỏi nhé. Ví dụ: "
                f"{self.user.mention} deadline bài tuần này là khi nào?",
                mention_author=False,
            )
            return

        logger.info(
            "Nhận câu hỏi qua @bot: guild=%s channel=%s user=%s "
            "message=%s question_length=%s",
            message.guild.id,
            message.channel.id,
            message.author.id,
            message.id,
            len(question),
        )

        payload = {
            "message": question,
            "history": [],
            "student_id": str(message.author.id),
            "bot_id": str(self.user.id),
            "user_role_ids": discord_role_ids(message.author),
            "channel_id": str(message.channel.id),
            "guild_id": str(message.guild.id),
            "discord_message_id": str(message.id),
        }

        try:
            async with message.channel.typing():
                data = await self.backend_client.send_message(payload)

            answer = discord_safe_reply(
                str(data.get("reply") or "Mình chưa tạo được câu trả lời.")
            )
            reply_message = await message.reply(answer, mention_author=False)
            logger.info(
                "Đã trả lời @bot thành công: request_message=%s "
                "reply_message=%s decision=%s",
                message.id,
                reply_message.id,
                data.get("action", "UNKNOWN"),
            )
        except httpx.TimeoutException:
            logger.warning(
                "Backend timeout khi xử lý Discord message id=%s",
                message.id,
            )
            await message.reply(
                "Mình xử lý hơi lâu và đã hết thời gian chờ. Bạn thử lại nhé.",
                mention_author=False,
            )
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.replace("\r", " ").replace("\n", " ")
            logger.error(
                "Backend trả lỗi HTTP %s cho Discord message id=%s detail=%r",
                exc.response.status_code,
                message.id,
                detail[:500],
            )
            if exc.response.status_code == 429:
                user_message = (
                    "Bạn đang gửi yêu cầu quá nhanh. "
                    "Vui lòng thử lại sau khoảng 1 phút."
                )
            elif exc.response.status_code == 400:
                try:
                    user_message = str(exc.response.json().get("detail"))
                except ValueError:
                    user_message = "Tin nhắn không vượt qua kiểm tra an toàn."
            else:
                user_message = (
                    "Hệ thống trả lời đang gặp lỗi. Bạn thử lại sau nhé."
                )
            await message.reply(user_message, mention_author=False)
        except (httpx.RequestError, RuntimeError, ValueError):
            logger.exception(
                "Không gọi được backend cho Discord message id=%s",
                message.id,
            )
            await message.reply(
                "Mình chưa kết nối được với hệ thống trả lời. Bạn thử lại sau nhé.",
                mention_author=False,
            )
        except discord.DiscordException:
            logger.exception(
                "Không thể gửi phản hồi cho Discord message id=%s",
                message.id,
            )
