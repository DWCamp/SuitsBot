import aiohttp
import feedparser
from datetime import datetime
import random
import re
import traceback
from typing import Optional, Union

from discord import Client, Embed, Member, Message, User
from discord.abc import GuildChannel, PrivateChannel
from discord.ext.commands import Context

from config.local_config import *
from constants import EMBED_COLORS


# ------------------------------------------------------------------------ Discord Specific Functions

_bot: Client = None  # This will be defined as soon as the bot is initialized


def _get_bot() -> Client:
    """ Sometimes you just need the bot """
    if _bot is None:
        raise AttributeError("`utils.get_bot()` was called before the bot was initialized")
    return _bot


async def get_message(channel_id: int, message_id: int) -> Optional[Message]:
    """
    Fetches a specific message object from Discord using a channel and message ID
    :param channel_id: The ID of the channel containing the message
    :param message_id: The ID of the message being fetched
    :return: If found, the Message object with that ID. `None` otherwise
    """
    message_channel = _get_bot().get_channel(channel_id)
    if message_channel is None:
        return None
    return await message_channel.fetch_message(message_id)


async def get_channel(channel_id: int) -> Optional[Union[GuildChannel, PrivateChannel]]:
    """
    Fetches a specific channel object from Discord using a channel ID

    :param channel_id: The ID of the channel containing the message
    :return: If found, the Channel object with that ID. `None` otherwise
    """
    return _get_bot().get_channel(channel_id)


def get_screen_name(user: Union[User, Member]) -> str:
    """
    Gets the screen name of either a User or Member object
    :param user: The User or Member
    :return: The name or nickname (if applicable) of a user
    """
    return user.nick if isinstance(user, Member) and user.nick is not None else user.name


# ------------------------------------------------------------------------ Utilities


def curr_time():
    """ Returns a human readable printout of the current time """
    return datetime.now().strftime("%a %b %d, %I:%M:%S %p")


def random_element(array):
    """ Returns a random element from a list """
    return array[random.randint(0, len(array) - 1)]


def trim_to_len(content, length):
    """ Converts a value to a string of limited length, truncated by ellipses

    Parameters
    -------------
    content : Any
        The value to trim
    length : int
        The maximum length of the returned string. Strings under this limit will be returned unchanged

    Returns
    -------------
    A content as a string (if it wasn't already) of length <= length. Truncated strings have "…" added to the end to
    visually indicate that they have been shortened
    """
    content = str(content)
    if length < 2:
        return "…"
    if len(content) > length:
        return content[:length - 1] + "…"
    return content


def internal_strip(content: str) -> str:
    """
    Reduces all instances of whitespace (space, new line, tab) in a string to single spaces
    Most useful for cleaning up crazy Amazon HTML

    :param content: The string to strip
    :return: The stripped string
    """

    return " ".join(re.split(r"\s+", content))


def time_from_unix_ts(timestamp):
    """
    Converts a unix timestamp to a human readable printout

    Parameters
    -------------
    timestamp : str or int
        A UNIX timestamp in UTC

    Returns
    -------------
    time : str
        Printout
    """
    time = datetime.fromtimestamp(int(timestamp))
    return time.strftime("%a %b %d, %I:%M:%S %p") + " ET"


def first_whitespace(haystack):
    """
    Returns the index of the first occurrence of whitespace in a string

    :param haystack: The string to search in
    :return: The index of the first whitespace character, returns -1 if no such character exists
    """
    count = 0
    for char in haystack:
        if char in [" ", "\n", "\t", "\r"]:
            return count
        count += 1
    return -1


def embed_to_str(embed) -> str:
    """
    Creates a string which represents the contents of an embed in the following format:

    <title>
    ----
    <description>
    ----
    <field>: <field value>
    ...
    ----
    <footer>
    URL: <url>


    :param embed: The embed to parse
    :return: A string description of the embed
    """
    text_embed = ""

    # Title
    text_embed += f"{embed.title}"
    # Description
    if embed.description is not Embed.Empty:
        description = embed.description
        # Escape triple backtick by breaking them up with ZWJ
        description = description.replace("```", "`‍`‍`")
        text_embed += f"\n----\n{description}"
    # Fields
    if embed.fields:
        text_embed += "\n----"
    for field in embed.fields:
        text_embed += f"\n{field.name}: {field.value}"
    # Footer
    if embed.footer.text is not Embed.Empty:
        text_embed += f"\n----\n{embed.footer.text}"
    # URL
    if embed.url is not Embed.Empty:
        "\nURL: {embed.url}"

    return text_embed


# ------------------------------------------------------------------------ Web functions

def checkurl(regex, url):
    """
    Validates that a string is a properly formatted url

    Parameters
    -------------
    regex : compiled regex pattern
        The pattern to check the url against
    url : str
        The string to check

    Returns
    -------------
    Returns True if the url matches the format of a url
    """
    return regex.fullmatch(url) is not None


def embed_from_dict(dictionary, title=None, description=None, thumbnail_url=None, color=EMBED_COLORS["default"]):
    """
    Creates an embeded object from a dictionary

    dictionary : {str: str} dictionary
        A dictionary mapping field names to values
    title : str
        The title of the embed
    description : str
        The description of the embed
    thumbnail_url : str
        A url to the image which will become the embed thumbnail
    color : int
        The hexadecimal value for the color of the embed's highlight.
        If not provided, uses the default (SuitsBot purple)

    Returns
    ---------
    An embed built with the passed parameters
    """
    embed = Embed()
    if title is not None:
        embed.title = title
    if thumbnail_url is not None:
        embed.set_thumbnail(url=thumbnail_url)
    if description is not None:
        embed.description = description
    if color is not None:
        embed.colour = color

    for key in dictionary.keys():
        embed.add_field(name=key, value=dictionary[key], inline=False)
    return embed


async def get_json_with_get(url, params=None, headers=None, content_type=None):
    """
    Requests JSON data using a GET request

    Parameters
    -------------
    url : str
        The url to request from
    params : Optional - dict{str:str}
        Parameters passed in the request. 
        If not provided, an empty dict is passed
    headers : dict{str:str}
        Headers passed in the request
        If not provided, the default headers are used
    content_type : Optional - String
        Content type of the returned json

    Returns
    -------------
    If the request is valid, a list
    [0] - json dictionary
    [1] - resp.status

    If the request fails, a list
    [0] - None
    [0] - resp.status
    """

    # Create parameter dictionary if none passed
    if params is None:
        params = {}

    # Use default headers if none passed, otherwise
    # add passed headers to default dictionary
    if headers is None:
        headers = HEADERS
    else:
        merged_headers = HEADERS
        merged_headers.update(headers)
        headers = merged_headers

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as resp:
            if resp.status is 200:
                json = await resp.json(content_type=content_type)
                return [json, 200]
            return [None, resp.status]


async def get_json_with_post(url, params=None, headers=None, json=None):
    """
    Requests JSON data using a POST request

    Parameters
    -------------
    url : str
        The url to request from
    params : Optional - dict{str:str}
        Parameters passed in the request. 
        If not provided, an empty dict is passed
    headers : dict{str:str}
        Headers passed in the request
        If not provided, the default headers are used
    json : Optional - dict{str:str}
        The JSON dictionary to be posted with the API

    Returns
    -------------
    If the request is valid, a list
    [0] - json dictionary
    [1] - resp.status

    If the request fails, a list
    [0] - None
    [0] - resp.status
    """

    # Create parameter dictionary if none passed
    if params is None:
        params = {}

    # Use default headers if none passed, otherwise
    # add passed headers to default dictionary
    if headers is None:
        headers = HEADERS
    else:
        merged_headers = HEADERS
        merged_headers.update(headers)
        headers = merged_headers

    # Create json dictionary if none passed
    if json is None:
        json = {}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, params=params, json=json) as resp:
            json = await resp.json()
            return [json, resp.status]


async def get_website_text(url, params=None, json=None):
    """
    Gets the contents of a web page and returns it in raw HTML

    :param url: The url to query
    :param params: a dictionary of url parameters
    :param json: A JSON payload to include
    :return: The raw HTML of the web page
    """
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(url, params=params, json=json) as resp:
            if resp.status is not 200:
                return None
            return await resp.text()


def get_rss_feed(url):
    """
    Returns a feedparser object containing the information about the RSS feed

    :param url: (str) the url of the rss feed
    :return: A feedparser object
    """
    return feedparser.parse(url)


# ------------------------------------------------------------------------ Database caching

def add_to_cache(dbconn, key, value=None):
    """
    Add an entry to the cache

    Parameters
    -------------
    dbconn : DBConnection
        A database connection
    key : str
        The cache key
    value : Optional - str
        The value to store

    Raises
    -------------
    ValueError - If a Cache entry already exists with the provided key
    """

    dbconn.ensure_sql_connection()

    # Check if key is already in use
    select_command = "SELECT * FROM Cache WHERE ID=%s"
    select_data = (key,)
    cursor = dbconn.execute(select_command, select_data)
    if cursor.rowcount > 0:
        raise ValueError("Entry already exists for key " + key)

    # Add key
    cache_command = "INSERT INTO Cache VALUES (%s, %s)"
    cache_data = (key, value)
    dbconn.execute(cache_command, cache_data)
    dbconn.commit()
    return None


def update_cache(dbconn, key, value):
    """
    Cache a value

    Parameters
    -------------
    dbconn : DBConnection
        A database connection object
    key : str
        The cache key
    value : str
        The value to store
    """

    dbconn.ensure_sql_connection()
    cache_command = "UPDATE Cache SET Value=%s WHERE ID=%s"
    cache_data = (value, key)
    dbconn.execute(cache_command, cache_data)
    dbconn.commit()


def load_from_cache(dbconn, key, default=None):
    """
    Load a cache values from database

    Parameters
    -------------
    dbconn : DBConnection
        A database connection object
    key : str
        The cache key
    default : Any
        The value to return if the cache contains
        no row for the provided key

    Returns
    -------------
    str : The value stored under the provided key
    """

    query = "SELECT * FROM Cache WHERE ID=%s"
    data = key,
    cursor = dbconn.execute(query, data)
    row = cursor.fetchone()
    if row is None:
        return default
    return row[1].decode("utf-8")


# ------------------------------------------------------------------------ Error messages

async def flag(alert, description=None, ctx=None, message=None):
    """
    Send a non-urgent message to the dev

    Parameters
    -------------
    alert : str
        A title for the alert
    description : Optional - str
        The body of the message. Use this for a description of what went wrong as well
        as any stack trace or additional text
    ctx : Optional - context object
        The context object of the message which triggered the flag
    message : Optional - message object
        The message object which triggered the flag, used in case a context object is not available
    """
    bot = _get_bot()
    try:
        if message is None:
            if ctx is None:
                if description is None:
                    await bot.ALERT_CHANNEL.send("----\n**Alert:\n" + alert + "**")
                else:
                    await bot.ALERT_CHANNEL.send("Alert:\n" + alert + "\n---\n" + description)
                return
            message = ctx.message

        flag_embed = Embed()
        flag_embed.title = alert
        flag_embed.colour = EMBED_COLORS["flag"]
        flag_embed.add_field(name="Author", value=message.author.name, inline=False)
        flag_embed.add_field(name="Time", value=curr_time(), inline=False)
        if isinstance(message.channel, PrivateChannel):
            flag_embed.add_field(name="Channel", value="Private", inline=False)
        else:
            flag_embed.add_field(name="Channel",
                                 value=message.guild.name + " / " + message.channel.name,
                                 inline=False)
            flag_embed.add_field(name="Link",
                                 value=f"https://discord.com/channels/"
                                       f"{message.guild.id}/{message.channel.id}/{message.id}")

        # Try to avoid issues where users joining servers causes an error because of blank messages
        if message.content is not None and message.content != "":
            flag_embed.add_field(name="Message", value=message.content, inline=False)

        if description is not None:
            flag_embed.description = trim_to_len(description, 2048)
        await bot.ALERT_CHANNEL.send(embed=flag_embed)
    except Exception as e:
        await report(str(e) + "\n\nAlert:\n" + alert + "\nDescription:\n" + trim_to_len(description, 2000),
                     source="Error when producing flag", ctx=ctx)


async def report(alert, source=None, ctx=None):
    """
    Send an error message to the dev

    This message should be called when a serious issue has occurred.
    When report is called, an embed will be posted in the error-messages
    channel on the dev server. It will print out all relevant details
    including the alert message, the stack trace, and the exception
    This embed is not returned, it is sent immediately

    Parameters
    -------------
    alert : str
        A title for the alert
    source : Optional - str
        The location in the codebase which raised the error
    ctx : Optional - context object
        The context/message object which triggered the flag
    """
    bot = _get_bot()

    # Value validation
    if not alert:
        alert = "❗"

    error_embed = Embed()
    if ctx is None:
        error_embed.title = "Alert"
        error_embed.colour = EMBED_COLORS["error"]
        error_embed.add_field(name="Alert", value=alert, inline=False)
        if source is not None:
            error_embed.add_field(name="Source", value=source, inline=False)
        await bot.ERROR_CHANNEL.send(embed=error_embed)
        return
    msg = ctx.message if isinstance(ctx, Context) else ctx
    error_embed.title = "ERROR REPORT"
    error_embed.colour = EMBED_COLORS["error"]
    error_embed.add_field(name="Alert", value=alert, inline=False)
    error_embed.add_field(name="Author", value=msg.author.name, inline=False)
    error_embed.add_field(name="Time", value=curr_time(), inline=False)
    if isinstance(msg.channel, PrivateChannel):
        error_embed.add_field(name="Channel", value="Private", inline=False)
    else:
        error_embed.add_field(name="Channel",
                              value=msg.guild.name + " / " + msg.channel.name,
                              inline=False)
        error_embed.add_field(name="Link",
                              value=f"https://discord.com/channels/"
                                    f"{msg.guild.id}/"
                                    f"{msg.channel.id}/"
                                    f"{msg.id}",
                              inline=False)
    if source is not None:
        error_embed.add_field(name="Source", value=source, inline=False)
    error_embed.add_field(name="Message", value=msg.content, inline=False)

    # Error message (exception + stacktrace)
    error_message = traceback.format_exc(limit=5)
    error_message = "```" + trim_to_len(error_message, 2042) + "```"
    error_embed.description = error_message

    await bot.ERROR_CHANNEL.send(embed=error_embed)


# ------------------------------------------------------------------------ HTML Processing

def html_to_markdown(htmltext):
    """ Converts HTML tags to their corresponding Markdown symbols """
    htmltext = htmltext.replace("<b>", "**").replace("</b>", "**")
    htmltext = htmltext.replace("<i>", "*").replace("</i>", "*")
    htmltext = htmltext.replace("<li>", " - ").replace("</li>", "")
    htmltext = htmltext.replace("</p>", "\n").replace("<p>", "")
    htmltext = htmltext.replace("<br>", "\n").replace("<br />", "")
    strip_html_tags(htmltext)
    return htmltext


def strip_html_tags(htmltext):
    """ Removes HTML tags which are not markdown related """
    htmltext = htmltext.replace("<ul>", "").replace("</ul>", "")
    htmltext = htmltext.replace("<sup>", "").replace("</sup>", "")
    htmltext = htmltext.replace("<b>", "").replace("</b>", "")
    htmltext = htmltext.replace("<i>", "").replace("</i>", "")
    htmltext = htmltext.replace("<li>", "").replace("</li>", "")
    htmltext = htmltext.replace("</p>", "").replace("<p>", "")
    # Removes every tag named
    for html_tag in ["span"]:
        htmltext = htmltext.replace("</" + html_tag + ">", "")
        tagloc = htmltext.find("<" + html_tag)
        i = 0
        while tagloc > -1 and i < 50:
            i += 1
            endtagloc = htmltext[tagloc:].find(">") + tagloc
            htmltext = htmltext[:tagloc] + htmltext[endtagloc + 1:]
            tagloc = htmltext.find("<" + html_tag)

    # Remove the tag and its contents for every tag named
    for html_tag in ["small"]:
        tagloc = htmltext.find("<" + html_tag)
        i = 0
        while tagloc > -1 and i < 50:
            i += 1
            endtagloc = htmltext[tagloc:].find("/" + html_tag + ">") + tagloc
            htmltext = htmltext[:tagloc] + htmltext[endtagloc + (2 + len(html_tag)):]
            tagloc = htmltext.find("<" + html_tag)

    return htmltext
