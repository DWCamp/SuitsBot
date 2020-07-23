import aiohttp
from urllib.parse import quote
from discord.ext import commands
from discord.ext.commands import Cog
from discord import Embed
from constants import *
import parse
import utils
from config import credentials
from config.local_config import *


class WebQueries(Cog):

    def __init__(self, bot):
        self.bot = bot

    # Searches urban dictionary for a term
    @commands.command(help=LONG_HELP['ud'], brief=BRIEF_HELP['ud'], aliases=ALIASES['ud'])
    async def ud(self, ctx):
        # Removes the brackets around words, which UD puts around words in definitions
        # and examples that have their own definitions
        def strip_brackets(text):
            text = text.replace("[", " ").replace("]", "")
            return text

        """ Query the UrbanDictionary API """
        try:
            # removes the invocation portion of the message
            message = parse.stripcommand(ctx.message.content)

            max_definitions = 4

            # Reject empty messages
            if message == "":
                await ctx.send("You must pass in a term to get a definition")
                return

            # Query the API and post its response
            url = "http://api.urbandictionary.com/v0/define?term=" + quote(message)
            (ud_json, response) = await utils.get_json_with_get(url)
            if response is not 200:
                await ctx.send("There was an error processing your request. I apologize for the inconvenience.")
                return
            if len(ud_json["list"]) > 0:
                ud_embed = Embed()
                ud_embed.set_footer(text="UrbanDictionary",
                                    icon_url="https://firebounty.com/image/635-urban-dictionary")
                counter = 0
                first_result = ""
                while counter < len(ud_json["list"]) and counter <= max_definitions:
                    definition = ud_json["list"][counter]
                    if counter == 0:
                        first_result = definition["word"]
                        ud_embed.title = utils.trimtolength(first_result, 256).capitalize()
                    if definition["word"] == first_result:
                        def_text = definition["definition"].replace("*", "\\*")
                        example_text = "**Example: " + definition["example"].replace("*", "\\*") + "**"
                        ud_embed.add_field(name=str(counter + 1),
                                           value=utils.trimtolength(strip_brackets(def_text + "\n\n" + example_text),
                                                                    1024),
                                           inline=False)
                    counter += 1
                ud_embed.colour = EMBED_COLORS['ud']  # Make the embed white

                await ctx.send(embed=ud_embed)
            else:
                await ctx.send("I can't find any UrbanDictionary results for `" + message + "`")
        except Exception as e:
            await utils.report(self.bot, str(e), source="ud command", ctx=ctx)

    # Returns a description of an item from Wikipedia
    @commands.command(help=LONG_HELP['wiki'], brief=BRIEF_HELP['wiki'], aliases=ALIASES['wiki'])
    async def wiki(self, ctx):
        # ---------------------------------------------------- HELPER METHODS

        # Find an article with a matching title
        async def search_for_term(term):
            wiki_search_url = ("http://en.wikipedia.org/w/api.php?action=query&format=json" +
                               "&prop=&list=search&titles=&srsearch=" + quote(term))
            # Looks for articles matching the search term
            wiki_search_json = await utils.get_json_with_get(wiki_search_url)
            if wiki_search_json[0]['query']['searchinfo']['totalhits'] == 0:
                return None
            return wiki_search_json[0]['query']['search'][0]['title']

        # Gets the details of an article with an exact URL title (not always the same as the article title)
        # Returns a tuple of the article's title, its extract, and a brief description of the subject
        # Returns None if no article was found or the result has no extract
        async def query_article(querytitle):
            # Makes the title URL friendly
            quoted_article_title = quote(querytitle)
            wiki_query_url = ("http://en.wikipedia.org/w/api.php?action=query&format=json" +
                              "&prop=info%7Cextracts%7Cdescription&titles=" + quoted_article_title +
                              "&exlimit=max&explaintext=1&exsectionformat=plain")
            # Gets the article details
            response = await utils.get_json_with_get(wiki_query_url)
            # If Wikipedia found nothing
            if "-1" in response[0]['query']['pages'].keys():
                return None
            # Gets the first result
            response = list(response[0]['query']['pages'].values())[0]
            # If the returned result isn't usable
            if "extract" not in response.keys():
                await utils.report(self.bot,
                                   utils.trimtolength(response, 2000),
                                   source="Wiki command found no useful article", ctx=ctx)
                return None
            response_title = response['title']
            response_extract = response['extract']
            if 'description' in response.keys():
                response_description = response['description']
            else:
                response_description = None
            return response_title, response_extract, response_description

        # ---------------------------------------------------- COMMAND LOGIC

        try:
            # WIKI -------------------------------- SET-UP

            (arguments, search_term) = parse.args(ctx.message.content)

            # WIKI -------------------------------- ARGUMENTS

            # Act on arguments
            if "help" in arguments:  # provides help using this command
                title = "`!wiki` User Guide"
                description = "Wikipedia search engine. Searches wikipedia for an article with the title provided " \
                              "and returns the opening section or the full article text. Additionally, it can " \
                              "return the sections of an article or the text of a designated section."
                helpdict = {
                    "-help": "Displays this user guide. Gives instructions on how to use the command and its features",
                    "-full <title>": "Displays the full extract of the article, up to the embed character limit"}
                await ctx.send(embed=utils.embedfromdict(helpdict,
                                                             title=title,
                                                             description=description,
                                                             thumbnail_url=COMMAND_THUMBNAILS["wiki"]))
                return

            # Performs article search
            if search_term == "":
                await ctx.send("I need a term to search")
                return
            article_title = await search_for_term(search_term)
            if article_title is None:
                await ctx.send("I found no articles matching the term '" + search_term + "'")
                return

            # Shows the text of the article searched for
            [title, extract, summary] = await query_article(article_title)
            wiki_embed = Embed()
            wiki_embed.title = title
            wiki_embed.set_footer(text="Wikipedia",
                                  icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/"
                                           "Wikipedia-logo-v2.svg/800px-Wikipedia-logo-v2.svg.png")
            if "full" in arguments or "f" in arguments:
                description = utils.trimtolength(extract, 2048)
            else:
                description = utils.trimtolength(extract[:extract.find("\n")], 2048)
            wiki_embed.description = description
            wiki_embed.add_field(name="Summary",
                                 value=summary,
                                 inline=False)
            wiki_embed.add_field(name="Full Article",
                                 value="http://en.wikipedia.org/wiki/" + quote(title),
                                 inline=False)
            wiki_embed.colour = EMBED_COLORS['wiki']  # Make the embed white
            await ctx.send(embed=wiki_embed)
        except Exception as e:
            await utils.report(self.bot, str(e), source="Wiki command", ctx=ctx)

    @commands.command(help=LONG_HELP['wolf'], brief=BRIEF_HELP['wolf'], aliases=ALIASES['wolf'])
    async def wolf(self, ctx):
        """ Query the Simple Wolfram|Alpha API """
        try:
            # removes the "!wolf" portion of the message
            message = parse.stripcommand(ctx.message.content)

            # Reject empty messages
            if message == "":
                await ctx.send("You must pass in a question to get a response")
                return

            # Query the API and post its response
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get("http://api.wolframalpha.com/v1/result?appid=" +
                                       credentials.tokens["WOLFRAMALPHA_APPID"] + "&i=" + quote(message)) as resp:
                    if resp.status is 501:
                        await ctx.send("WolframAlpha could not understand the question '{}' because {}"
                                           .format(message, resp.reason))
                        return
                    data = await resp.content.read()
                    await ctx.send(data.decode("utf-8"))
        except Exception as e:
            await utils.report(self.bot, str(e), source="wolf command", ctx=ctx)

    @commands.command(help=LONG_HELP['youtube'], brief=BRIEF_HELP['youtube'],
                      aliases=ALIASES['youtube'])
    async def youtube(self, ctx):
        """ Search Youtube for a video """
        try:
            # YOUTUBE -------------------------------- SET-UP

            (arguments, query) = parse.args(ctx.message.content)

            api_url = "https://www.googleapis.com/youtube/v3/search"
            params = {"part": "id, snippet",
                      "maxResults": 5,
                      "q": query,
                      "relevanceLanguage": "en-us",
                      "type": "video",
                      "videoEmbeddable": "true",
                      "fields": "items(id/videoId,snippet/title)",
                      "key": credentials.tokens["YOUTUBE_KEY"]}

            # Get the top 5 search results for a given query
            [json, resp_code] = await utils.get_json_with_get(api_url, params=params)
            if resp_code != 200:
                await utils.report(self.bot,
                                   "Failed to find video with search '" + query + "'",
                                   source="youtube command",
                                   ctx=ctx)
                await ctx.send("There was a problem retrieving that video")
                return

            # YOUTUBE -------------------------------- ARGUMENTS

            # User asks for a list of results and picks with an emoji reaction
            if "r" in arguments:
                emoji_list = ['1\u20e3', '2\u20e3', '3\u20e3', '4\u20e3', '5\u20e3']
                description = ""
                for (index, result) in enumerate(json['items']):
                    description += "**" + str(index + 1) + "**. " + result['snippet']['title'] + "\n"
                search_embed = Embed()
                search_embed.colour = EMBED_COLORS['youtube']
                search_embed.title = "Search results"
                search_embed.description = description
                search_message = await ctx.send(embed=search_embed)
                for emoji in emoji_list:
                    await self.bot.add_reaction(search_message, emoji)
                response = await self.bot.wait_for_reaction(emoji_list,
                                                            timeout=30,
                                                            user=ctx.author,
                                                            message=search_message)

                # Reject response if it takes too long
                if response is None:
                    search_embed.description = "(Response timeout)"
                    await self.bot.edit_message(search_message, embed=search_embed)
                else:
                    # Delete the results embed and post the youtube link
                    await self.bot.delete_message(search_message)
                    index = emoji_list.index(response[0].emoji)
                    video_id = json['items'][index]['id']['videoId']
                    title = json['items'][index]['snippet']['title']
                    await ctx.send("**" + title + "**\nhttps://www.youtube.com/watch?v=" + video_id)
            # Otherwise just provide the top result
            else:
                video_id = json['items'][0]['id']['videoId']
                title = json['items'][0]['snippet']['title']
                await ctx.send("**" + title + "**\nhttps://www.youtube.com/watch?v=" + video_id)
        except Exception as e:
            await utils.report(self.bot, str(e), source="youtube command", ctx=ctx)


def setup(bot):
    bot.add_cog(WebQueries(bot))
