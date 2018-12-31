from datetime import datetime
from bs4 import BeautifulSoup
from discord import Embed
import utils
from constants import EMBED_COLORS


async def embeds_from_regex(matchlist, embed_method):
    embed_list = list()
    for match in matchlist:
        link = match.strip()
        embed = await embed_method(link)
        if embed is not None:
            embed_list.append(embed)
    return embed_list


async def amazon(url: str):
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


async def newegg(url: str):
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


async def subreddit(subname: str, allow_nsfw=True):
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

    subembed = Embed()
    subembed.colour = embedcolor
    subembed.title = data["display_name"]
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


async def reddit_post(post_url: str):
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
        json_url = post_url[:-1] + ".json"
    else:
        json_url = post_url + ".json"
    [json, response] = await utils.get_json_with_get(json_url)
    if response is not 200:
        return None
    post_data = json[0]['data']['children'][0]['data']

    embedcolor = EMBED_COLORS["reddit"]
    nsfw_thumbnail = "https://cdn2.iconfinder.com/data/icons/freecns-cumulus/32/519791-101_Warning-512.png"
    default_thumbnail = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"

    post_embed = Embed()
    post_embed.colour = embedcolor
    post_embed.url = post_url
    post_embed.title = utils.trimtolength(post_data['title'], 256)
    post_embed.add_field(name="Author", value=post_data['author'])
    post_embed.add_field(name="Subreddit", value=post_data['subreddit_name_prefixed'])
    if not post_data['hide_score']:
        post_embed.add_field(name="Score", value=post_data['score'])
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

    if post_data["is_self"]:
        post_embed.description = utils.trimtolength(post_data['body'], 2048)
    if post_data["thumbnail"] not in ["default", "self", None]:
        post_embed.set_thumbnail(url=post_data["thumbnail"])
    else:
        post_embed.set_thumbnail(url=default_thumbnail)

    # Guildings
    gildings = list()
    if post_data['gildings']['gid_3'] > 0:
        gildings.append("Platinum x" + str(post_data['gildings']['gid_3']))
    if post_data['gildings']['gid_2'] > 0:
        gildings.append("Gold x" + str(post_data['gildings']['gid_2']))
    if post_data['gildings']['gid_1'] > 0:
        gildings.append("Silver x" + str(post_data['gildings']['gid_1']))

    if gildings:
        post_embed.add_field(name="Gildings", value=", ".join(gildings))

    return post_embed


async def reddit_comment(comment_url: str):
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

    comment_embed = Embed()
    comment_embed.colour = embedcolor
    comment_embed.url = comment_url
    comment_embed.title = utils.trimtolength(link_data['title'], 256)
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
    if comment_data['gildings']['gid_3'] > 0:
        gildings.append("Platinum x" + str(comment_data['gildings']['gid_3']))
    if comment_data['gildings']['gid_2'] > 0:
        gildings.append("Gold x" + str(comment_data['gildings']['gid_2']))
    if comment_data['gildings']['gid_1'] > 0:
        gildings.append("Silver x" + str(comment_data['gildings']['gid_1']))

    if gildings:
        comment_embed.add_field(name="Gildings", value=", ".join(gildings))

    return comment_embed
