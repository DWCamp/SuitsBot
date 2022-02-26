import re
from typing import Optional

from discord import Message, Embed

from embedGenerator import BaseGenerator
from config.credentials import tokens
from constants import *
import utils


class TwitterReplyGenerator(BaseGenerator):
    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        return re.findall(r'\b(?:https://twitter\.com/\w{1,15}/status/)(\d{19})\b', msg.content)

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:
        original_ids = []
        embed_list = []
        for trigger in triggers:
            # Fetch info on the tweet
            twitter_api_url = "https://api.twitter.com/1.1/statuses/show.json"
            parameters = {"id": str(trigger),
                          "tweet_mode": "extended",
                          "include_entities": "true"}
            headers = {"Authorization": "Bearer " + tokens["TWITTER_BEARER"]}
            [payload, response] = await utils.get_json_with_get(twitter_api_url, headers=headers, params=parameters)
            # Ignore if failed to load tweet or tweet was not a reply
            if response is not 200 or (payload['in_reply_to_status_id_str'] is None and not payload['is_quote_status']):
                continue

            # Get response tweet ID
            if payload['is_quote_status']:
                original_id = payload['quoted_status_id']
            else:
                original_id = payload["in_reply_to_status_id_str"]
            # If this is the same tweet an earlier trigger in the list, ignore
            if original_id in original_ids:
                continue
            original_ids.append(original_id)

            # Get info about original tweet
            parameters["id"] = str(original_id)
            [original_json, response] = await utils.get_json_with_get(twitter_api_url, headers=headers,
                                                                      params=parameters)
            if response is not 200:
                continue

            # Ignore if tweet had been recently posted
            short_url = original_json["full_text"].split(" ")[-1]
            full_url = f"https://twitter.com/{original_json['user']['screen_name']}/status/{original_id}"
            prev_mentioned = False
            async for message in msg.channel.history(limit=30):
                if short_url in message.content or full_url in message.content:
                    prev_mentioned = True
                    break
            if prev_mentioned:
                print("reply was recently posted")
                continue

            # ==== Generate Embed

            # Header
            embed = Embed()
            embed.colour = EMBED_COLORS["twitter"]
            embed.title = "This tweet was in response to..."
            embed.set_thumbnail(url=original_json["user"]["profile_image_url_https"])
            embed.url = f"https://twitter.com/{original_json['user']['screen_name']}/status/{str(original_json['id'])}"

            # Text
            user = "**" + original_json["user"]["name"] + "**  (@" + original_json["user"]["name"] + ")"
            embed.description = user + "\n\n" + original_json["full_text"].replace("&amp;", "&")

            # Fields
            embed.add_field(name="Retweets", value=str(original_json["retweet_count"]))
            embed.add_field(name="Likes", value=str(original_json["favorite_count"]))

            # Image
            if 'extended_entities' in original_json:
                # Restrict entities to only photos
                photos = [entity for entity in original_json['extended_entities']['media'] if
                          entity["type"] == "photo"]
                print(photos)
                if photos:  # If there are photos in the media list, embed the first image
                    embed = embed.set_image(url=photos[0]["media_url_https"])

            # Footer
            embed.set_footer(icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png", text="Twitter")
            embed_list.append(embed)
        return embed_list

    @classmethod
    def get_original_url(cls, reply_id) -> Optional[str]:
        pass
