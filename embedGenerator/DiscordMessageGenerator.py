import re

from discord import Embed, Member, Message

from embedGenerator import BaseGenerator
from constants import *
import utils


class DiscordMessageGenerator(BaseGenerator):
    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        links = re.findall(r'discord(app)?.com/channels/(\d{18}/\d{18}/\d{18})', msg.content)
        return [group[1] for group in links]

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> [Embed]:
        discord_logo = "https://cdn3.iconfinder.com/data/icons/logos-and-brands-adobe/512/91_Discord-512.png"

        embed_list = []
        for trigger in triggers:
            (guild_id, channel_id, message_id) = trigger.split("/")

            # Cast id values to int
            guild_id = int(guild_id)
            channel_id = int(channel_id)
            message_id = int(message_id)

            # Find message
            bot = utils.get_bot()
            message_channel = bot.get_channel(channel_id)
            if message_channel is None:
                return
            linked_message = await message_channel.fetch_message(message_id)
            if linked_message is None:
                return

            """ Make the Embed """
            embed = Embed()
            embed.url = f"http://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            embed.colour = EMBED_COLORS['discord']

            # Count embeds/attachments
            if len(linked_message.embeds) > 0:
                embed.add_field(name="Embeds", value=f"{len(linked_message.embeds)}", inline=True)
            if len(linked_message.attachments) > 0:
                embed.add_field(name="Attachments", value=f"{len(linked_message.attachments)}", inline=True)

            # Set image from attachments or embeds
            for attach in linked_message.attachments:
                if attach.height:  # Non-null height attribute indicates attachment is an image
                    embed.set_image(url=attach.url)
                    break
            else:
                # If the attachments didn't work, try embeds
                for message_embed in linked_message.embeds:
                    if message_embed.type == "image":
                        embed.set_image(url=message_embed.url)
                        break

            # Set message text
            text = utils.trim_to_len(linked_message.content, 2048)
            if len(text) == 0:  # If message empty, check embeds
                if len(linked_message.embeds) > 0:
                    embed_as_text = utils.embed_to_str(linked_message.embeds[0])
                    text = utils.trim_to_len(f"**Message contained embed**\n```\n{embed_as_text}\n```", 2048)
                elif embed.image.url is Embed.Empty:  # Description doesn't need to be modified if an image is attached
                    text = "```(Message was empty)```"

            embed.description = text

            # Try and use author's nickname if author is a Member object
            if isinstance(linked_message.author, Member):
                embed.title = linked_message.author.name \
                    if linked_message.author.nick is None \
                    else linked_message.author.nick
            else:
                embed.title = linked_message.author.name

            if linked_message.author.avatar_url:
                embed.set_thumbnail(url=linked_message.author.avatar_url)

            # Collapse Reactions to a single list
            if linked_message.reactions:
                react_str = " ‍ ‍ ".join(
                    [f"{reaction.emoji} **{reaction.count}**" for reaction in linked_message.reactions])
                embed.add_field(name="Reactions", value=utils.trim_to_len(react_str, 1024))

            # Add timestamp to footer
            if linked_message.edited_at:
                timestamp = linked_message.edited_at
                verb = "Edited"
            else:
                timestamp = linked_message.created_at
                verb = "Sent"
            embed.set_footer(text=f"{verb} at {timestamp.strftime('%H:%M  %Y-%m-%d')}",
                             icon_url=discord_logo)
            embed_list.append(embed)
        return embed_list
