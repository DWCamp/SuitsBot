import random
from discord.ext import commands
from discord import Embed
from urllib.parse import quote
from constants import *
from credentials import tokens
import parse
import utils
from stringcache import StringCache


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
        self.meow_cache = CatCache(bot)
        self.gritty_urls = ["https://media.newyorker.com/photos/5bbd10430cdf452cf93ca22f/master/w_1023,c_limit/Crouch-Gritty.jpg",
                            "https://media.phillyvoice.com/media/images/Dn9LBKjU8AAaIYO.jpg-large.ad646704.fill-735x490.jpg",
                            "https://i.imgflip.com/2imt3r.gif",
                            "https://pbs.twimg.com/media/Dn591_aXsAE0rvt?format=jpg",
                            "https://media.giphy.com/media/1AgZiwuFdlt8iPSAmt/giphy.gif",
                            "https://video-images.vice.com/_uncategorized/1573284466885-Gritty_Vice_Mascots_Leaman_548_FINAL.jpeg",
                            "https://video-images.vice.com/_uncategorized/1573284489524-Gritty_Vice_Mascots_Leaman_309_FINAL.jpeg",
                            ("https://mondrian.mashable.com/uploads%252Fcard%252Fimage%252F887937%252F57b3613c-304a-" +
                             "4078-bbb2-d7f8fa82dc75.jpg%252F950x534__filters%253Aquality%252880%2529.jpg?signature=" +
                             "RGtrrSLtdBTz61_erR9HRmtWfAc=&source=https%3A%2F%2Fblueprint-api-production.s3.amazonaws.com"),
                            "https://d.newsweek.com/en/full/1137055/dn3mx-bxuainf87.webp?w=737&f=c4214da3e318d1ce6f48f611bcdd346e",
                            ("https://www.nbcsports.com/philadelphia/sites/csnphilly/files/styles/article_hero_image/" +
                             "public/2019/02/23/022319gritty1550970956833_7000k_1920x1080_1447358019700.jpg?itok=iOjK3zeQ"),
                            "https://www.phillymag.com/wp-content/uploads/sites/3/2018/11/gritty-time-magazine-person-of-the-year.jpg",
                            ("https://www.si.com/.image/ar_16:9%2Cc_fill%2Ccs_srgb%2Cfl_progressive%2Cg_faces:" +
                             "center%2Cq_auto:good%2Cw_768/MTY4MDMxMjg0NTEwNzk1MTM2/gritty-qajpg.jpg"),
                            ("https://cdn.vox-cdn.com/thumbor/7cFKvPx44nNr7GhfSQBQlxvOATs=/0x0:2048x1536/1200x800/" +
                             "filters:focal(788x383:1114x709)/cdn.vox-cdn.com/uploads/chorus_image/image/64007338/GrittyPride.0.jpg"),
                            "https://usatftw.files.wordpress.com/2019/10/gritty.jpg?w=1000&h=600&crop=1",
                            "https://i.redd.it/ae2e968kxfx11.jpg",
                            "https://i.redd.it/g3cw8vlq0d121.jpg",
                            "https://i.redd.it/e15pjejpfdo21.jpg",
                            "https://i.redd.it/x5we704ijv521.png",
                            "https://i.redd.it/0fwwueqlidz11.jpg",
                            "https://i.redd.it/qgznzo117zt11.jpg",
                            "https://giant.gfycat.com/SlightLeanCats.webm",
                            "https://i.imgur.com/FMhCMbw.jpg",
                            "https://i.redd.it/1cllnxyk7xr21.jpg",
                            "https://i.redd.it/xdpr7uctd2a31.jpg",
                            "https://i.redd.it/oq88wl9x33921.jpg",
                            "https://i.redd.it/pve7gkrgmet11.jpg",
                            "https://i.imgur.com/2BrTP5q.jpg"]

    @commands.command(pass_context=True, help=LONG_HELP['gritty'], brief=BRIEF_HELP['gritty'], aliases=ALIASES['gritty'])
    async def gritty(self, ctx):
        try:
            url = self.get_gritty_url()
            embed = Embed().set_image(url=url)
            embed.colour = EMBED_COLORS["gritty"]
            await self.bot.say(embed=embed)
        except Exception as e:
            await utils.report(self.bot, str(e), source="Gritty command", ctx=ctx)

    @commands.command(pass_context=True, help=LONG_HELP['meow'], brief=BRIEF_HELP['meow'], aliases=ALIASES['meow'])
    async def meow(self, ctx):
        try:
            meow_url = self.meow_cache.next()
            if meow_url:
                embed = Embed().set_image(url=meow_url)
                embed.colour = EMBED_COLORS["meow"]
                await self.bot.say(embed=embed)
            else:
                await self.bot.say("I'm sorry, I don't have a cat photo at the moment. Please try again in a minute")
        except Exception as e:
            await utils.report(self.bot, str(e), source="Meow command", ctx=ctx)

    # Present the astronomy picture of the day
    @commands.command(pass_context=True, help=LONG_HELP['nasa'], brief=BRIEF_HELP['nasa'], aliases=ALIASES['nasa'])
    async def nasa(self, ctx):
        try:
            apod_post = get_apod_embed()
            if isinstance(apod_post, str):
                await self.bot(apod_post)
            else:
                await self.bot(embed=apod_post)
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
                "Authorization": "Client-ID " + tokens["UNSPLASH_CLIENT_ID"],
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

    def get_gritty_url(self):
        """Gets a random Gritty url"""
        return random.choice(self.gritty_urls)


class CatCache(StringCache):
    """ An implementation of the StringCache for cat photos """
    def __init__(self, bot):
        StringCache.__init__(self, bot, cache_id="meow")

    async def gather(self):
        """ Fetches cat urls from thecatapi.com """
        json = await utils.get_json_with_get("https://api.thecatapi.com/v1/images/search?limit=10",
                                             headers={"x-api-token": tokens["THECATAPI"]})
        return [result["url"] for result in json[0]]


async def get_apod_embed():
    """
    Get's the day's APOD and returns an entity which can be posted
     This entity will either be an embed with the picture and its
     description or a string (if the post is a video) containing
     a message about the post. Videos need to be sent as strings
     since videos cannot be put into containers

    :return: Either an embed (for images) or a string (for videos)
    """
    embed_icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/" + \
                 "1200px-NASA_logo.svg.png"
    api_url = f"https://api.nasa.gov/planetary/apod?api_key={tokens['APOD']}"
    [json, status_code] = await utils.get_json_with_get(api_url)
    if status_code != 200:
        raise RuntimeError(f"Failed to retrieve APOD, status code: {status_code}")
    if json['media_type'] == "video":
        return f"**{json['title']}**\n{json['explanation']}\n{json['url']}"
    embed = Embed().set_image(url=json['hdurl'])
    embed.title = json['title']
    date = json["date"][2:].replace("-", "")
    embed.url = f"https://apod.nasa.gov/apod/ap{date}.html"
    embed.description = json['explanation']
    embed.set_footer(icon_url=embed_icon,
                     text="NASA Astronomy Photo of the Day https://apod.nasa.gov/apod/astropix.html")
    embed.colour = EMBED_COLORS["nasa"]
    return embed


def setup(bot):
    bot.add_cog(Images(bot))
