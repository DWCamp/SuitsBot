import re

from discord import Message, Embed

from embedGenerator import BaseGenerator
from constants import *
import utils


class SubredditGenerator(BaseGenerator):
    """
        EmbedGenerator for detecting the names of Subreddits
    """

    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        subreddit = re.compile(r'(?:^|\s)/?r/(\w+)(?:|$)')
        triggers = re.findall(pattern=subreddit, string=msg.content)
        return [trig.lower() for trig in triggers]  # Subreddits are case-insensitive

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:
        embed_color = EMBED_COLORS["reddit"]
        nsfw_thumbnail = "https://cdn2.iconfinder.com/data/icons/freecns-cumulus/32/519791-101_Warning-512.png"
        default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"
        quar_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/946283776550522890/" \
                         "transparantWarning.png"
        embed_icon = "https://s18955.pcdn.co/wp-content/uploads/2017/05/Reddit.png"

        # Reply with all relevant embeds and return the message objects of the replies
        embed_list = []
        for trigger in triggers:
            print(f"{cls.__name__}: unfurling '{trigger}'...")
            sub_name = trigger.strip()

            muted_subreddits = ["animemes", "pussypassdenied", "all", "watchpeopledie", "makemesuffer"]
            if sub_name in muted_subreddits:
                continue

            [json, response] = await utils.get_json_with_get("https://www.reddit.com/r/" + sub_name + "/about.json")
            if response is not 200:
                continue
            data = json["data"]
            if "children" in data:  # If the sub does not exist
                continue

            embed = Embed()
            embed.colour = embed_color
            embed.title = "r/" + data["display_name"]
            embed.set_footer(text="via Reddit.com", icon_url=embed_icon)
            embed.url = "https://www.reddit.com" + data["url"]

            embed.add_field(name="Subscribers", value=data["subscribers"])
            embed.add_field(name="Created", value=f"<t:{int(data['created'])}:D>")

            # Return censored embed if community is NSFW or Quarantined
            if data["over18"]:
                embed.description = "This subreddit is listed as NSFW"
                embed.set_thumbnail(url=nsfw_thumbnail)
            elif data["quarantine"]:
                embed.set_thumbnail(url=quar_thumbnail)
                embed.description = "This subreddit has been quarantined"
            else:
                # Add community icons
                if "icon_img" in data and data["icon_img"]:
                    embed.set_thumbnail(url=data["icon_img"])
                elif "banner_img" in data and data["banner_img"]:
                    embed.set_thumbnail(url=data["banner_img"])
                else:
                    embed.set_thumbnail(url=default_thumbnail)
                embed.description = data["public_description"]
            embed_list.append(embed)
        return embed_list
