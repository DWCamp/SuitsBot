import re


from discord import Embed, Message

from embedGenerator import BaseGenerator
from constants import *
import utils
import parse


class DuplicateLinkAlertGenerator(BaseGenerator):

    DUPLICATE_LINK_EXPIRY_SECONDS = 60 * 60 * 24 * 2    # Two days
    GENERATOR_ALLOWS_REPEATS = True  # The whole point is to find OTHER PEOPLE'S repeats

    @classmethod
    def get_link_key(cls, link: str, msg: Message) -> str:
        """ Generates the key for a link seen in a given Message """
        return f"{msg.guild.id}-{link}"

    @classmethod
    async def recently_on_server(cls, link: str, msg: Message) -> bool:
        """
        Checks if a given links was recently seen in a different message on this server
        If it wasn't, the link and guild ID are used as a key to store the channel and
        message ID where they were seen. This data is stored as the string

        `<channel_ID>/<message_ID>/<author_ID>'

        :param link: The link to check in the past 48 hours for
        :param msg: The Message where the link was found
        :return: `True` if the link was recently seen on the server
        """
        link_key = cls.get_link_key(link, msg)
        if await cls.load_data(link_key) is not None:
            return True
        await cls.store_data(link_key,
                             f"{msg.channel.id}/{msg.id}/{msg.author.id}",
                             expiration=cls.DUPLICATE_LINK_EXPIRY_SECONDS)
        return False

    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        links = re.findall(parse.URL_REGEX, msg.content)    # Extract URLs
        links = [group[0] for group in links]   # Get just the full string
        # Return only the links that were already seen on this server recently
        return [link for link in links if await cls.recently_on_server(link, msg)]

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:
        embed_list = []

        alert_icon = "http://icons.iconarchive.com/icons/paomedia/small-n-flat/96/sign-warning-icon.png"

        for trigger in triggers:
            # Get channel id and message id of previous sighting
            link_key = cls.get_link_key(trigger, msg)
            prev_sighting = await cls.load_data(link_key)

            if prev_sighting is None:   # Alert and abort if it didn't find anything
                print(f"Didn't find trigger {trigger} in the DB")
                continue

            channel_id, message_id, prev_author_id = prev_sighting.split("/")

            # If it's the same user, don't say anything
            if int(prev_author_id) == msg.author.id:
                continue

            prev_message = await utils.get_message(int(channel_id), int(message_id))

            # Make sure the bot isn't linking to a different guild
            guild_id = prev_message.guild.id
            assert guild_id == msg.guild.id

            # Make alert embed
            embed = Embed()
            embed.url = f"http://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            embed.colour = EMBED_COLORS["flag"]

            trigger_author_name = utils.get_screen_name(msg.author)
            prev_author_name = prev_message.author
            if prev_message.channel.id == msg.channel.id:
                embed.title = f"Heads up {trigger_author_name}, " \
                              f"I think {prev_author_name} recently posted that link in this channel"
            else:
                embed.title = f"Heads up {trigger_author_name}, " \
                              f"I think {prev_author_name} recently posted that link in #{prev_message.channel.name}"

            embed.add_field(name="Author", value=prev_author_name)
            embed.add_field(name="Sent", value=f"<t:{int(prev_message.created_at.timestamp())}>")

            embed.description = f"```{utils.trim_to_len(prev_message.content, 500)}```"  # Just in case it's really long
            embed.set_footer(text=f"If this was a mistake, click the {REPORT_EMOJI} reaction to report it",
                             icon_url=alert_icon)

            embed_list.append(embed)
        return embed_list
