from datetime import datetime, timedelta
from random import randint
import re
from discord.ext import commands
from discord import Embed
from constants import *
import parse
import utils


class RSSCrawler:
    """
    Commands dealing with fetching rss feeds

    Supports:
        - MECO (!meco)
        - Off-Nominal (!on)
        - We Martians (!wm)
        + xkcd (!xkcd)  <- NOT IMPLEMENTED
    """
    def __init__(self, bot):
        self.bot = bot
        self.feeds = {}
        self._feed_ids = {"meco": "https://feeds.simplecast.com/Zg9AF5cA",
                          "on": "https://feeds.simplecast.com/iyz_ESAp",
                          "wm": "https://www.wemartians.com/feed/podcast/",
                          "xkcd": "https://xkcd.com/rss.xml"}
        self._embed_hex_codes = {"meco": 0x9FB1C2,
                                 "on": 0x716C4F,
                                 "wm": 0xC4511F,
                                 "xkcd": 0xFFFFFF}

    # Posts the url for the MECO episode with the passed argument
    @commands.command(pass_context=True, help=LONG_HELP['meco'], brief=BRIEF_HELP['meco'], aliases=ALIASES['meco'])
    async def meco(self, ctx):
        try:
            await self.handle_podcast("meco", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="meco command", ctx=ctx)

    # Posts the url for the Off-Nominal episode with the passed argument
    @commands.command(pass_context=True, help=LONG_HELP['on'], brief=BRIEF_HELP['on'], aliases=ALIASES['on'])
    async def on(self, ctx):
        try:
            await self.handle_podcast("on", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="on command", ctx=ctx)

    # Posts the url for the We Martians episode with the passed argument
    @commands.command(pass_context=True, help=LONG_HELP['wm'], brief=BRIEF_HELP['wm'], aliases=ALIASES['wm'])
    async def wm(self, ctx):
        try:
            await self.handle_podcast("wm", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="wm command", ctx=ctx)

    # Posts the url for the xkcd comic with the passed argument
    @commands.command(pass_context=True, hidden=True, help=LONG_HELP['wm'],
                      brief=BRIEF_HELP['wm'], aliases=ALIASES['wm'])
    async def xkcd(self, ctx):
        try:
            await self.bot.say("Shhhhhhhhhh...")
            # await self.handle_podcast("xkcd", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="xkcd command", ctx=ctx)

    async def get_podcast(self, feed_id):
        """
        Makes podcast fetching lazy. If the podcast has already been fetched, it returns the podcast.
        If the podcast has not been fetched yet, it firsts initializes the podcast object retrieved.
        If the podcast was fetched but the data is stale, it will refresh the content

        :param feed_id: The podcasts's identifier(see self.podcasts)
        :return: The podcast object for that title
        """
        if feed_id not in self.feeds:
            self.feeds[feed_id] = RSSFeed(self._feed_ids[feed_id])
        self.feeds[feed_id].refresh_if_stale()
        return self.feeds[feed_id]

    async def handle_podcast(self, feed_id, ctx):
        """
        The universal podcast handler. Takes in the title of the podcast and
        the context of the message, then does all the magic
        :param feed_id: The podcast's identifier (e.g. 'meco', 'on', etc)
        :param ctx: The ctx object of the inciting message
        """
        try:
            podcast = await self.get_podcast(feed_id)
            message = parse.stripcommand(ctx.message.content)

            # Oops no parameter
            if message == "":
                await self.bot.say(
                    "Usage: `!" + feed_id + " <number>`")
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
                await self.bot.say("Search for an episode by typing a search term")
                return

            # Check the age
            if subcommand == "age":
                await self.bot.say(f"{podcast.fetchtime}\n{podcast.is_stale()}")
                return

            # Post all of the keys for the episode dict
            if subcommand == "deets":
                await self.bot.say(" | ".join(podcast.items[0].keys()))
                return

            # Dump all the info about the podcast
            if subcommand == "dump":
                await self.bot.say(podcast.to_string())
                return

            # Test an embed for a given podcast
            if subcommand == "embed":
                await self.bot.say(embed=self.embed_episode(feed_id, podcast.items[0]))
                return

            # Prints the text of the item requested
            if subcommand == "print":
                await self.bot.say(utils.trimtolength(podcast.items[0][parameter], 1000))
                return

            # If some nerd like Kris or Pat wants to do regex search
            if subcommand == "r":
                episode = podcast.search(parameter, regex=True)
                if episode:
                    await self.bot.say(embed=self.embed_episode(feed_id, episode))
                    return
                await self.bot.say(f"I couldn't find any results for the regex string `{parameter}`")

            # Force a refresh on the feed
            if subcommand == "refresh":
                self.feeds[feed_id].refresh()
                await self.bot.say(f"Alright, I have refreshed the feed `{feed_id}`")
                return

            # Returns search results that the user can select
            if subcommand == "search":
                await self.bot.say("This has not been implemented yet :sad:")
                return

            # If there was a subcommand but it was unrecognized
            if subcommand != "":
                await self.bot.say(f"I'm sorry, I don't understand the subcommand `{subcommand}`. " +
                                   f"Please consult `-help` for more information")
                return

            # Search for the term
            episode = podcast.search(parameter)
            if episode:
                await self.bot.say(embed=self.embed_episode(feed_id, episode))
                return
            await self.bot.say(f"I couldn't find any results for the term `{parameter}` :worried:")

        except Exception as e:
            await utils.report(self.bot, str(e), source=f"handle_podcast() for '{feed_id}'", ctx=ctx)

    def embed_results(self, episode_list):
        """
        Generates an embed representing a list of search results

        :param episode_list: [episode] The array of episodes.
            This is limited to five episodes
        :return: An embed containing the list of options
        """
        embed = Embed()
        emoji = [":one:", ":two:", ":three:", ":four:", ":five:"]
        description = ""
        for count, episode in enumerate(episode_list[:5]):
            description += emoji[count] + " " + episode["title"] + "\n"
        return embed

    def embed_episode(self, feed_id, episode):
        """
        Generates an embed for a given episode of a podcast

        :param feed_id: (str) The string identifier for the podcast (e.g. "on")
        :param episode: ([str : Any]) The dictionary of information for the episode
        :return: Embed
        """
        embed = Embed()
        podcast = self.feeds[feed_id]

        # Appearance
        embed.colour = self._embed_hex_codes[feed_id]
        embed.description = utils.trimtolength(episode["subtitle"], 2048)
        embed.set_thumbnail(url=podcast.image)

        # Data
        embed.title = episode["title"]
        embed.url = episode["link"]
        embed.set_author(name=podcast.title, url=podcast.url)

        timeobj = episode["published_parsed"]
        pubstr = f"{timeobj.tm_mon}/{timeobj.tm_mday}/{timeobj.tm_year}"

        embed.add_field(name="Published", value=pubstr)
        embed.add_field(name="Quality", value=f"{randint(20, 100) / 10}/10")

        return embed


class RSSFeed:
    """
    Creates an object representing a podcast feed

    :param url: The url of the feed
    :param ttl: A timedelta object representing how long the cache
        can last before it is considered "stale". Defaults to 1 minute
    """
    def __init__(self, url, ttl=timedelta(hours=1)):
        self.url = url
        feed = utils.get_rss_feed(url)
        self.feed = feed
        self.fetchtime = datetime.today()
        self.expire_time = self.fetchtime + ttl

        # RSS Info
        self.title = feed["channel"]["title"]
        self.description = feed["channel"]["description"]
        self.image = feed["channel"]["image"]["url"]
        self.url = feed["channel"]["link"]
        self.items = feed["items"]
        self.episodes = {}

        # Computed Info
        self.count = len(self.items)

        # Index elements by iTunes episode, or by number if not present
        num = 1
        for item in reversed(feed["items"]):
            if "itunes_episode" in item:
                self.episodes[item["itunes_episode"].lower()] = item
            # Bonus episodes get a "b" after their name and the number of the previous episode
            elif "itunes_episodetype" in item and item["itunes_episodetype"] == "bonus":
                self.episodes[f"{num - 1}b"] = item
                num -= 1  # Bonuses don't increment the count
            else:
                self.episodes[str(num)] = item
            num += 1

    def search(self, term, regex=False):
        """
        Finds the newest instance of a search term in an episode

        :param term: The term being searched for
        :param regex: Whether to regex escape the search term. For the true nerds
            Defaults to False
        :return: If it finds an appropriate episode, it returns it.
            If it can't find any matching episode, it returns null
        """
        if regex:
            pattern = re.compile(f"(?<!\w){term}(?!\w)")
        else:
            pattern = re.compile("(?<!\w)" + re.escape(term) + "(?!\w)", re.IGNORECASE)

        for episode in self.items:
            if re.search(pattern, episode["title"]):
                return episode
        return

    def to_string(self):
        string = f"""
Title: {self.title}
Count: {self.count}
Ep Nums: {list(self.episodes.keys())}
"""
        return string

    def is_stale(self):
        """
        Checks if the information is stale (older than 24 hours)
        :return: Returns 'True' if the stored data was cached more than 24 hours ago
        """
        return datetime.today() > self.expire_time

    def refresh(self):
        """
        Updates the cached data
        :return:
        """
        self.feed = utils.get_rss_feed(self.url)
        self.fetchtime = datetime.today()

    def refresh_if_stale(self):
        """
        Helper method. Only refreshes information if cache is 'data' (i.e. data is older than max_age)
        """
        if self.is_stale():
            self.refresh()


def setup(bot):
    bot.add_cog(RSSCrawler(bot))
