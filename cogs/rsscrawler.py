from datetime import datetime, timedelta
from random import randint
import re
from discord.ext import commands
from discord.ext.commands import Cog
from discord import Embed
from constants import *
import parse
import utils


class RSSCrawler(Cog):
    """
    Commands dealing with fetching rss feeds
    """
    def __init__(self, bot):
        self.bot = bot
        self.feeds = [
            RSSFeed("Accidental Tech Podcast",
                    "http://atp.fm/episodes?format=rss",
                    color=0x203D65),
            RSSFeed("KSP History",
                    "https://dwcamp.net/feeds/ksp_history.xml",
                    color=0x339BDC),
            RSSFeed("Main Engine Cutoff",
                    "https://feeds.simplecast.com/Zg9AF5cA",
                    color=0x9FB1C2),
            RSSFeed("My Brother My Brother and Me",
                    "https://feeds.simplecast.com/wjQvYtdl",
                    color=0x4B4B4B),
            RSSFeed("Off-Nominal",
                    "https://feeds.simplecast.com/iyz_ESAp",
                    color=0x716C4F),
            RSSFeed("The Adventure Zone",
                    "https://feeds.simplecast.com/cYQVc__c"),
            RSSFeed("We Martians",
                    "https://www.wemartians.com/feed/podcast",
                    color=0xC4511F),
            WebComic("xkcd",
                     "https://dwcamp.net/feeds/xkcd.xml",
                     color=0xFFFFFF),
        ]

    # Searches for an item in your favorite RSS Feeds
    @commands.command(help=LONG_HELP['rssfeed'],
                      brief=BRIEF_HELP['rssfeed'], aliases=ALIASES["rssfeed"])
    async def rssfeed(self, ctx):
        try:
            invoking_id = ctx.invoked_with
            for feed in self.feeds:
                if invoking_id in feed.aliases:
                    await self.handle_rss_feed(feed, ctx)
                    return
            await ctx.send("This command can be used to search for episodes of your favorite feed. It " +
                           "currently supports the following channels:\n" + FEED_TEXT_LIST)
        except Exception as e:
            await utils.report(str(e), source="rssfeed command", ctx=ctx)

    async def handle_rss_feed(self, feed, ctx):
        """
        The universal rss feed handler. Takes in an RSSFeed object
        then does all the magic
        :param feed: The RSSFeed
        :param ctx: The ctx object of the inciting message
        """
        try:
            message = parse.strip_command(ctx.message.content)

            # Update feed
            feed.refresh_if_stale()

            # Show most recent episode
            if message == "":
                episode = feed.items[0]
                await ctx.send(embed=feed.get_embed(episode))
                return

            # check for subcommand and parse it out
            subcommand = ""
            parameter = message
            if message[0] == "-":
                whitespace = utils.first_whitespace(message)
                if whitespace == -1:
                    subcommand = message[1:]
                    parameter = ""
                else:
                    subcommand = message[1:whitespace]
                    parameter = message[whitespace:].strip()

            # Teach the person how to use this thing
            if subcommand == "help":
                command_name = ctx.invoked_with
                title = f"!{command_name} - User Guide"
                description = f"Searches the RSS feed for {feed.title}"
                helpdict = {
                    f"!{command_name}": "Post the most recent item in the feed",
                    f"!{command_name} <word>": "Post the most recent item whose title contains the whole word <word>",
                    f"!{command_name} -help": "Posts this message",
                    f"!{command_name} -reg <regex>": "Perform a regular expression search for the most "
                                                     "recent item title matching <regex>",
                    f"!{command_name} -refresh": "Force the bot to refresh its cache"}
                thumbnail = feed.image if feed.image is not None else COMMAND_THUMBNAILS["rssfeed"]
                await ctx.send(embed=utils.embed_from_dict(helpdict,
                                                           title=title,
                                                           description=description,
                                                           thumbnail_url=thumbnail))
                return

            # Dump all the info about the feed
            if subcommand == "details":
                await ctx.send(feed.to_string())
                return

            # Test an embed for a given feed
            if subcommand == "embed":
                await ctx.send(embed=feed.get_embed(feed.items[0]))
                return

            # Test an embed for a given feed
            if subcommand == "image":
                embed = Embed()
                embed.set_image(url=feed.image)
                await ctx.send(embed=embed)
                return

            # If some nerd like Kris or Pat wants to do regex search
            if subcommand == "reg":
                episode = feed.search(parameter, regex=True)
                if episode:
                    await ctx.send(embed=feed.get_embed(episode))
                    return
                await ctx.send(f"I couldn't find any results for the regex string `{parameter}`")

            # Force a refresh on the feed
            if subcommand == "refresh":
                feed.refresh()
                await ctx.send(f"Alright, I have refreshed the feed `{feed.feed_id}`")
                return

            # Returns search results that the user can select
            if subcommand == "search":
                await ctx.send("This has not been implemented yet :sad:")
                return

            # If there was a subcommand but it was unrecognized
            if subcommand != "":
                await ctx.send(f"I'm sorry, I don't understand the subcommand `{subcommand}`. " +
                               f"Please consult `-help` for more information")
                return

            # Search for the term
            episode = feed.search(parameter)
            if episode:
                await ctx.send(embed=feed.get_embed(episode))
                return
            await ctx.send(f"I couldn't find any results in the {feed.title} feed "
                           f"for the term `{parameter}` :worried:")

        except Exception as e:
            await utils.report(str(e), source=f"handle_rss_feed() for '{feed.feed_id}'", ctx=ctx)


class RSSFeed:
    """
    Creates an object representing a podcast feed

    :param feed_id: The id used to store information about the feed
    :param url: The url of the feed
    :param color: The color of the embed for episodes
    :param ttl: A timedelta object representing how long the cache
        can last before it is considered "stale". Defaults to 1 minute
    """
    def __init__(self, feed_id, url, color=EMBED_COLORS["default"], ttl=timedelta(hours=24)):
        self.feed_id = feed_id
        self.feed_url = url
        self.aliases = FEED_ALIAS_LIST[feed_id]
        self.color = color
        self.ttl = ttl

        # RSS Info. These values are not defined at init and
        # must be fetched by refreshing the feed

        self.raw_rss = None  # The feedparser dictionary
        self.feed = None  # The "feed" object from feedparser
        self.channel = None  # The channel object
        self.fetch_time = None  # When the item was fetched
        self.title = feed_id  # The title of the feed (temporarily set to feed_id)
        self.subtitle = None  # The description of the feed
        self.image = None  # The covert art for the feed
        self.link = None  # The website associated with the feed
        self.items = None  # The list of items in the feed

    def __len__(self):
        """
        Support len(RSSFeed)
        :return:
        """
        return len(self.items)

    def search(self, term, regex=False):
        """
        Finds the item whose title exactly matches the search term (case insensitive)
        If one can not be found, the most recent item in the feed whose title contains
        the search term will be returned

        :param term: The term being searched for
        :param regex: Whether to regex escape the search term. For the true nerds
            Defaults to `False`
        :return: If it finds an appropriate episode, it returns it.
            If it can't find any matching episode, it returns null
        """
        if regex:
            pattern = re.compile(term, re.IGNORECASE)
            fuzzy_pattern = pattern
        else:
            escaped = re.escape(term)
            pattern = re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)
            fuzzy_pattern = re.compile(escaped.replace(r"\ ", r".*"), re.IGNORECASE)

        partial_match = None
        fuzzy_match = None
        for item in self.items:
            if re.fullmatch(pattern, item["title"]):  # If an exact match is found, return
                return item
            # In case of no full match, find most recent episode containing the string
            if re.search(pattern, item["title"]) and partial_match is None:
                print(f"Found partial match `{item['title']}`")
                partial_match = item
            # In case of no partial match, do a "fuzzy search" where whitespace is replaced with ".*"
            if re.search(fuzzy_pattern, item["title"]) and fuzzy_match is None:
                print(f"Found fuzzy match `{item['title']}`")
                fuzzy_match = item
        return partial_match if partial_match is not None else fuzzy_match

    def to_string(self):
        string = f"""
Title: {self.title}
Item Count: {len(self.items)}
Fetch time: {self.fetch_time}
"""
        return string

    def is_stale(self):
        """
        Checks if the information is stale (older than 24 hours)
        :return: Returns 'True' if the stored data was cached more than 24 hours ago
        """
        if self.raw_rss is None:
            return True
        return datetime.today() > self.fetch_time + self.ttl

    def refresh(self):
        """
        Updates the cached data
        """
        print(f"Refreshing feed '{self.feed_id}'")
        self.raw_rss = utils.get_rss_feed(self.feed_url)
        self.fetch_time = datetime.today()
        self.channel = self.raw_rss["channel"]
        self.items = self.raw_rss["items"]

        self.feed = self.raw_rss["feed"]
        self.subtitle = self.feed.subtitle
        self.link = self.feed["link"]
        if self.feed.image:
            self.image = self.feed.image["href"]

        self.title = self.channel["title"]

        # Optional elements
        if "ttl" in self.channel:
            self.ttl = self.channel["ttl"]

    def refresh_if_stale(self):
        """
        Helper method. Only refreshes information if cache is 'data' (i.e. data is older than max_age)
        """
        if self.is_stale():
            self.refresh()

    def get_embed(self, item):
        """
        Generates an embed containing information about the provided item
        :param item: An item from this feed
        :return: An embed of information about it
        """
        embed = Embed()
        embed.colour = self.color
        embed.title = item["title"]
        embed.url = item["link"]
        if "description" in item:
            description = item["subtitle"] if "subtitle" in item else item["summary"]
            embed.description = utils.trim_to_len(description, 2048)
        embed.set_author(name=self.title, url=self.link)
        if self.image:
            embed.set_thumbnail(url=self.image)

        embed.add_field(name="Published", value=format_time(item["published_parsed"]))
        embed.add_field(name="Quality", value=f"{randint(20, 100) / 10}/10")

        # look through enclosures for an image
        for enclosure in item.links:
            if enclosure["type"].startswith("image"):
                embed.set_image(url=enclosure["href"])

        embed.set_footer(text=utils.trim_to_len(f"{self.title} - {self.subtitle}", 256))
        return embed


class WebComic(RSSFeed):
    """
    A special case RSS feed, without fields and the description moved to the footer
    """
    def get_embed(self, item):
        """
        Generates an embed for an issue of a webcomic

        :param item: ([str : Any]) The dictionary of information for the panel
        :return: Embed
        """
        embed = super().get_embed(item)

        # Remove all fields
        embed.clear_fields()

        # Move description to footer
        embed.description = ""
        description = item["subtitle"] if "subtitle" in item else item["summary"]
        embed.set_footer(text=utils.trim_to_len(description, 2048))

        return embed


def format_time(time):
    """
    Formats a datetime object for easy human viewing
    Formats to ISO 8601
    :param time: The datetime object
    :return: The time in 'YYYY-MM-DD' format
    """
    return f"{time.tm_year}-{time.tm_mon}-{time.tm_mday}"


def setup(bot):
    bot.add_cog(RSSCrawler(bot))
