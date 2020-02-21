import aiohttp
import feedparser
from datetime import datetime
import random
import traceback
from discord import Embed
from local_config import *
from constants import EMBED_COLORS


# ------------------------------------------------------------------------ Utilities

def currtime():
    """ Returns a human readable printout of the current time """
    return datetime.now().strftime("%a %b %d, %I:%M:%S %p")


def random_element(array):
    """ Returns a random element from a list """
    return array[random.randint(0, len(array) - 1)]


def trimtolength(content, length):
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


def timefromunix(timestamp):
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


def embedfromdict(dictionary, title=None, description=None, thumbnail_url=None, color=EMBED_COLORS["default"]):
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
        headers = merged_headers.update(headers)

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
        headers = merged_headers.update(headers)

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

async def flag(bot, alert, description=None, ctx=None, message=None):
    """
    Send a non-urgent message to the dev

    Parameters
    -------------
    bot : discord.bot object
        The bot object for sending the message
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
    try:
        if message is None:
            if ctx is None:
                if description is None:
                    await bot.send_message(bot.ALERT_CHANNEL, "----\n**Alert:\n" + alert + "**")
                else:
                    await bot.send_message(bot.ALERT_CHANNEL, "Alert:\n" + alert + "\n---\n" + description)
                return
            message = ctx.message

        flag_embed = Embed()
        flag_embed.title = alert
        flag_embed.colour = EMBED_COLORS["flag"]
        flag_embed.add_field(name="Author", value=message.author.name, inline=False)
        flag_embed.add_field(name="Time", value=currtime(), inline=False)
        if message.channel.is_private:
            flag_embed.add_field(name="Channel", value="Private", inline=False)
        else:
            flag_embed.add_field(name="Channel", value=message.server.name + " / " + message.channel.name,
                                 inline=False)

        # Try to avoid issues where users joining servers causes an error because of blank messages
        if message.content is not None and message.content != "":
            flag_embed.add_field(name="Message", value=message.content, inline=False)

        if description is not None:
            flag_embed.description = trimtolength(description, 2048)
        await bot.send_message(bot.ALERT_CHANNEL, embed=flag_embed)
    except Exception as e:
        await report(bot,
                     str(e) + "\n\nAlert:\n" + alert + "\nDescription:\n" + trimtolength(description, 2000),
                     source="Error when producing flag", ctx=ctx)


async def report(bot, alert, source=None, ctx=None):
    """
    Send an error message to the dev

    This message should be called when a serious issue has occurred.
    When report is called, an embed will be posted in the error-messages
    channel on the dev server. It will print out all relevant details
    including the alert message, the stack trace, and the exception
    This embed is not returned, it is sent immediately

    Parameters
    -------------
    bot : discord.bot object
        The bot object for sending the message
    alert : str
        A title for the alert
    source : Optional - str
        The location in the codebase which raised the error
    ctx : Optional - context object
        The context object of the message which triggered the flag
    """
    error_embed = Embed()
    if ctx is None:
        error_embed.title = "Alert"
        error_embed.colour = EMBED_COLORS["error"]
        error_embed.add_field(name="Alert", value=alert, inline=False)
        if source is not None:
            error_embed.add_field(name="Source", value=source, inline=False)
        await bot.send_message(bot.ERROR_CHANNEL, embed=error_embed)
        return
    error_embed.title = "ERROR REPORT"
    error_embed.colour = EMBED_COLORS["error"]
    error_embed.add_field(name="Alert", value=alert, inline=False)
    error_embed.add_field(name="Author", value=ctx.message.author.name, inline=False)
    error_embed.add_field(name="Time", value=currtime(), inline=False)
    if ctx.message.channel.is_private:
        error_embed.add_field(name="Channel", value="Private", inline=False)
    else:
        error_embed.add_field(name="Channel",
                              value=ctx.message.server.name + " / " + ctx.message.channel.name,
                              inline=False)
    if source is not None:
        error_embed.add_field(name="Source", value=source, inline=False)
    error_embed.add_field(name="Message", value=ctx.message.content, inline=False)

    # Error message (exception + stacktrace)
    error_message = traceback.format_exc(limit=5)
    error_message = "```" + trimtolength(error_message, 2042) + "```"
    error_embed.description = error_message

    await bot.send_message(bot.ERROR_CHANNEL, embed=error_embed)


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
