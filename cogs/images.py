from discord.ext import commands
from discord import Embed
from urllib.parse import quote
from constants import *
import parse
import utils


class Images:

    """
    Several image querying commands that can show you some pictures to brighten your day

    meow
      Get a random picture of a cat

    nasa
      See the NASA Astronomy Picture of the Day

    picture
      Use Unsplash.com to see a random picture of some search term

    woof
      Get a random picture of a dog
    """

    def __init__(self, bot):
        self.bot = bot
        [meow_successes, meow_attempts] = utils.loadfromcache(bot.dbconn, "meowFailRate").split("/")
        self.meow_successes = int(meow_successes)
        self.meow_attempts = int(meow_attempts)
        self.next_meow_url = utils.loadfromcache(bot.dbconn, "meowURL")

    @commands.command(pass_context=True, help=LONG_HELP['meow'], brief=BRIEF_HELP['meow'], ALIASES=ALIASES['meow'])
    async def meow(self, ctx):
        try:
            if self.next_meow_url is None:
                await self.get_meow_url()
            if self.next_meow_url is None:
                await self.bot.say("This command is having a problem. Try again in a bit.")
                return
            embed = Embed().set_image(url=self.next_meow_url)
            embed.colour = EMBED_COLORS["meow"]
            await self.bot.say(embed=embed)
            await self.get_meow_url()
        except Exception as e:
            await utils.report(self.bot, str(e), source="Meow command", ctx=ctx)

    # Present the astronomy picture of the day
    @commands.command(pass_context=True, help=LONG_HELP['nasa'], brief=BRIEF_HELP['nasa'], aliases=ALIASES['nasa'])
    async def nasa(self, ctx):
        try:
            embed_icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/" +\
                         "1200px-NASA_logo.svg.png"
            api_url = "https://api.nasa.gov/planetary/apod?api_key=OSoqPlD9uDBXvXXpn4ybhFt1ulflqtmGtQnkLgAD"
            [json, status_code] = await utils.get_json_with_get(api_url)
            if status_code != 200:
                await utils.report(self.bot,
                                   "Error with !nasa, response code " + str(status_code) + "\n" + str(json),
                                   source="NASA APOD command", ctx=ctx)
                return
            if json['media_type'] == "video":
                await self.bot.say("**{}**\n{}\n{}".format(json['title'], json['explanation'], json['url']))
            else:
                embed = Embed().set_image(url=json['hdurl'])
                embed.title = json['title']
                embed.description = json['explanation']
                embed.set_footer(icon_url=embed_icon,
                                 text="NASA Astronomy Photo of the Day https://apod.nasa.gov/apod/astropix.html")
                embed.colour = EMBED_COLORS["nasa"]
                await self.bot.say(embed=embed)
        except Exception as e:
            await utils.report(self.bot, str(e), source="NASA APOD command", ctx=ctx)

    # Returns a random image of a snek
    @commands.command(pass_context=True, help=LONG_HELP['picture'], brief=BRIEF_HELP['picture'],
                      aliases=ALIASES['picture'])
    async def picture(self, ctx):
        try:
            unsplash_icon = ('https://image.winudf.com/v2/image/Y29tLmFwcHlidWlsZGVyLmFmYXFsZW8xMDIuVW5zcG' +
                             'xhc2hfaWNvbl8xNTMxMTA2MTg5XzA5OQ/icon.png?w=170&fakeurl=1&type=.png')
            headers = {
                "User-Agent": "suitsBot Discord Bot - https://github.com/DWCamp",
                "Authorization": "Client-ID " + self.bot.UNSPLASH_CLIENT_ID,
                "Accept-Version": "v1"
            }

            # Parse command
            content = parse.stripcommand(ctx.message.content)

            # Query defaults to a picture of a snake
            if content == "":
                query = "snake"
            else:
                query = quote(content)

            # Get the image URL
            json = await utils.get_json_with_get('https://api.unsplash.com/photos/random?query=' + query,
                                                 headers=headers)
            author_url = json[0]['user']['links']['html'] + "?utm_source=SuitsBot&utm_medium=referral"
            pic_embed = Embed().set_image(url=json[0]['urls']['full'])
            pic_embed.description = "Photo credit: " + author_url
            pic_embed.colour = EMBED_COLORS['picture']
            pic_embed.set_footer(icon_url=unsplash_icon,
                                 text="https://unsplash.com/?utm_source=SuitsBot&utm_medium=referral")
            await self.bot.say(embed=pic_embed)
        except Exception as e:
            await utils.report(self.bot, str(e), source="picture command", ctx=ctx)

    # Interfaces with the WolframAlpha API
    @commands.command(pass_context=True, help=LONG_HELP['woof'], brief=BRIEF_HELP['woof'], aliases=ALIASES['woof'])
    async def woof(self, ctx):
        try:
            # Get the image URL
            json = await utils.get_json_with_get("https://dog.ceo/api/breeds/image/random")

            # If there is an error
            if 'status' not in json[0].keys() or json[0]['status'] != "success":
                await self.bot.say("I have encountered an error. Please contact the bot creator")
                await utils.flag(self.bot, "Error with random dog api", description=json, ctx=ctx)
                return

            # Embed the image and send it
            woof_embed = Embed().set_image(url=json[0]['message'])
            woof_embed.colour = EMBED_COLORS['woof']
            await self.bot.say(embed=woof_embed)
        except Exception as e:
            await utils.report(self.bot, str(e), source="woof command", ctx=ctx)

    async def get_meow_url(self):
        """ Gets the url of a random image from aws.random.cat and caches the value """
        json = None
        status_code = 0
        counter = 0
        while status_code != 200 and counter < 100:
            [json, status_code] = await utils.get_json_with_get("http://aws.random.cat/meow")
            self.meow_attempts += 1
            counter += 1
        self.next_meow_url = json['file']
        self.meow_successes += 1
        utils.update_cache(self.bot.dbconn, "meowURL", json['file'])
        utils.update_cache(self.bot.dbconn, "meowFailRate", "{}/{}".format(self.meow_successes, self.meow_attempts))


def setup(bot):
    bot.add_cog(Images(bot))
