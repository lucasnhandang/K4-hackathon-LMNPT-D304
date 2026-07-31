"""Discord bot integration for the student assistant.

Listens to Discord messages and processes them through the ChatbotOrchestrator.
Requires discord.py >= 2.6 and a valid bot token in .env.
"""

from __future__ import annotations

import os
import logging
from typing import Any

import discord
from discord import app_commands

from chatbot_tools.orchestrator import ChatbotOrchestrator
from chatbot_tools.registry import build_default_registry

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
ALLOWED_CHANNELS: set[str] = set()

# Parse allowed channels from env
for i in range(1, 20):
    ch = os.getenv(f"CHANNEL_{i}")
    if ch:
        ALLOWED_CHANNELS.add(ch)


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Initialize orchestrator
orchestrator = ChatbotOrchestrator(build_default_registry())

# Store pending clarifications per user
pending_clarifications: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def pseudonymize_user(user: discord.User) -> str:
    """Create a pseudonymized user ID using HMAC."""
    import hashlib
    import os

    secret = os.getenv("PSEUDONYM_SECRET", "default-secret")
    raw = f"{user.id}:{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def is_allowed_channel(channel_id: int) -> bool:
    """Check if the channel is in the allowed list."""
    if not ALLOWED_CHANNELS:
        return True  # If no channels configured, allow all
    return str(channel_id) in ALLOWED_CHANNELS


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@client.event
async def on_ready():
    logger.info("Logged in as %s (ID: %s)", client.user, client.user.id)
    logger.info("Allowed channels: %s", ALLOWED_CHANNELS or "all")

    # Sync slash commands
    try:
        synced = await tree.sync()
        logger.info("Synced %d slash commands", len(synced))
    except Exception as e:
        logger.error("Failed to sync commands: %s", e)


@client.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Ignore messages outside allowed channels
    if not is_allowed_channel(message.channel.id):
        return

    # Check if bot is mentioned or replying to bot
    bot_mentioned = client.user in message.mentions
    is_reply_to_bot = (
        message.reference
        and message.reference.resolved
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author == client.user
    )

    # Only respond if mentioned or replying to bot
    if not bot_mentioned and not is_reply_to_bot:
        return

    # Clean mention from message
    content = message.content
    if bot_mentioned:
        content = content.replace(f"<@{client.user.id}>", "").strip()
        content = content.replace(f"<@!{client.user.id}>", "").strip()

    if not content:
        await message.channel.send("Bạn cần hỏi gì nha? 😊")
        return

    # Process message
    user_id = pseudonymize_user(message.author)
    session_id = f"session_{message.channel.id}_{message.author.id}"

    # Check for pending clarification
    pending = pending_clarifications.get(user_id)

    # Show typing indicator
    async with message.channel.typing():
        response = orchestrator.process_message(
            message=content,
            user_id=user_id,
            session_id=session_id,
            channel_id=str(message.channel.id),
            pending_clarification=pending,
        )

    # Send response
    route = response.get("route", "ANSWER")
    response_text = response.get("response", "")

    # Handle clarification
    if route == "CLARIFY":
        clarification = response.get("clarification", {})
        suggested = clarification.get("suggested_replies", [])

        # Add suggested replies as buttons if available
        if suggested:
            view = SuggestionView(suggested, user_id, pending_clarifications)
            await message.channel.send(response_text, view=view)
        else:
            await message.channel.send(response_text)

        # Store pending clarification
        pending_clarifications[user_id] = clarification

    # Handle escalation
    elif route == "ESCALATE":
        escalation = response.get("escalation", {})
        target = escalation.get("target", "Mod")

        # Ping the appropriate role
        role_mentions = {
            "MOD": "@Mod",
            "TA": "@TA",
            "MENTOR": "@Mentor",
        }
        role_text = role_mentions.get(target, f"@{target}")

        await message.channel.send(f"{response_text}\n\n{role_text} vui lòng hỗ trợ! 🙏")

        # Clear pending clarification
        pending_clarifications.pop(user_id, None)

    # Handle answer
    else:
        await message.channel.send(response_text)

        # Clear pending clarification if any
        pending_clarifications.pop(user_id, None)

    # Log the interaction
    logger.info(
        "User=%s Channel=%s Intent=%s Route=%s Confidence=%.2f",
        user_id,
        message.channel.id,
        response.get("intent", "unknown"),
        route,
        response.get("confidence", 0),
    )


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

@tree.command(name="ask", description="Hỏi trợ lý AI về thông tin khóa học")
@app_commands.describe(question="Câu hỏi của bạn")
async def ask_command(interaction: discord.Interaction, question: str):
    """Handle /ask slash command."""
    await interaction.response.defer()

    user_id = pseudonymize_user(interaction.user)
    session_id = f"session_{interaction.channel_id}_{interaction.user.id}"

    response = orchestrator.process_message(
        message=question,
        user_id=user_id,
        session_id=session_id,
        channel_id=str(interaction.channel_id),
    )

    # Format response for slash command
    route = response.get("route", "ANSWER")
    response_text = response.get("response", "")

    if route == "CLARIFY":
        clarification = response.get("clarification", {})
        suggested = clarification.get("suggested_replies", [])

        if suggested:
            view = SuggestionView(suggested, user_id, pending_clarifications)
            await interaction.followup.send(response_text, view=view)
        else:
            await interaction.followup.send(response_text)

        pending_clarifications[user_id] = clarification

    elif route == "ESCALATE":
        escalation = response.get("escalation", {})
        target = escalation.get("target", "Mod")
        role_mentions = {"MOD": "@Mod", "TA": "@TA", "MENTOR": "@Mentor"}
        role_text = role_mentions.get(target, f"@{target}")
        await interaction.followup.send(f"{response_text}\n\n{role_text} vui lòng hỗ trợ! 🙏")
        pending_clarifications.pop(user_id, None)

    else:
        await interaction.followup.send(response_text)
        pending_clarifications.pop(user_id, None)


@tree.command(name="help_bot", description="Xem hướng dẫn sử dụng trợ lý AI")
async def help_command(interaction: discord.Interaction):
    """Handle /help_bot slash command."""
    from chatbot_tools.response_generator import HELP_RESPONSE
    await interaction.response.send_message(HELP_RESPONSE)


# ---------------------------------------------------------------------------
# Suggestion view (buttons for quick replies)
# ---------------------------------------------------------------------------

class SuggestionView(discord.ui.View):
    """View with suggestion buttons for quick replies."""

    def __init__(self, suggestions: list[str], user_id: str, pending: dict):
        super().__init__(timeout=60)
        self.suggestions = suggestions
        self.user_id = user_id
        self.pending = pending

        for suggestion in suggestions[:5]:  # Max 5 buttons
            button = discord.ui.Button(
                label=suggestion[:80],  # Discord button label limit
                style=discord.ButtonStyle.primary,
                custom_id=f"suggestion_{hash(suggestion)}",
            )
            button.callback = self._make_callback(suggestion)
            self.add_item(button)

    def _make_callback(self, suggestion: str):
        async def callback(interaction: discord.Interaction):
            # Process the suggestion as a new message
            user_id = pseudonymize_user(interaction.user)
            session_id = f"session_{interaction.channel_id}_{interaction.user.id}"

            pending = self.pending.get(user_id)

            response = orchestrator.process_message(
                message=suggestion,
                user_id=user_id,
                session_id=session_id,
                channel_id=str(interaction.channel_id),
                pending_clarification=pending,
            )

            route = response.get("route", "ANSWER")
            response_text = response.get("response", "")

            if route == "CLARIFY":
                clarification = response.get("clarification", {})
                new_suggestions = clarification.get("suggested_replies", [])
                if new_suggestions:
                    new_view = SuggestionView(new_suggestions, user_id, self.pending)
                    await interaction.response.edit_message(content=response_text, view=new_view)
                else:
                    await interaction.response.edit_message(content=response_text, view=None)
                self.pending[user_id] = clarification
            elif route == "ESCALATE":
                escalation = response.get("escalation", {})
                target = escalation.get("target", "Mod")
                role_mentions = {"MOD": "@Mod", "TA": "@TA", "MENTOR": "@Mentor"}
                role_text = role_mentions.get(target, f"@{target}")
                await interaction.response.edit_message(
                    content=f"{response_text}\n\n{role_text} vui lòng hỗ trợ! 🙏",
                    view=None,
                )
                self.pending.pop(user_id, None)
            else:
                await interaction.response.edit_message(content=response_text, view=None)
                self.pending.pop(user_id, None)

        return callback


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Start the Discord bot."""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in environment")
        return

    client.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
