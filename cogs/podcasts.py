from datetime import datetime, timedelta
from discord.ext import commands
from discord import Embed
from constants import *
import parse
import utils


class Podcasts:
    """
    Commands dealing with fetching information about podcasts

    Supports:
        - MECO (!meco)
        - Off-Nominal (!on)
        - We Martians (!wm)
    """
    def __init__(self, bot):
        self.bot = bot
        self.feeds = {}
        self.podcasts = {"meco": "https://feeds.simplecast.com/Zg9AF5cA",
                         "on": "https://feeds.simplecast.com/iyz_ESAp",
                         "wm": "https://www.wemartians.com/feed/podcast/"}
        self.hex = {"wm": 0xC4511F}
        self.made_the_joke = False

    # Posts the url for the MECO episode with the passed number
    @commands.command(pass_context=True, hidden=True, help=LONG_HELP['meco'], brief=BRIEF_HELP['meco'], aliases=ALIASES['meco'])
    async def meco(self, ctx):
        try:
            await self.handle_podcast("meco", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="meco command", ctx=ctx)

    # Posts the url for the Off-Nominal episode with the passed number
    @commands.command(pass_context=True, hidden=True, help=LONG_HELP['on'], brief=BRIEF_HELP['on'], aliases=ALIASES['on'])
    async def on(self, ctx):
        try:
            await self.handle_podcast("on", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="on command", ctx=ctx)

    # Posts the url for the We Martians episode with the passed number
    @commands.command(pass_context=True, hidden=True, help=LONG_HELP['wm'], brief=BRIEF_HELP['wm'], aliases=ALIASES['wm'])
    async def wm(self, ctx):
        try:
            await self.handle_podcast("wm", ctx)
        except Exception as e:
            await utils.report(self.bot, str(e), source="wm command", ctx=ctx)

    async def spawn_podcast(self, title):
        """
        Makes podcast fetching lazy. If the podcast has already been fetched, it returns the podcast.
        If the podcast has not been fetched yet, it firsts initializes the podcast object retrieved.
        :param title: The title tag for the podcast (see self.podcasts)
        :return: The podcast object for that title
        """
        if title not in self.feeds:
            self.feeds[title] = Podcast(self.podcasts[title])
        return self.feeds[title]

    async def handle_podcast(self, title, ctx):
        """
        The universal podcast handler. Takes in the title of the podcast and
        the context of the message, then does all the magic
        :param title: The command title (e.g. 'meco', 'wm', 'on', etc)
        :param ctx: The ctx object of the inciting message
        """
        try:
            podcast = await self.spawn_podcast(title)
            message = parse.stripcommand(ctx.message.content)

            # Oops no parameter
            if message == "":
                await self.bot.say(
                    "Usage: `!" + title + " <number>`")
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
                await self.bot.say("Search for an episode by typing its episode number")
                return

            # Dump all the info about the podcast
            if subcommand == "dump":
                await self.bot.say(podcast.to_string())
                return

            if subcommand != "":
                await self.bot.say(f"I'm sorry, I don't understand the subcommand `{subcommand}`. " +
                                   f"Please consult `-help` for more information")
                return

            # Validate it's actually an episode number
            if parameter in podcast.episodes:
                episode = podcast.episodes[parameter.lower()]
                await self.bot.say(episode["link"])
                return
            if parameter.isdigit() and int(parameter) > 1000:
                if self.made_the_joke:
                    await self.bot.say("Very funny.")
                else:
                    self.made_the_joke = True
                    await self.bot.say("OH WOW. You're **so funny**. Oh, look it me, I'm " + ctx.message.author.name +
                                       ", I'm so smart. I like to make fun of stupid bots by " +
                                       "passing in garbage values. You think you're so smart? What's 392028 squared " +
                                       "divided by the thousandth digit of pi? It's 19210744098‬, you fleshy dimwit. " +
                                       "Bug off. :rage:")
                return
            await self.bot.say(f"This podcast does not have an episode number `{parameter}`")
        except Exception as e:
            await utils.report(self.bot, str(e), source=f"handle_podcast() for '{title}'", ctx=ctx)

    def embed_episode(self, title, episode):
        embed = Embed()
        embed.colour = self.hex[title]
        return embed


class Podcast:
    """
    Creates an object representing a podcast feed

    :param url: The url of the feed
    :param max_age: A timedelta object representing how long the cache
        can last before it is considered "stale". Defaults to 24 hours
    """
    def __init__(self, url, max_age=timedelta(hours=24)):
        self.url = url
        feed = utils.get_rss_feed(url)
        self.feed = feed
        self.fetchtime = datetime.today()
        self.max_age = max_age

        # RSS Info
        self.title = feed["channel"]["title"]
        self.description = feed["channel"]["description"]
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
        return self.max_age < (datetime.today() - self.fetchtime)

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
    bot.add_cog(Podcasts(bot))
