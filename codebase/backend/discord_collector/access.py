from __future__ import annotations

import discord


class GuildInspector(discord.Client):
    async def on_ready(self) -> None:
        print(f"Bot: {self.user}")
        if not self.guilds:
            print("Bot is not installed in any server.")
        for guild in self.guilds:
            print(f"Guild: {guild.name} | ID: {guild.id}")
        await self.close()


def inspect_guilds(token: str) -> None:
    intents = discord.Intents.none()
    intents.guilds = True
    client = GuildInspector(intents=intents)
    client.run(token, log_handler=None)
