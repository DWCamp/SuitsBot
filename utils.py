import aiohttp
from datetime import datetime
import random
import traceback
from discord import Embed
from constants import EMBED_COLORS, HEADERS


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
    return time.strftime("%a %b %d, %I:%M:%S %p") + " EST"


# ------------------------------------------------------------------------ Web functions

def checkurl(regex, url):
    """
    Validates that a string is a properly formatted url

    Parameters
    -------------
    regex : compiled regex patter
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

    dictionary - A [str:str] dictionary where the keys are the field names and the values are the field values
    title - The title of the embed
    description - The description of the embed
    thumbnail_url - A string which holds a url to the image which will become the embed thumbnail
    color - The embed color
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


async def get_json_with_get(url, params=None, headers=HEADERS, content_type=None):
    """ Requests JSON data using a GET request

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

    if params is None:
        params = {}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as resp:
            if resp.status is 200:
                json = await resp.json(content_type=content_type)
                return [json, 200]
            return [None, resp.status]


async def get_json_with_post(url, params=None, json=None):
    """ Requests JSON data using a POST request

    Parameters
    -------------
    url : str
        The url to request from
    params : Optional - dict{str:str}
        Parameters passed in the request. 
        If not provided, an empty dict is passed
    json : Optional - dict{str:str}
        The JSON dictionary to be posted with the API
    }

    Returns
    -------------
    If the request is valid, a list
    [0] - json dictionary
    [1] - resp.status

    If the request fails, a list
    [0] - None
    [0] - resp.status
    """

    if params is None:
        params = {}
    if json is None:
        json = {}

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(url, params=params, json=json) as resp:
            json = await resp.json()
            return [json, resp.status]


async def get_website_text(url, params=None, json=None):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(url, params=params, json=json) as resp:
            if resp.status is not 200:
                return None
            return await resp.text()


# ------------------------------------------------------------------------ Database caching

def addtocache(dbconn, key, value=None):
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


def loadfromcache(dbconn, key):
    """
    Load a cache values from database

    Parameters
    -------------
    dbconn : DBConnection
        A database connection object
    key : str
        The cache key

    Returns
    -------------
    str : The value stored under the provided key
    """

    query = "SELECT * FROM Cache WHERE ID=%s"
    data = key,
    cursor = dbconn.execute(query, data)
    row = cursor.fetchone()
    if row is None:
        return None
    return row[1].decode("utf-8")


# ------------------------------------------------------------------------ Error messages

async def flag(bot, alert, description="(No description provided)", ctx=None, message=None):
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
    Send an urgent message to the dev

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
    stack_trace = reversed(traceback.format_stack()[:-1])
    stack_trace = "```" + trimtolength("".join(stack_trace), 2042) + "```"
    error_embed.description = stack_trace
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
