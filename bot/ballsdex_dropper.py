import asyncio
import string
import random
import discord

from bot import spawn

# designed to target one server from another server
PREFIX = '.'
TOKEN = 'MTEzMDk1OTMxOTU0MjgwODU5OQ.GQgNTY.0mccKMvQvuWrclibXyBrv5V87AAOPXLnhlBB0g'
INFO_CHANNEL_ID = 1133026684304625716
DROP_GUILD_ID = 1130959129503076472
BALLS_DEX_ID = 999736048596816014
spawn_manager = spawn.SpawnManager()


class SharedState:
    enabled = False


def random_word(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class BallsDropper(discord.Client):

    def init_data(self):
        self.info_channel = None

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.info_channel = await self.fetch_channel(INFO_CHANNEL_ID)

    async def on_message(self, message):
        if message.guild.id != DROP_GUILD_ID:
            return

        await spawn_manager.handle_message(message)
        content = message.content.strip()
        if content.startswith(PREFIX):
            await self.resolve_as_command(message, content)
            return

        if message.author.id == BALLS_DEX_ID and message.content.startswith("A wild"):
            SharedState.enabled = False
            print("Ball dropped")
            await message.channel.send("Ball dropped")
            await asyncio.sleep(60)
            SharedState.enabled = True
            return

    async def resolve_as_command(self, message, content):
        content = content[1:]
        content = content.split()
        if len(content) == 0:
            return

        command = content[0]
        args = content[1:]

        if command == 'alive':
            await message.channel.send('alive')
            return


bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot_intents.members = True
bot_intents.bans = True

client = BallsDropper(intents=bot_intents)
client.init_data()

client.run(TOKEN)
