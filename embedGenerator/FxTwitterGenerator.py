import re

from discord import Message

from embedGenerator import BaseGenerator
from config.credentials import tokens
import utils


class FxTwitterGenerator(BaseGenerator):

    @classmethod
    async def extract(cls, msg: Message) -> [str]:
        # By extracting all twitter links without checking them, you avoid having to invoke the API on duplicates
        return re.findall(r'\b(?:https://twitter\.com/\w{1,15}/status/)(\d{19})\b', msg.content)

    @classmethod
    async def unfurl(cls, triggers: [str], msg: Message) -> list:
        url_list = []
        for trigger in triggers:
            # Fetch info on the tweet
            twitter_api_url = "https://api.twitter.com/1.1/statuses/show.json"
            parameters = {"id": str(trigger),
                          "tweet_mode": "extended",
                          "include_entities": "true"}
            headers = {"Authorization": "Bearer " + tokens["TWITTER_BEARER"]}
            [payload, response] = await utils.get_json_with_get(twitter_api_url, headers=headers, params=parameters)
            # Ignore if failed to load tweet
            if response is not 200:
                continue

            # Ignore if it doesn't have "extended entities" (i.e. complex media)
            if "extended_entities" not in payload or "media" not in payload["extended_entities"]:
                continue

            # Find media of type "video"
            video_url = None
            for media in payload["extended_entities"]["media"]:
                if media["type"] == "video":
                    video_url = f"https://fxtwitter.com/{payload['user']['screen_name']}/status/{trigger}"
                    break
            if video_url:
                url_list.append(video_url)

        return url_list
