import json
from discord import Embed, Message, Reaction, User
from discord.errors import NotFound
import redis

from config import *
from constants import *
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

# Create redis client
REDIS_CLIENT = redis.StrictRedis(host='localhost', charset="utf-8", decode_responses=True)

# Records the most recent report to prevent spamming #alert-messages
PREVIOUS_REPORT = None


class BaseGenerator:
    """
        Base class for all EmbedGenerators

        This class provides the `run()` which is called along with a discord.Message object
        to produce embeds. This class also defines several method signatures for its subclasses
        to specify how Message objects should be parsed and Embeds be generated from that data.

        Additionally, it defines static methods for managing recent triggers and unfurls
    """

    # Channel/Server ID Blacklist
    SERVER_BLACKLIST = []
    CHANNEL_BLACKLIST = []

    # Server/Channel ID Whitelist
    # NOTE: If there is a server whitelist and channel blacklist (or vice versa), the channel list takes priority
    SERVER_WHITELIST = []
    CHANNEL_WHITELIST = []

    # Whether to filter triggers that were recently seen. Can be changed by subclasses
    GENERATOR_ALLOWS_REPEATS = False

    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        """
        Extracts the list of relevant phrases from the contents of a message.
        This must be defined by each subclass based on the information it is looking for
        This method only needs to extract relevant strings. `run()` will handle ignoring
        recent triggers and removing duplicates

        :param msg: The discord.Message object this Generator is extracting data from
        :return: The list of triggers
        """
        raise NotImplementedError

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:
        """
        Generates a list of responses, either Embeds or URL strings, for a given list of triggers
        Not all trigger phrases need to produce responses

        :param triggers: The list of trigger phrases
        :param msg: A copy of the original message object
        :return: The list of relevant responses
        """
        raise NotImplementedError

    @classmethod
    async def recently_seen(cls, trigger: str, channel_id: int) -> bool:
        """
        Checks if trigger was recently seen by this Generator in the same channel. If not, it is recorded

        :param trigger: The trigger to check for
        :param channel_id: The ID of the channel the message was seen in
        :return: `True` if the trigger is still considered recently seen, `False` otherwise
        """
        key = f"{cls._get_recent_prefix()}{channel_id}-{trigger}"
        if REDIS_CLIENT.exists(key):
            return True
        # If key is not present, set and return `False`
        REDIS_CLIENT.set(key, "", RECENTLY_UNFURLED_TIMEOUT)
        return False

    @classmethod
    def _get_recent_prefix(cls):
        """ Gets this class' the redis key prefix for recently seen trigger entries """
        return f"{BASE_PREFIX}{cls.__name__}-RECENT-"

    @classmethod
    def _get_data_prefix(cls):
        """ Gets this class' the redis key prefix for generic data entries """
        return f"{BASE_PREFIX}{cls.__name__}-DATA-"

    @classmethod
    def _source_blocked(cls, msg):
        """
        Checks if the source of the message is blocked, meaning either:
            - The channel is blacklisted
            - The channel isn't on the whitelist
            - The server is blacklisted and the channel isn't whitelisted
            - The server isn't on the whitelist

        :param msg: The message to check
        :return: Returns `True` if the message is from a disabled source
        """
        # Throw an error if there's a blacklist AND whitelist for either source
        if cls.SERVER_BLACKLIST and cls.SERVER_WHITELIST:
            raise ValueError(f"{cls.__name__} has both a server whitelist and blacklist, which is not allowed")
        elif cls.CHANNEL_BLACKLIST and cls.CHANNEL_WHITELIST:
            raise ValueError(f"{cls.__name__} has both a channel whitelist and blacklist, which is not allowed")

        # If there isn't a blacklist or whitelist, message is automatically allowed
        if not cls.SERVER_BLACKLIST and not cls.SERVER_WHITELIST and \
                not cls.CHANNEL_BLACKLIST and not cls.CHANNEL_WHITELIST:
            return False

        # The channel is not whitelisted
        if msg.channel.id not in cls.CHANNEL_WHITELIST:
            return True
        # The channel is blacklisted
        if msg.channel.id in cls.CHANNEL_BLACKLIST:
            return True
        # The is server not whitelisted
        if msg.guild.id not in cls.SERVER_WHITELIST:
            return True
        # The is server not blacklisted
        if msg.guild.id in cls.SERVER_BLACKLIST:
            return True

        # If no disable condition is met, return message is allowed
        return False

    @classmethod
    async def run(cls, msg: Message):
        """
        Parses a Message for certain text patterns that can be unfurled into embeds. These
        embeds are then generated and posted as replies to the original message. If the message
        was sent in a guild or channel whose ID is in this Generator's blacklist, nothing
        will happen.

        :param msg: The discord.Message object this Generator is extracting data from
        """
        try:
            # Ignore if message location blacklisted or not whitelisted
            if cls._source_blocked(msg):
                return

            # Parse triggers from message
            try:
                triggers = await cls.extract(msg)
            except Exception as e:
                await utils.report(str(e), f"{cls.__name__} failed to parse message", msg)
                return

            # Deduplicate
            triggers = {trig for trig in triggers}

            # Ignore recent triggers if enabled
            if RECENT_EMBED_TRIGGER_FILTER_ENABLED and cls.GENERATOR_ALLOWS_REPEATS:
                c_id = msg.channel.id
                triggers = [t for t in triggers if not await cls.recently_seen(t, c_id)]
            else:
                triggers = list(triggers)

            # Unfurl triggers
            try:
                embed_list = await cls.unfurl(triggers, msg)
            except Exception as e:
                await utils.report(str(e), f"{cls.__name__} failed to unfurl message", msg)
                return

            # Post embeds
            unfurl_ids = []
            for reply in embed_list:
                try:
                    if isinstance(reply, Embed):
                        unfurl = await msg.reply(embed=reply)
                    else:
                        unfurl = await msg.reply(str(reply))
                    await unfurl.add_reaction(DELETE_EMOJI)
                    await unfurl.add_reaction(REPORT_EMOJI)
                    await unfurl.add_reaction(HEART_EMOJI)
                    unfurl_ids.append(unfurl.id)
                    # Record unfurled message triggering author as unfurl_message_id: author_id
                    unfurl_message_key = f"{UNFURL_PREFIX}{unfurl.id}"
                    REDIS_CLIENT.set(unfurl_message_key, msg.author.id, UNFURLED_CLEANUP_TRACKING)
                except Exception as e:
                    await utils.report(str(e), f"{cls.__name__} failed to reply with embed for message", msg)
                    return

            # If no triggers were unfurled, the message's cleanup entry doesn't need to be updated
            if len(unfurl_ids) == 0:
                return

            # Record unfurled message triggering message as trigger_message_id: [unfurl_message_id, ...]
            trig_message_key = f"{TRIGGER_PREFIX}{msg.id}"
            # Check if message has other associated unfurls, and if so, append them to the new list
            trig_message_value = REDIS_CLIENT.get(trig_message_key)
            if trig_message_value:
                unfurl_ids += json.loads(trig_message_value)
            REDIS_CLIENT.set(trig_message_key, json.dumps(unfurl_ids), UNFURLED_CLEANUP_TRACKING)
        except Exception as e:
            await utils.report(str(e), f"run() in `{cls.__name__}`", msg)

    @classmethod
    async def store_data(cls, key: str, data, expiration: int = None):
        """
        Stores data in the redis DB under a given key. Data will be dumped to JSON first

        :param key: The key to store the data under
        :param data: The data to store
        :param expiration: How many seconds the data should be stored for before expiring.
            Defaults to `None`, which means it will never expire
        """
        data_key = f"{cls._get_data_prefix()}{key}"
        REDIS_CLIENT.set(data_key, json.dumps(data), ex=expiration)

    @classmethod
    async def load_data(cls, key: str):
        """
        Loads data from the redis DB stored under a given key.
        Data will be loaded from JSON first

        :param key: The key the data was stored under. If key could not be found, returns `None`
        """
        data_key = f"{cls._get_data_prefix()}{key}"
        data = REDIS_CLIENT.get(data_key)
        return data if data is None else json.loads(data)


async def process_trigger_delete(msg: Message):
    """
    When another user's message is deleted, this method checks if that message was a trigger
    for any unfurls. If it was, the unfurl is deleted as well
    :param msg: The message that was deleted
    """
    trigger_key = f"{TRIGGER_PREFIX}{msg.id}"
    unfurl_messages = REDIS_CLIENT.get(trigger_key)
    if unfurl_messages is None:
        return
    unfurl_messages = json.loads(unfurl_messages)   # Convert to list
    for unfurl in unfurl_messages:
        try:
            unfurl_message = await utils.get_message(msg.channel.id, int(unfurl))
            await unfurl_message.delete()
            await utils.flag(alert="Unfurl deleted",
                             description=f"User `{msg.author.name}` deleted an unfurl in guild `{msg.guild.name}` "
                                         f"on channel `#{msg.channel.name}` at `{msg.created_at}`",
                             message=msg)
        except NotFound:
            pass    # Unfurl was probably already deleted
        except Exception as e:
            await utils.flag(alert="Failed to deleted unfurl",
                             description=f"When the specified message was deleted, the unfurl `{unfurl}` "
                                         f"failed to delete with the following error:\n```{str(e)}```",
                             message=msg)


async def process_delete_reaction(reaction: Reaction, user: User):
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
        # Only attempt to delete the bot's own messages
        if reaction.message.author.id != BOT_USER_ID:
            return

        # Get trigger author id
        unfurl_message_key = f"{UNFURL_PREFIX}{reaction.message.id}"
        trigger_author_id = REDIS_CLIENT.get(unfurl_message_key)
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
        await utils.report(str(e), source="process_delete_reaction", ctx=reaction.message)


async def process_report_reaction(reaction: Reaction, user: User):
    """
    Handles a user reacting to a message with the 'loudspeaker' emoji. If this message is an
    unfurl, the bot will post a dev alert about the report

    :param reaction: The Reaction
    :param user: The User leaving the reaction
    """
    global PREVIOUS_REPORT
    try:
        # Check if it's one of the bot's messages
        msg = reaction.message
        if msg.author.id != BOT_USER_ID:
            return

        # Ignore if there wasn't already a report reaction on it
        # This would mean it's either an embed or multiple people manually reported it
        if reaction.count < 2:
            return

        # Ignore if this reaction has been seen already
        reaction_record = msg.id + user.id  # *Technically* this could collide, but it's fast and the chances are low
        if reaction_record == PREVIOUS_REPORT:
            return
        else:
            PREVIOUS_REPORT = reaction_record

        # Flag reaction
        await utils.flag("Message Reported", f"User '{user.name}' reported a message", message=msg)

    except Exception as e:
        await utils.report(str(e), source="process_report_reaction")


async def process_heart_reaction(reaction: Reaction, user: User):
    """
    Handles a user reacting to a message with the 'heart' emoji.
    Notifies the bot owner that SuitsBot has been given some love

    :param reaction: The Reaction
    :param user: The User leaving the reaction
    """
    try:
        # Only process reactions on the bot's own messages
        if reaction.message.author.id != BOT_USER_ID:
            return
        await utils.flag("A user has given SuitsBot a heart", ctx=reaction.message)
    except Exception as e:
        await utils.report(str(e), source="process_heart_reaction", ctx=reaction.message)
