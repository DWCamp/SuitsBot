from typing import Optional
import json
from discord import Embed, Message, Reaction, User
from discord.errors import NotFound
import redis

from constants import DELETE_EMOJI
import utils


"""
EmbedGenerator

EmbedGenerators are objects which parse the contents of a message for any information
which the bot can 'unfurl' into an embed containing additional information. This class
both serves as a base class which specific generators are derived from and also to
provide static methods for providing common functionality and coordinating the bot's
many generators.   
"""

# key prefixes
BASE_PREFIX = "EG-"
TRIGGER_PREFIX = f"{BASE_PREFIX}TRIG-"  # IDs of Trigger messages
UNFURL_PREFIX = f"{BASE_PREFIX}UNFURL-"  # IDs of messages with embeds

# redis entry timeout config
RECENTLY_UNFURLED_TIMEOUT = 3600  # How long to wait before unfurling the same thing again (1 hr)
UNFURLED_CLEANUP_TRACKING = 60 * 60 * 24  # How long to track messages to cleanup unfurls (1 day)

# Threshold of community reactions for the bot to delete an unfurl
DELETE_EMOJI_COUNT_TO_DELETE = 4

class EmbedGenerator:

    redis_client = redis.StrictRedis(host='localhost', charset="utf-8", decode_responses=True)

    def __init__(self, bot, recent_trigger_timeout: int = RECENTLY_UNFURLED_TIMEOUT, blacklist: [int] = None):
        """
        Base class for all EmbedGenerators

        This class provides the `run()` which is called along with a discord.Message object
        to produce embeds. This class also defines several method signatures for its subclasses
        to specify how Message objects should be parsed and Embeds be generated from that data.

        Additionally, it defines static methods for managing recent triggers and unfurls

        :param recent_trigger_timeout: The number of seconds after a specific trigger is
            detected that it should still be ignored as "recently seen". Defaults to 2 hours
        :param blacklist: A list of guild or channel IDs from which any Messages should be
            ignored by this Generator. Defaults to an empty list
        """
        self.bot = bot
        self.recent_trigger_timeout = recent_trigger_timeout
        self.blacklist = [] if blacklist is None else blacklist

        # Set class-specific prefix for this generator
        self.recent_prefix = f"{BASE_PREFIX}{self.__class__.__name__}-"     # Recently seen triggers
        self.data_prefix = f"{BASE_PREFIX}DATA-"                                   # Any non-volatile data

    async def parse(self, msg: Message) -> [str]:
        """
        Generates a list of triggers which should be unfurled. This must be defined by each
        subclass based on the information it is looking for

        :param msg: The discord.Message object this Generator is extracting data from
        :return: The list of triggers
        """
        raise NotImplementedError

    async def unfurl(self, trigger: str) -> Optional[Embed]:
        """
        Generates an embed for a given trigger
        :param trigger: The trigger to unfurl
        :return:
        """
        raise NotImplementedError

    async def _recently_seen(self, trigger: str) -> bool:
        """
        Checks if trigger was recently seen by this Generator. If not, it is recorded

        :param trigger: The trigger to check for
        :return: `True` if the trigger is still considered recently seen, `False` otherwise
        """
        key = f"{self.recent_prefix}{trigger}"
        if EmbedGenerator.redis_client.exists(key):
            return True
        # If key is not present, set and return `False`
        EmbedGenerator.redis_client.set(key, "", self.recent_trigger_timeout)
        return False

    async def run(self, msg: Message):
        """
        Parses a Message for certain text patterns that can be unfurled into embeds. These
        embeds are then generated and posted as replies to the original message. If the message
        was sent in a guild or channel whose ID is in this Generator's blacklist, nothing
        will happen.

        :param msg: The discord.Message object this Generator is extracting data from
        """
        try:
            # Ignore if message location blacklisted
            if msg.channel.id in self.blacklist or msg.guild.id in self.blacklist:
                return

            # Parse triggers from message, then unfurl
            unfurl_messages = []
            try:
                triggers = await self.parse(msg)
            except Exception as e:
                await utils.report(str(e), f"parse() in `{self.__class__.__name__}`", msg)
                return
            for trigger in triggers:
                if self._recently_seen(trigger):  # Ignore triggers that were already seen recently
                    continue
                try:
                    embed = self.unfurl(trigger)
                    if embed:
                        unfurl = await msg.reply(embed=embed)
                        await unfurl.add_reaction(DELETE_EMOJI)
                        unfurl_messages.append(unfurl)
                        # Record unfurled message triggering author as unfurl_message_id: author_id
                        unfurl_message_key = f"{UNFURL_PREFIX}{unfurl.id}"
                        EmbedGenerator.redis_client.set(unfurl_message_key,
                                                        msg.author.id,
                                                        UNFURLED_CLEANUP_TRACKING)
                except Exception as e:
                    await utils.report(str(e), f"unfurl() for EmbedGenerator {self.__class__.__name__} "
                                               f"for trigger {trigger}", msg)
                    return

            # If no triggers were unfurled, the message's cleanup entry doesn't need to be updated
            if len(unfurl_messages) == 0:
                return

            # Record unfurled message triggering message as trigger_message_id: [unfurl_message_id, ...]
            trig_message_key = f"{TRIGGER_PREFIX}{msg.id}"
            # Check if message has other associated unfurls, and if so, append them to the new list
            trig_message_value = EmbedGenerator.redis_client.get(trig_message_key)
            if trig_message_value:
                unfurl_messages += json.loads(trig_message_value)
            EmbedGenerator.redis_client.set(trig_message_key,
                                            json.dumps(unfurl_messages),
                                            UNFURLED_CLEANUP_TRACKING)
        except Exception as e:
            await utils.report(str(e), f"run() in `{self.__class__.__name__}`", msg)

    async def store_data(self, key: str, data):
        """
        Stores data in the redis DB under a given key. Data will be dumped to JSON first
        Unlike unfurl keys, this will not expire over time

        :param key: The key to store the data under
        :param data: The data to store
        """
        data_key = f"{self.data_prefix}{key}"
        EmbedGenerator.redis_client.set(data_key, json.dumps(data))

    async def load_data(self, key: str):
        """
        Loads data from the redis DB stored under a given key.
        Data will be loaded from JSON first

        :param key: The key the data was stored under. If key could not be found, returns `None`
        """
        data_key = f"{self.data_prefix}{key}"
        data = EmbedGenerator.redis_client.get(data_key)
        return data if data is None else json.loads(data)

    @classmethod
    async def process_trigger_reaction(cls, msg: Message):
        """
        When another user's message is deleted, this method checks if that message was a trigger
        for any unfurls. If it was, the unfurl is deleted as well
        :param msg: The message that was deleted
        """


    @classmethod
    async def process_delete_reaction(cls, reaction: Reaction, user: User):
        """
        Handles a user reacting to a message with the red 'X' emoji. If this message is an
        unfurl, it will be deleted if any of the following is true:
            - the user has permission to delete messages
            - the user is the author of the message which triggered the unfurl
            - the unfurl has 5 'X' user reactions (6 total)

        :param reaction: The Reaction
        :param user: The User leaving the reaction
        """
        try:
            # Get trigger author id
            unfurl_message_key = f"{UNFURL_PREFIX}{reaction.message.id}"
            trigger_author_id = EmbedGenerator.redis_client.get(unfurl_message_key)
            if trigger_author_id:   # Make sure ID is the right type
                trigger_author_id = int(trigger_author_id)

            # Check if user has permission to delete this message, and if so, try to delete it
            if trigger_author_id == user.id or \
                    user.permissions_in(reaction.message.channel).manage_messages or \
                    reaction.count >= DELETE_EMOJI_COUNT_TO_DELETE:
                try:
                    await reaction.message.delete()
                except NotFound:
                    pass
        except Exception as e:
            await utils.report(str(e), source="on_reaction_add")
