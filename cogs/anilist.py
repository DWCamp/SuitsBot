from discord import Embed
from discord.ext import commands
from discord.ext.commands import Cog
from constants import *
import parse
import utils

EMBED_COLOR = EMBED_COLORS["anime"]


class Anilist(Cog):
    """
    Anilist.co API query engine

    Queries the Anilist.co API for information about anime characters and shows.
    To support memes and reduce finiky results, the bot holds several synonyms for
    characters and shows which will have the bot search for a different specific
    string when given another query (e.g. 'KLK' becomes 'Kill la Kill' or 'Goku'
    becomes 'Son Goku'). This synonym list can be modified by users using CLI
    arguments. The arguments are listed below:

    "-help": Displays a help message
    "-add": Adds an entry to the synonym list
    "-char": Searches the database for a character instead of a show
    "-info": Shows the complete list of data returned from the API
    "-ls": Lists the anime synonym table
    "-raw": Disables synonym correction for a search
    "-remove": Removes an entry from the synonym list
    """

    def __init__(self, bot):
        self.bot = bot
        self.anime_query = """
    query ($title: String) {
        Media (search: $title, type: ANIME) {
            averageScore
            characters(role: MAIN) {
              nodes {
                name {
                  first
                  last
                  native
                }
              }
            }
            coverImage {
              medium
            }
            description
            duration
            endDate {
              year
              month
              day
            }
            episodes
            format
            genres
            siteUrl
            source
            startDate {
              year
              month
              day
            }
            status
            studios(isMain: true) {
                nodes {
                  name
                }
            }
            tags {
              name
              isGeneralSpoiler
            }
            title {
              english
              romaji
            }
        }
    }
    """
        self.char_query = """
    query ($name: String) {
        Character (search: $name) {
            description
            image {
              large
            }
            media(sort: TITLE_ENGLISH, type: ANIME) {
              nodes {
                title {
                  english
                  romaji
                }
              }
            }
            name {
              first
              last
              native
              alternative
            }
            siteUrl
        }
    }
    """
        self.anime_synonyms = {}
        self.character_synonyms = {}
        self.api_url = 'https://graphql.anilist.co'
        self.loadsynonyms()

    @commands.command(help=LONG_HELP['anime'], brief=BRIEF_HELP['anime'], aliases=ALIASES['anime'])
    async def anime(self, ctx):
        """
        anime command

        Parameters
        ------------
        ctx : discord.context
            The message context object
        """

        try:
            # Gets the arguments from the message
            (arguments, searchterm) = parse.args(ctx.message.content)

            if "dev" in arguments:
                await ctx.send(self.character_synonyms)
                return

            # Explain all the arguments to the user
            if "help" in arguments or searchterm == "help":
                title = "!anime - User Guide"
                description = (
                            "A search tool for anime shows and characters. This command uses the AniList.co API to " +
                            "return details on the search term provided for the show/character whose name is provide " +
                            "with the command (e.g. `!anime Kill la Kill`). For shows, information like a show " +
                            "description, air date, rating, and genre information will be returned. For characters, " +
                            "the bot provides a description, their nicknames, and the media they've been in.\n\nThe " +
                            "bot uses a synonym engine to make it easier to find popular characters and allow for " +
                            "searching for entries using unofficial nicknames (e.g. `!anime klk` redirects to " +
                            "`!anime Kill la Kill`). The bot's synonym table can be modified by users to allow for a " +
                            "more complete table of synonyms")
                helpdict = {"<search>": "Searches the database for an anime",
                            "-help": "Displays this message",
                            "-add [<Synonym>] <Value>": ("Adds a synonym to the list. Will search for " +
                                                         "`Value` when a user types `Synonym`. Can be used " +
                                                         "with the `-char` command to create character " +
                                                         "synonyms. `<Synonym>` also supports semicolon-" +
                                                         "delineated lists"),
                            "-char <search>": "Searches the database for a character page",
                            "-info <search>": ("Shows the complete details for an anime. Has no effect on " +
                                               "`-char` searches"),
                            "-ls": ("Lists the anime synonym table. If used with the `-char` command, it " +
                                    "lists the character synonym table"),
                            "-raw <search>": "Disables synonym correction for search terms",
                            "-remove <Search Value>": ("Removes a synonym from the list. Can be used with " +
                                                       "the `-char` command to remove character synonyms")}
                await ctx.send(embed=utils.embedfromdict(helpdict,
                                                             title=title,
                                                             description=description,
                                                             thumbnail_url=COMMAND_THUMBNAILS["anime"]))
                return

            if "ls" in arguments:
                if "char" in arguments:
                    searchdict = self.character_synonyms
                    title = "Character name synonyms"
                else:
                    searchdict = self.anime_synonyms
                    title = "Anime title synonyms"
                message = ""
                for changeto in sorted(list(searchdict.keys())):
                    message += "**" + changeto + "** <- " + ", ".join(searchdict[changeto]) + "\n"
                embed = Embed()
                embed.title = title
                embed.description = utils.trimtolength(message, 2040)
                embed.colour = EMBED_COLORS["anime"]
                await ctx.send(embed=embed)
                return

            if "add" in arguments and "remove" in arguments:
                await ctx.send("I don't know how you possibly expect me to both add and " +
                                   "remove a synonym in the same command")

            if "char" in arguments:
                synonymdict = self.character_synonyms
                searchtype = "character"
            else:
                synonymdict = self.anime_synonyms
                searchtype = "anime"

            # Add search synonym
            if "add" in arguments:
                tag_kv = parse.key_value(searchterm)
                if tag_kv[0] is None:
                    errormessages = {
                        "EMPTY KEY": "There was no synonym for the search value",
                        "UNCLOSED KEY": "You didn't close your brackets",
                        "NO VALUE": "There was no search value to save for the synonym",
                        "WHITESPACE KEY": (
                                    "Just because this bot is written in Python does not mean whitespace is an " +
                                    "acceptable synonym"),
                        "KEY STARTS WITH -": (
                                    "The `-` character denotes the start of an argument and cannot be used to " +
                                    "start a synonym")}
                    await ctx.send(errormessages[tag_kv[1]])
                    return
                changefrom = tag_kv[0].lower()
                changeto = tag_kv[1]
                collision = checkforexistingsynonym(changefrom, synonymdict)
                if collision is None:
                    if changeto not in synonymdict.keys():
                        synonymdict[changeto] = list()
                    changefromlist = changefrom.split(";")
                    for element in changefromlist:
                        synonymdict[changeto].append(element.strip())
                        self.add_synonym(searchtype.upper(), changeto, element)
                    await ctx.send("All " + searchtype + " searches for `" + "` or `".join(changefromlist) +
                                       "` will now correct to `" + changeto + "`")
                else:
                    await ctx.send("The synonym `` {} `` already corrects to `` {} ``. Pick a different " +
                                       "word/phrase or remove the existing synonym with the command " +
                                       "``!anime -remove {} ``".format(changefrom, collision, changefrom))
                return

            # Remove search synonym
            if "remove" in arguments:
                correction = checkforexistingsynonym(searchterm, synonymdict)
                if correction is not None:
                    synonymdict[correction].remove(searchterm)
                    if len(synonymdict[correction]) == 0:
                        del synonymdict[correction]
                    self.remove_synonym(searchtype.upper(), searchterm)
                    await ctx.send("Alright, `" + searchterm + "` will no longer correct to `" + correction +
                                       "` for " + searchtype + " searches")
                else:
                    await ctx.send(("The synonym you searched for does not exist. Check your use " +
                                        "(or lack thereof) of the `-char` command, or use the `-ls` command to check " +
                                        "that everything is spelled correctly"))
                return

            if searchterm == "":
                await ctx.send("I don't see a search term to look up. Type `!anime -help` for a user guide")
                return

            embedgenerator = None
            if "char" in arguments:
                if "raw" not in arguments:
                    for key in self.character_synonyms.keys():
                        if searchterm.lower() in self.character_synonyms[key]:
                            searchterm = key
                char_var = {'name': searchterm}
                [json, status] = await utils.get_json_with_post(self.api_url,
                                                                json={'query': self.char_query, 'variables': char_var})
                if "json" in arguments:
                    await ctx.send(utils.trimtolength(json, 2000))
                if status == 200:
                    embedgenerator = Character(json['data']['Character'])
            else:
                if "raw" not in arguments:
                    for key in self.anime_synonyms.keys():
                        if searchterm.lower() in self.anime_synonyms[key]:
                            searchterm = key
                anime_var = {'title': searchterm}
                [json, status] = await utils.get_json_with_post(self.api_url,
                                                                json={'query': self.anime_query,
                                                                      'variables': anime_var})
                if "json" in arguments:
                    await ctx.send(utils.trimtolength(json, 2000))
                if status == 200:
                    embedgenerator = Anime(json['data']['Media'])

            if status != 200:
                if status == 500:
                    await utils.flag(self.bot,
                                     "500 Server Error on search term " + searchterm,
                                     description=str(json),
                                     ctx=ctx)
                    await ctx.send(
                        "`500 Server Error`. The AniList servers had a brief hiccup. Try again in a little bit")
                elif status == 404:
                    await utils.flag(self.bot,
                                     "Failed to find result for search term " + searchterm,
                                     description=str(json),
                                     ctx=ctx)
                    await ctx.send("I found no results for `" + searchterm + "`")
                elif status == 400:
                    await utils.report(self.bot,
                                       str(json),
                                       source="Error in `!anime` search for term " + searchterm,
                                       ctx=ctx)
                    await ctx.send("The bot made an error. My bad. A bug report has been automatically submitted")
                else:
                    await utils.report(self.bot,
                                       str(json),
                                       source="Unknown Error Type",
                                       ctx=ctx)
                    await ctx.send("Something went wrong and I don't know why")
                return

            if "info" in arguments:
                await ctx.send(embed=embedgenerator.info_embed())
            else:
                await ctx.send(embed=embedgenerator.embed())
        except Exception as e:
            await utils.report(self.bot, str(e), source="!anime command", ctx=ctx)

    def loadsynonyms(self):
        """ Load !anime synonym table from database """
        query = "SELECT * FROM Synonyms"
        cursor = self.bot.dbconn.execute(query)
        for (synonym_type, change_to, change_from) in cursor:
            change_from = change_from.decode("utf-8")
            change_to = change_to.decode("utf-8")
            if synonym_type == "ANIME":
                if change_to not in self.anime_synonyms.keys():
                    self.anime_synonyms[change_to] = list()
                self.anime_synonyms[change_to].append(change_from)
            elif synonym_type == "CHARACTER":
                if change_to not in self.character_synonyms.keys():
                    self.character_synonyms[change_to] = list()
                self.character_synonyms[change_to].append(change_from)

    def add_synonym(self, synonym_type, change_to, change_from):
        """ Adds a synonym from the database

        Parameters
        -------------
        synonym_type : str
            The string representing the type of synonym it is
            "ANIME" - A synonym for a show
            "CHARACTER" - A synonym for a character
        change_to : str
            The string which replaces the original search term
        change_from : str
            The search term which is replaced
        """
        self.bot.dbconn.ensure_sql_connection()
        add_command = "INSERT INTO Synonyms VALUES (%s, %s, %s)"
        add_data = (synonym_type, change_to, change_from)
        self.bot.dbconn.execute(add_command, add_data)
        self.bot.dbconn.commit()

    def remove_synonym(self, synonym_type, change_from):
        """ Removes a synonym from the database

        Parameters
        -------------
        synonym_type : str
            The string representing the type of synonym it is
            "ANIME" - A synonym for a show
            "CHARACTER" - A synonym for a character
        change_from : str
            The search term that will no longer be corrected
        """
        self.bot.dbconn.ensure_sql_connection()
        delete_command = "DELETE FROM Synonyms WHERE Type=%s AND ChangeFrom=%s"
        delete_data = (synonym_type, change_from)
        self.bot.dbconn.execute(delete_command, delete_data)
        self.bot.dbconn.commit()


class Anime:
    """
    Anime embed generator

    Stores the data from an AniList.co query about a show and produces 
    different embeds with the information

    Parameters
    ------------
    media : dict[str:str]
        A JSON dictionary retrieved from AniList containing the show's
        properties. 
    """
    def __init__(self, media):

        self.characters = list()
        for character in media['characters']['nodes']:
            if character['name']['first'] is None:
                self.characters.append(character['name']['native'])
            elif character['name']['last'] is None:
                self.characters.append(character['name']['first'])
            else:
                self.characters.append(character['name']['first'] + " " + 
                                       character['name']['last'])
        if media['description'] is None:
            self.description = "*(This media has no description)*"
        else:
            self.description = media['description'].replace("<br>", "")
        self.duration = media['duration']
        self.end_date = (str(media['endDate']['year']) + "/" +
                         _format_date(media['endDate']['month']) + "/" +
                         _format_date(media['endDate']['day']))
        self.episodes = media['episodes']
        if len(media['genres']) > 0:
            self.genres = ", ".join(media['genres'])
        else:
            self.genres = None
        self.image = media['coverImage']['medium']
        self.score = media['averageScore']

        if media['source'] is not None:
            not_capitalized = ["a", "an", "the", "for", "and", "nor", "but", "or", "yet", "so"]
            split_source = media['source'].split("_")
            for i, word in enumerate(split_source):
                if i == 0 or word not in not_capitalized:
                    split_source[i] = word[:1].upper() + word[1:]
            self.source = " ".join(split_source)
        else:
            self.source = None

        self.startDate = (_format_date(media['startDate']['year']) + "/"
                          + _format_date(media['startDate']['month']) + "/"
                          + _format_date(media['startDate']['day']))
        self.status = media['status'].title()
        self.studios = list()
        for studio in media['studios']['nodes']:
            self.studios.append(studio['name'])
        self.tags = list()
        for tag in media['tags']:
            if not tag['isGeneralSpoiler']:
                self.tags.append(tag['name'])
        self.url = media['siteUrl']

        # ------------ Enum Values

        if media['title']['english'] is None:
            if media['title']['romaji'] is None:
                self.title = "<None>"
            else:
                self.title = media['title']['romaji']
        else:
            self.title = media['title']['english']

        # Parse enum value to normal looking string
        if media['format'] == "TV_SHORT":
            self.format = "TV Short"
        elif media['format'] == "MOVIE":
            self.format = "Movie"
        elif media['format'] == "SPECIAL":
            self.format = "Special"
        elif media['format'] == "MUSIC":
            self.format = "Music video"
        else:
            self.format = media['format']

    def embed(self):
        """ Default embed generator
        Creates an embed object from a summary of the object's data and returns it
        """
        anime_embed = Embed()
        if self.image is not None:
            anime_embed.set_thumbnail(url=self.image)
        anime_embed.title = self.title
        anime_embed.description = utils.trimtolength(self.description, 2047)
        if self.genres is not None:
            anime_embed.add_field(name="Genre", value=self.genres)
        if self.score is None:
            anime_embed.add_field(name="Score", value="--/100")
        else:
            anime_embed.add_field(name="Score", value=str(self.score) + "/100")
        anime_embed.url = self.url
        anime_embed.colour = EMBED_COLOR
        anime_embed.set_footer(text="Data retrieved using the https://anilist.co API",
                               icon_url="https://anilist.co/img/icons/logo_full.png")
        return anime_embed

    def info_embed(self):
        """ Verbose embed generator
        Creates an embed from the entire set of the object's data and returns it """
        anime_embed = Embed().set_thumbnail(url=self.image)
        anime_embed.title = self.title
        if self.format is not None:
            anime_embed.add_field(name="Format", value=self.format)
        if self.source is not None:
            anime_embed.add_field(name="Source", value=self.source)
        if self.format == "TV" and self.episodes is not None:
            anime_embed.add_field(name="Episodes", value=self.episodes)
        if self.duration is not None:
            anime_embed.add_field(name="Duration", value=str(self.duration) + " minutes")

        if self.format == "TV":
            if self.startDate is not None:
                anime_embed.add_field(name="Start Date", value=self.startDate)
            if self.status == "Releasing":
                anime_embed.add_field(name="Status", value="Currently Airing")
            elif self.status == "Finished":
                anime_embed.add_field(name="End Date", value=self.end_date)
        else:
            if self.startDate is not None:
                anime_embed.add_field(name="Release Date", value=self.startDate)

        if len(self.studios) == 1:
            anime_embed.add_field(name="Studio", value=self.studios[0])
        elif len(self.studios) > 1:
            anime_embed.add_field(name="Studios", value=", ".join(self.studios))

        anime_embed.add_field(name="Score", value=str(self.score) + "/100")

        if len(self.characters) > 0:
            anime_embed.add_field(name="Main Characters", value=", ".join(self.characters), inline=False)

        if len(self.tags) > 0:
            anime_embed.add_field(name="Tags", value=", ".join(self.tags), inline=False)

        anime_embed.url = self.url
        anime_embed.color = EMBED_COLOR
        anime_embed.set_footer(text="Data retrieved using the https://anilist.co API",
                               icon_url="https://anilist.co/img/icons/logo_full.png")
        return anime_embed


class Character:
    """
    Anime embed generator

    Stores the data from an AniList.co query about a character and 
    produces different embeds with the information

    Parameters
    ------------
    character : dict[str:str]
        A JSON dictionary retrieved from AniList containing the 
        character's properties. 
    """
    def __init__(self, character):
        if character['name']['first'] is None:
            self.name = character['name']['native']
        elif character['name']['last'] is None:
            self.name = character['name']['first']
        else:
            self.name = character['name']['first'] + " " + character['name']['last']
        self.image = character['image']['large']
        self.native = character['name']['native']
        self.alternative = character['name']['alternative']
        self.description = utils.trimtolength(character['description'].replace("~!", "").replace("!~", ""), 2047)
        self.media = list()
        for media in character['media']['nodes']:
            if media['title']['english'] is None:
                self.media.append(media['title']['romaji'])
            else:
                self.media.append(media['title']['romaji'])
        self.url = character['siteUrl']

    def embed(self):
        """ Default embed generator
        Creates an embed object from the object's data and returns it
        """
        character_embed = Embed().set_thumbnail(url=self.image)
        character_embed.title = self.name
        character_embed.description = self.description
        if self.native is not None:
            character_embed.add_field(name="Name in native language", value=self.native)
        if len(self.alternative) > 0 and self.alternative[0] != "":
            character_embed.add_field(name="Alternative Names", value=", ".join(self.alternative))
        if len(self.media) > 0:
            character_embed.add_field(name="Appeared in", value=utils.trimtolength(", ".join(self.media), 2000))
        character_embed.url = self.url
        character_embed.colour = EMBED_COLOR
        character_embed.set_footer(text="Data retrieved using the https://anilist.co API",
                                   icon_url="https://anilist.co/img/icons/logo_full.png")
        return character_embed

    def info_embed(self):
        """
        Returns an embed containing the character's data
        Only included to make the class interchangable with Anime
        """
        return self.embed()


def _format_date(date):
    """ Formats a number for a date printout
    Pads the number to two digits with a trailing zero
    If number is None, returns '--' """
    if date is None:
        return "--"
    elif date < 10:
        return "0" + str(date)
    return str(date)


def checkforexistingsynonym(newterm, synonym_dict):
    for term in synonym_dict.keys():
        if newterm in synonym_dict[term]:
            return term
    return None


def setup(bot):
    bot.add_cog(Anilist(bot))
