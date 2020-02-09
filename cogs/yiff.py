from discord.ext import commands
from discord import Embed
from constants import EMBED_COLORS
import parse
import utils


class Yiff:

    def __init__(self, bot):
        self.bot = bot
        self.fetchlimit = 6
        self._unlocked = True
        self._loop = bot.loop
        self._dbconn = bot.dbconn
        self._queue = utils.load_from_cache(bot.dbconn, "yiffURL", "").split(" ")

    def __len__(self):
        return len(self._queue)

    @commands.command(pass_context=True, hidden=True)
    async def yiff(self, ctx):
        """ Post a random furry porn picture from e621.net OwO """

        meme_quotes = ["glom", "OwO", "*notices bulge*", "What's this?",
                       "#OwO#", "UwU", "Want to see my fursona?", "*pounces on you*",
                       "Don't kinkshame me", "furries < scalies", "furries > scalies",
                       "I own three copies of Zootopia on Blu-Ray", "KNOT ME DADDY",
                       "Look how wide I can gape my anus...", "My fur suit is arriving next Monday"]
        try:
            message = parse.stripcommand(ctx.message.content)

            # You're on you're own here, pal
            if message in ["help", "-help"]:
                await self.bot.say("There is no help for any of us in this god forsaken world.")
                return

            # Yiff roulette
            if message == "\N{PISTOL}":
                num = 3
            else:
                num = 1

            # For dev reasons
            if message in ["test", "dev"]:
                target_channel = ctx.message.channel
            else:
                target_channel = self.bot.HERESY_CHANNEL

            # Let's play a little game
            for i in range(num):
                yiffembed = self.next()
                await self.bot.send_message(target_channel, utils.random_element(meme_quotes), embed=yiffembed)

        except Exception as e:
            await utils.report(self.bot, str(e), source="yiff command", ctx=ctx)

    def next(self):
        """ Returns an embed containing next url in the queue """
        if len(self) < self.fetchlimit and self._unlocked:
            self._loop.create_task(self._fetch())
        if len(self) == 0:
            return None
        url = self._queue.pop(0)
        utils.update_cache(self._dbconn, "yiffURL", " ".join(self._queue))
        yiffembed = Embed()
        yiffembed.set_image(url=url)
        yiffembed.colour = EMBED_COLORS["yiff"]
        return yiffembed

    async def _fetch(self):
        try:
            """ Returns urls of random image posts from aWebsite.net """
            if not self._unlocked:
                return
            self._unlocked = False  # Lock fetching
            api_url = "https://e621.net/post/index.json?limit=25&tags=order%3Arandom"

            [json, response] = await utils.get_json_with_get(api_url)

            if response is 200:
                for result in json:
                    url = result['file_url']
                    if self.bot.regex.is_url(url):
                        self._queue.append(url)
                    else:
                        await utils.flag(self.bot, "Yiff URL failed inspection", "`` {} ``".format(url))

            self._unlocked = True
            utils.update_cache(self._dbconn, "yiffURL", " ".join(self._queue))
        except Exception as e:
            await utils.report(self.bot, "Failed to fetch yiff urls \n" + str(e))


def setup(bot):
    bot.add_cog(Yiff(bot))
