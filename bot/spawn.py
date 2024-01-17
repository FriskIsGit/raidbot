import discord
import random
import asyncio

from typing import Dict
from datetime import datetime
from collections import deque, namedtuple
from dataclasses import dataclass

SPAWN_CHANCE_RANGE = (40, 55)
SEND_INSTEAD_OF_PRINT = False
CachedMessage = namedtuple("CachedMessage", ["content", "author_id"])


@dataclass
class SpawnCooldown:
    """
    Represents the spawn internal system per guild. Contains the counters that will determine
    if a countryball should be spawned next or not.

    Attributes
    ----------
    time: datetime
        Time when the object was initialized. Block spawning when it's been less than two minutes
    amount: float
        A number starting at 0, incrementing with the messages until reaching `chance`. At this
        point, a ball will be spawned next.
    chance: int
        The number `amount` has to reach for spawn. Determined randomly with `SPAWN_CHANCE_RANGE`
    lock: asyncio.Lock
        Used to ratelimit messages and ignore fast spam
    message_cache: ~collections.deque[CachedMessage]
        A list of recent messages used to reduce the spawn chance when too few different chatters
        are present. Limited to the 100 most recent messages in the guild.
    """

    def __init__(self, created_at: datetime):
        self.time: datetime = created_at
        self.amount: float = SPAWN_CHANCE_RANGE[0] // 2
        self.chance: int = random.randint(*SPAWN_CHANCE_RANGE)
        self.lock: asyncio.Lock = asyncio.Lock()
        self.message_cache: deque[CachedMessage] = deque(maxlen=100)

    def reset(self, time: datetime):
        self.amount = 1.0
        self.chance = random.randint(*SPAWN_CHANCE_RANGE)
        try:
            self.lock.release()
        except RuntimeError:  # lock is not acquired
            pass
        self.time = time

    async def increase(self, message: discord.Message) -> bool:
        # this is a deque, not a list
        # its property is that, once the max length is reached (100 for us),
        # the oldest element is removed, thus we only have the last 100 messages in memory
        self.message_cache.append(
            CachedMessage(content=message.content, author_id=message.author.id)
        )
        if self.lock.locked():
            print("Can't increase, I'm sleeping..")
            return False

        async with self.lock:
            amount = 1
            if message.guild.member_count < 5 or message.guild.member_count > 1000:
                amount /= 2
                print(f'Lost half on member_count < 5 or > 1000')
                
            if len(message.content) < 5:
                amount /= 2
                print(f'Lost half on message len < 5')

            if len(set(x.author_id for x in self.message_cache)) < 4:
                print(f'Lost half on lack of 4 distinct users')
                amount /= 2
            cache_len = len(list(filter(lambda x: x.author_id == message.author.id, self.message_cache)))
            contribution = cache_len / self.message_cache.maxlen > 0.4

            if contribution:
                await message.channel.send(f'Message contribution: {cache_len / self.message_cache.maxlen} exceeded 0.4')

            self.amount += amount
            if SEND_INSTEAD_OF_PRINT:
                await message.channel.send(f'Increased by {amount}, going to sleep for 10s')
            else:
                print(f'Increased by {amount}, going to sleep for 10s')
            await asyncio.sleep(10)
            print(f'Woke up')
        return True


@dataclass
class SpawnManager:
    def __init__(self):
        self.cooldowns: Dict[int, SpawnCooldown] = dict()
        self.cache: Dict[int, int] = dict()

    async def handle_message(self, message: discord.Message):
        # moved this check here for clarity
        if message.author.bot:
            return

        guild = message.guild
        if not guild:
            return

        cooldown = self.cooldowns.get(guild.id, None)
        if not cooldown:
            cooldown = SpawnCooldown(message.created_at)
            self.cooldowns[guild.id] = cooldown
            print(f"Created cooldown manager for guild {guild.id}")

        delta = (message.created_at - cooldown.time).total_seconds()
        # change how the threshold varies according to the member count, while nuking farm servers
        if guild.member_count < 5:
            multiplier = 0.1
        elif guild.member_count < 100:
            multiplier = 0.8
        elif guild.member_count < 1000:
            multiplier = 0.5
        else:
            multiplier = 0.2

        chance = cooldown.chance - multiplier * (delta // 60)
        print(f'{cooldown.chance} - {multiplier * (delta // 60)}')
        print(f'{chance}')
        # manager cannot be increased more than once per 5 seconds
        if not await cooldown.increase(message):
            print(f"Handled message {message.id}, skipping due to spam control")
            return

        # normal increase, need to reach goal
        if cooldown.amount <= chance:
            if SEND_INSTEAD_OF_PRINT:
                await message.channel.send(f"Handled message {message.id}, count: {cooldown.amount}/{chance}")
            else:
                print(f"Handled message {message.id}, count: {cooldown.amount}/{chance}")
            return

        # at this point, the goal is reached
        if delta < 600:
            # wait for at least 10 minutes before spawning
            print(f"Handled message {message.id}, waiting for manager to be 10 mins old")
            return

        # spawn countryball
        cooldown.reset(message.created_at)
        if SEND_INSTEAD_OF_PRINT:
            await message.channel.send(f"Handled message {message.id}, spawning ball")
        else:
            print(f"Handled message {message.id}, spawning ball")
