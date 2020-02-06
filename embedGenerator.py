import json
from datetime import datetime
from typing import List, Callable, Optional, Union
from bs4 import BeautifulSoup
from discord import Embed, Message
from constants import EMBED_COLORS
import credentials
import utils
import redis

redis_db = redis.StrictRedis(host='localhost', charset="utf-8", decode_responses=True)
REDIS_PREFIX = "suitsBot-"
RECENTLY_UNFURLED_TIMEOUT_SECONDS = 300                 # How long to wait before unfurling the same thing again
UNFURLED_CLEANUP_TRACKING_IN_SECONDS = 60 * 60 * 24     # How long to track messages to cleanup unfurls


async def recently_unfurled(key: str) -> bool:
    """Check if key exists, if not set it."""
    key_to_check = f"{REDIS_PREFIX}{key}"
    if redis_db.exists(key_to_check):
        return True
    else:
        redis_db.set(key_to_check, "", RECENTLY_UNFURLED_TIMEOUT_SECONDS)
        return False


async def embeds_from_regex(matchlist: List[str],
                            embed_method: Callable[[str], Union[List[Embed], Embed, None]],
                            message: Message) -> List[Embed]:
    """
    Returns a list of embeds generated from a list of strings and
    a method used to convert those strings into embeds
    :param matchlist: The list of strings to convert
    :param embed_method: A method which takes a string (normally a url or id)
    and converts it into an embed or list of embeds
    :param message: The message triggering this embed response
    :return: A list of embeds
    """
    embed_list = list()
    for match in matchlist:
        link = match.strip()
        if await recently_unfurled(f"{message.channel.id}-{embed_method.__name__}-{link}"):
            continue
        embed = await embed_method(link)
        if embed is not None:
            if isinstance(embed, list):
                for item in embed:
                    embed_list.append(item)
            else:
                embed_list.append(embed)
    return embed_list


def get_trig_message_key(message_id: int) -> str:
    return f"{REDIS_PREFIX}trig-message-{message_id}"


async def get_unfurls_for_trigger_message(trigger_message: Message) -> List[str]:
    """Retrieve all messages IDs created from trigger message"""
    trig_message_key = get_trig_message_key(trigger_message.id)
    trig_message_value = redis_db.get(trig_message_key)
    if trig_message_value:
        return json.loads(trig_message_value)
    else:
        return []


async def record_unfurl(trigger_message: Message, unfurl_message: Message) -> None:
    """Record data about unfurled messages"""

    # Record unfurled message triggering message as trigger_message_id: [unfurl_message_id, ...]
    trig_message_key = get_trig_message_key(trigger_message.id)
    unfurl_messages = await get_unfurls_for_trigger_message(trigger_message)
    unfurl_messages.append(unfurl_message.id)
    redis_db.set(trig_message_key, json.dumps(unfurl_messages), UNFURLED_CLEANUP_TRACKING_IN_SECONDS)


async def amazon(url: str) -> Optional[Embed]:
    text = await utils.get_website_text(url)
    if text is None:
        return None
    embed = Embed()
    # Properties
    embed.url = url
    embed.colour = EMBED_COLORS['amazon']
    soup = BeautifulSoup(text, 'html.parser')
    embed.title = soup.find(id='productTitle').text.strip()
    embed.set_thumbnail(url=soup.find(id='landingImage').get('src'))
    # Description
    descdiv = soup.find(id='productDescription')
    if descdiv is not None:
        ptag = descdiv.p
        if ptag is not None:
            embed.description = utils.trimtolength(ptag.text, 2048)
    # Fields
    vendor = soup.find(id='bylineInfo')
    if vendor is not None:
        embed.add_field(name="Vendor", value=vendor.text)

    price = soup.find(id='priceblock_ourprice')
    if price is not None:
        embed.add_field(name="Price", value=price.text)
    else:
        price = soup.find(id='priceblock_dealprice')
        if price is not None:
            embed.add_field(name="Price", value=price.text)

    rating = soup.find(id='acrPopover')
    if rating is not None:
        embed.add_field(name="Rating", value=rating['title'])
    return embed


async def newegg(url: str) -> Optional[Embed]:
    text = await utils.get_website_text(url)
    if text is None:
        return None
    embed = Embed()
    # Properties
    embed.url = url
    embed.colour = EMBED_COLORS['newegg']
    soup = BeautifulSoup(text, 'html.parser')
    embed.title = soup.find(id='grpDescrip_h').span.text.strip()
    image_url = "http:" + soup.find(id="A2").span.img["src"]
    embed.set_thumbnail(url=image_url)
    # Description
    description = ""
    for bullet in soup.select(".itemColumn")[0].children:
        item = bullet.string.strip()  # filters weird parsing error
        if item:
            description += "**•** " + item + "\n"
    embed.description = utils.trimtolength(description, 2048)
    # Fields
    if soup.select(".itmRating"):
        embed.add_field(name="Rating", value=soup.select(".itmRating")[0].i["title"])
    return embed


async def subreddit(subname: str, allow_nsfw: bool = True) -> Optional[Embed]:
    """
    Gets an embed containing information about a subreddit

    Parameters
    -------------
    subname : str
        The name of the subreddit
    allow_nsfw : True
        Whether to return NSFW results. Defaults to True

    Returns
    -------------
    An embed containing the information of the subreddit
    Will return None if:
    - The subreddit is NSFW and allowNSFW is set to False
    - The subreddit does not exist, is private, or is banned
    - The subreddit is on the MUTTED_SUBREDDITS list
    """
    muted_subreddits = ["animemes", "the_donald", "pussypassdenied", "all"]

    if subname in muted_subreddits:
        return None
    [json, response] = await utils.get_json_with_get("https://www.reddit.com/r/" + subname + "/about.json")
    if response is not 200:
        return None
    data = json["data"]
    if "children" in data:  # If the sub does not exist
        return None

    embedcolor = EMBED_COLORS["reddit"]
    nsfw_thumbnail = "https://cdn2.iconfinder.com/data/icons/freecns-cumulus/32/519791-101_Warning-512.png"
    default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"
    embed_icon = "https://s18955.pcdn.co/wp-content/uploads/2017/05/Reddit.png"

    subembed = Embed()
    subembed.colour = embedcolor
    subembed.title = data["display_name"]
    subembed.set_footer(text="via Reddit.com", icon_url=embed_icon)
    subembed.url = "https://www.reddit.com" + data["url"]

    # Return special embed if community is NSFW
    if data["over18"]:
        if allow_nsfw:
            subembed.description = "This subreddit is listed as NSFW"
            subembed.set_thumbnail(url=nsfw_thumbnail)
            return subembed
        else:
            return None

    if data["community_icon"] is not None:
        subembed.set_thumbnail(url=data["community_icon"])
    elif data["banner_img"] is not None:
        subembed.set_thumbnail(url=data["banner_img"])
    else:
        subembed.set_thumbnail(url=default_thumbnail)

    subembed.description = utils.trimtolength(data["public_description"], 2048)
    subembed.add_field(name="Subscribers", value=format(data["subscribers"], ',d'))
    creation_time = datetime.utcfromtimestamp(data["created_utc"]).strftime('%Y-%m-%d')
    subembed.add_field(name="Subreddit Since", value=creation_time)
    return subembed


async def reddit_post(post_url: str) -> Optional[Embed]:
    """

    Parameters
    -------------
    post_url : str
        The url of the linked post

    Returns
    -------------
    An embed containing the body of the comment and related information
    Will return 'None' if the comment cannot be located
    """
    if post_url[-1] == "/":  # Strip trailing forward slash
        json_url = post_url[:-1] + ".json?raw_json=1"
    else:
        json_url = post_url + ".json"
    [json, response] = await utils.get_json_with_get(json_url)
    if response is not 200:
        return None
    post_data = json[0]['data']['children'][0]['data']

    if not post_data["is_self"]:  # Don't expand link posts
        return None

    embedcolor = EMBED_COLORS["reddit"]
    nsfw_thumbnail = "https://cdn2.iconfinder.com/data/icons/freecns-cumulus/32/519791-101_Warning-512.png"
    default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"
    embed_icon = "https://s18955.pcdn.co/wp-content/uploads/2017/05/Reddit.png"

    post_embed = Embed()
    post_embed.colour = embedcolor
    post_embed.url = post_url
    post_embed.title = utils.trimtolength(post_data['title'], 256)

    post_embed.set_footer(text="via Reddit.com", icon_url=embed_icon)
    post_embed.add_field(name="Author", value=post_data['author'])
    post_embed.add_field(name="Subreddit", value=post_data['subreddit_name_prefixed'])
    if not post_data['hide_score']:
        scoreText = f"{post_data['score']} ({post_data['upvote_ratio'] * 100}%)"
        post_embed.add_field(name="Score", value=scoreText)
    post_embed.add_field(name="Comments", value=post_data['num_comments'])

    # Hide other details if NSFW
    if post_data['over_18']:
        post_embed.description = "This post has been tagged as NSFW"
        post_embed.set_thumbnail(url=nsfw_thumbnail)
        return post_embed
    if post_data['spoiler']:
        post_embed.title = "SPOILER!"
        post_embed.set_thumbnail(url=nsfw_thumbnail)
        return post_embed

    post_embed.add_field(name="Posted", value=utils.timefromunix(post_data['created_utc']))

    text = post_data['selftext'].replace('&#x200B;', '')
    post_embed.description = utils.trimtolength(text, 2048)

    if "preview" in post_data and len(post_data["preview"]["images"]) > 0:
        post_embed.set_thumbnail(url=post_data["preview"]["images"][0]["source"]["url"])
    else:
        post_embed.set_thumbnail(url=default_thumbnail)

    # Guildings
    gildings = list()
    if 'gid_3' in post_data['gildings'].keys():
        gildings.append("Platinum x" + str(post_data['gildings']['gid_3']))
    if 'gid_2' in post_data['gildings'].keys():
        gildings.append("Gold x" + str(post_data['gildings']['gid_2']))
    if 'gid_1' in post_data['gildings'].keys():
        gildings.append("Silver x" + str(post_data['gildings']['gid_1']))

    if gildings:
        post_embed.add_field(name="Gildings", value=", ".join(gildings))

    return post_embed


async def reddit_comment(comment_url: str) -> Optional[Embed]:
    """

    Parameters
    -------------
    comment_url : str
        The url of the permalink comment

    Returns
    -------------
    An embed containing the body of the comment and related information
    Will return 'None' if the comment cannot be located
    """
    if comment_url[-1] == "/":  # Strip trailing forward slash
        json_url = comment_url[:-1] + ".json"
    else:
        json_url = comment_url + ".json"
    [json, response] = await utils.get_json_with_get(json_url)
    if response is not 200:
        return None
    link_data = json[0]['data']['children'][0]['data']
    comment_data = json[1]['data']['children'][0]['data']

    embedcolor = EMBED_COLORS["reddit"]
    default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"
    embed_icon = "https://s18955.pcdn.co/wp-content/uploads/2017/05/Reddit.png"

    comment_embed = Embed()
    comment_embed.colour = embedcolor
    comment_embed.url = comment_url
    comment_embed.title = utils.trimtolength(link_data['title'], 256)
    comment_embed.set_footer(text="via Reddit.com", icon_url=embed_icon)
    comment_embed.description = utils.trimtolength(comment_data['body'], 2048)

    if link_data["thumbnail"] is not None and link_data["thumbnail"] != "self":
        comment_embed.set_thumbnail(url=link_data["thumbnail"])
    else:
        comment_embed.set_thumbnail(url=default_thumbnail)

    comment_embed.add_field(name="Author", value=comment_data['author'])
    comment_embed.add_field(name="Score", value=comment_data['score'])
    comment_embed.add_field(name="Posted", value=utils.timefromunix(comment_data['created_utc']))

    # Guildings
    gildings = list()
    if 'gid_3' in comment_data['gildings'].keys():
        gildings.append("Platinum x" + str(comment_data['gildings']['gid_3']))
    if 'gid_2' in comment_data['gildings'].keys():
        gildings.append("Gold x" + str(comment_data['gildings']['gid_2']))
    if 'gid_1' in comment_data['gildings'].keys():
        gildings.append("Silver x" + str(comment_data['gildings']['gid_1']))

    if gildings:
        comment_embed.add_field(name="Gildings", value=", ".join(gildings))

    return comment_embed


async def twitter_handle(handle: str) -> Optional[Embed]:
    """

    Parameters
    -------------
    handle : str
        The twitter handle, with no @-sign or whitespace

    Returns
    -------------
    An embed containing the link to the twitter account and related information
    Will return 'None' if the account does not exist
    """
    twitter_api_url = "https://api.twitter.com/1.1/users/show.json?screen_name=" + handle
    headers = {"Authorization": "Bearer " + credentials.tokens["TWITTER_BEARER"]}
    [json, response] = await utils.get_json_with_get(twitter_api_url, headers=headers)
    if response is not 200:
        return None

    # Embed values
    embed_icon = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
    embed_color = EMBED_COLORS["twitter"]

    # Embed properties
    twitter_embed = Embed()
    twitter_embed.colour = embed_color
    twitter_embed.title = json["name"]
    twitter_embed.set_footer(icon_url=embed_icon, text="Twitter")
    twitter_embed.url = "https://twitter.com/" + handle
    twitter_embed.set_thumbnail(url=json["profile_image_url_https"])
    if json["description"]:
        twitter_embed.description = json["description"]

    # Fields
    twitter_embed.add_field(name="Followers", value=str(json["followers_count"]))
    if json["url"]:
        twitter_embed.add_field(name="Website", value=json["url"])

    return twitter_embed


async def twitter_images(image_id):
    """
    Provided the id of a tweet, returns a list of embeds,
    each containing an image from that tweet, excluding the first

    Parameters
    -------------
    image_id : str/int
        The id of the tweet media is being grabbed from

    Returns
    -------------
    A list of embeds containing every image attached to the tweet
    None if no images or tweet does not exist
    """
    twitter_api_url = "https://api.twitter.com/1.1/statuses/show.json"
    parameters = {"id": str(image_id),
                  "tweet_mode": "extended",
                  "include_entities": "true"}
    headers = {"Authorization": "Bearer " + credentials.tokens["TWITTER_BEARER"]}
    [json, response] = await utils.get_json_with_get(twitter_api_url, headers=headers, params=parameters)
    if response is not 200 or "extended_entities" not in json.keys():
        return None

    embed_list = list()

    # Embed values
    embed_icon = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
    embed_color = EMBED_COLORS["twitter"]
    count = 0

    # generate embed list
    for entity in json['extended_entities']['media']:
        count += 1
        image_embed = Embed().set_image(url=entity["media_url_https"])
        image_embed.colour = embed_color
        image_embed.title = "Image " + str(count)
        image_embed.url = entity["url"]
        image_embed.set_footer(icon_url=embed_icon, text="Twitter")
        embed_list.append(image_embed)

    return embed_list[1:] if count else None  # Drop the last since we only care about showing the hidden images


async def twitter_response(tweet_id: Union[str, int]) -> Optional[List[Embed]]:
    """
    Provided the id for a tweet, returns an embed with the
    information of the status that tweet was responding to

    Parameters
    -------------
    tweet_id : str/int
        The id of the tweet

    Returns
    -------------
    A list of embeds containing every image attached to the tweet
    None if tweet was not a response
    """

    # Fetch info on the tweet
    twitter_api_url = "https://api.twitter.com/1.1/statuses/show.json"
    parameters = {"id": str(tweet_id),
                  "tweet_mode": "extended",
                  "include_entities": "true"}
    headers = {"Authorization": "Bearer " + credentials.tokens["TWITTER_BEARER"]}
    [json, response] = await utils.get_json_with_get(twitter_api_url, headers=headers, params=parameters)
    if response is not 200 or (json['in_reply_to_status_id_str'] is None and not json['is_quote_status']):
        return None

    # Fetch info on the tweet it was in response to
    if json['is_quote_status']:
        original_id = json['quoted_status_id']
    else:
        original_id = json["in_reply_to_status_id_str"]
    parameters["id"] = str(original_id)
    [original_json, response] = await utils.get_json_with_get(twitter_api_url, headers=headers, params=parameters)
    if response is not 200:
        return None

    # ==== Generate Embed

    # Header
    original_embed = Embed()
    original_embed.colour = EMBED_COLORS["twitter"]
    original_embed.title = "This tweet was in response to..."
    original_embed.set_thumbnail(url=original_json["user"]["profile_image_url_https"])
    original_embed.url = ("https://twitter.com/" +
                          original_json["user"]["screen_name"] +
                          "/status/" +
                          str(original_json["id"]))

    # Text
    user = "**" + original_json["user"]["name"] + "**  (@" + original_json["user"]["name"] + ")"
    original_embed.description = user + "\n\n" + original_json["full_text"].replace("&amp;", "&")

    # Fields
    original_embed.add_field(name="Retweets", value=str(original_json["retweet_count"]))
    original_embed.add_field(name="Likes", value=str(original_json["favorite_count"]))

    # Image
    # (Not implemented)

    # Footer
    original_embed.set_footer(icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png", text="Twitter")

    return [original_embed]  # Embeds must be returned as a list
