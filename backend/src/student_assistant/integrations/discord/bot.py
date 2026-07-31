"""Discord bot process entrypoint."""

from student_assistant.core.config import settings
from student_assistant.core.logging import configure_logging
from student_assistant.integrations.discord.client import BackendChatClient
from student_assistant.integrations.discord.handlers import (
    StudentAssistantClient,
)
from student_assistant.integrations.discord.parsing import parse_channel_ids


def main() -> None:
    configure_logging()
    token = settings.discord_bot_token.strip()
    if not token:
        raise RuntimeError(
            "Thiếu DISCORD_BOT_TOKEN. Hãy thêm token vào backend/.env."
        )

    backend_client = BackendChatClient(
        settings.backend_base_url,
        settings.backend_timeout_seconds,
    )
    client = StudentAssistantClient(
        backend_client,
        parse_channel_ids(settings.discord_allowed_channel_ids),
        parse_channel_ids(
            settings.discord_kb_channel_ids,
            "DISCORD_KB_CHANNEL_IDS",
        ),
    )
    client.run(token, log_handler=None)


if __name__ == "__main__":
    main()
