import re

from discord import Message, Embed

from embedGenerator import BaseGenerator
from constants import *
import utils


class RedditSelfPostGenerator(BaseGenerator):
    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        return re.findall(r'reddit.com/r/\w{1,20}/comments/\w{5,6}/\w+/?', msg.content)

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:

        embed_color = EMBED_COLORS["reddit"]
        nsfw_thumbnail = "https://cdn2.iconfinder.com/data/icons/freecns-cumulus/32/519791-101_Warning-512.png"
        default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"
        embed_icon = "https://s18955.pcdn.co/wp-content/uploads/2017/05/Reddit.png"

        embed_list = []
        for trigger in triggers:
            post_url = "https://" + trigger

            print(f"post_url: '{post_url}'")
            # Get data from post
            if post_url[-1] == "/":  # Strip trailing forward slash
                json_url = post_url[:-1] + ".json?raw_json=1"
            else:
                json_url = post_url + ".json"
            [json, response] = await utils.get_json_with_get(json_url)
            if response is not 200:
                print("not 202")
                continue
            post_data = json[0]['data']['children'][0]['data']

            if not post_data["is_self"]:  # Don't expand link posts
                print("is self")
                continue

            # Embed data

            embed = Embed()
            embed.colour = embed_color
            embed.url = post_url
            embed.title = utils.trim_to_len(post_data['title'], 256)

            embed.set_footer(text="via Reddit.com", icon_url=embed_icon)
            embed.add_field(name="Author", value=post_data['author'])
            embed.add_field(name="Subreddit", value=post_data['subreddit_name_prefixed'])
            if not post_data['hide_score']:
                score_text = f"{post_data['score']} ({post_data['upvote_ratio'] * 100}%)"
                embed.add_field(name="Score", value=score_text)
            embed.add_field(name="Comments", value=post_data['num_comments'])

            # Hide other details if NSFW
            if post_data['over_18']:
                embed.description = "This post has been tagged as NSFW"
                embed.set_thumbnail(url=nsfw_thumbnail)
                embed_list.append(embed)
                continue
            if post_data['spoiler']:
                embed.title = "SPOILER!"
                embed.set_thumbnail(url=nsfw_thumbnail)
                embed_list.append(embed)
                continue

            embed.add_field(name="Posted", value=utils.time_from_unix_ts(post_data['created_utc']))

            text = post_data['selftext'].replace('&#x200B;', '')
            embed.description = utils.trim_to_len(text, 2048)

            if "preview" in post_data and len(post_data["preview"]["images"]) > 0:
                embed.set_thumbnail(url=post_data["preview"]["images"][0]["source"]["url"])
            else:
                embed.set_thumbnail(url=default_thumbnail)

            # Guildings
            gildings = list()
            if 'gid_3' in post_data['gildings'].keys():
                gildings.append("Platinum x" + str(post_data['gildings']['gid_3']))
            if 'gid_2' in post_data['gildings'].keys():
                gildings.append("Gold x" + str(post_data['gildings']['gid_2']))
            if 'gid_1' in post_data['gildings'].keys():
                gildings.append("Silver x" + str(post_data['gildings']['gid_1']))

            if gildings:
                embed.add_field(name="Gildings", value=", ".join(gildings))

            embed_list.append(embed)
        return embed_list
