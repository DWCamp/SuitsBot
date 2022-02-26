import re

from discord import Message, Embed

from embedGenerator import BaseGenerator
from constants import *
import utils


class RedditCommentGenerator(BaseGenerator):
    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        return re.findall(r'reddit\.com/r/\w+/comments/\w{6}/[\w%]+/\w{7}/?', msg.content)

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:
        embed_list = []

        embedcolor = EMBED_COLORS["reddit"]
        default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"
        embed_icon = "https://s18955.pcdn.co/wp-content/uploads/2017/05/Reddit.png"

        for trigger in triggers:
            comment_url = "https://" + trigger
            # Get data about comment
            if comment_url[-1] == "/":  # Strip trailing forward slash
                json_url = comment_url[:-1] + ".json"
            else:
                json_url = comment_url + ".json"
            [json, response] = await utils.get_json_with_get(json_url)
            if response is not 200:
                return []
            link_data = json[0]['data']['children'][0]['data']
            comment_data = json[1]['data']['children'][0]['data']

            embed = Embed()
            embed.colour = embedcolor
            embed.url = comment_url
            embed.title = utils.trim_to_len(link_data['title'], 256)
            embed.set_footer(text="via Reddit.com", icon_url=embed_icon)
            embed.description = utils.trim_to_len(comment_data['body'], 2048)

            if link_data["thumbnail"] is not None and link_data["thumbnail"] != "self":
                embed.set_thumbnail(url=link_data["thumbnail"])
            else:
                embed.set_thumbnail(url=default_thumbnail)

            embed.add_field(name="Author", value=comment_data['author'])
            embed.add_field(name="Score", value=comment_data['score'])
            embed.add_field(name="Posted", value=utils.time_from_unix_ts(comment_data['created_utc']))

            # Guildings
            gildings = list()
            if 'gid_3' in comment_data['gildings'].keys():
                gildings.append("Platinum x" + str(comment_data['gildings']['gid_3']))
            if 'gid_2' in comment_data['gildings'].keys():
                gildings.append("Gold x" + str(comment_data['gildings']['gid_2']))
            if 'gid_1' in comment_data['gildings'].keys():
                gildings.append("Silver x" + str(comment_data['gildings']['gid_1']))

            if gildings:
                embed.add_field(name="Gildings", value=", ".join(gildings))

            embed_list.append(embed)
        return embed_list
