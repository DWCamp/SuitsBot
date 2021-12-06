from discord.ext import commands
from discord.ext.commands import Cog
from constants import *
import parse
import utils


class Tags(Cog):
    """
    Call and response

    Allows users to pair a key and value on a global, guild, or user level. The values can then be
    accessed using the key phrase, allowing for long text, special characters, images, or urls to
    be fetched with short plaintext queries. Basic editing commands are present for text values

    Storing tags is done with the command `!tag [<key>] <value>`
    Fetching tags is done with the command `!tag <key>`

    These commands can be modified with CLI arguments

    `-ap` : Appends argument to value after a space
    `-apnl` : Appends argment to value after a line break
    `-edit` : Used to overwrite tag keys
    `-help` : Shows the user guide
    `-ls` : Lists the tags within the domain. Overrides any other argument
    `-rm` : Removes a tag from the domain
    `-u` : Changes the tag domain to the user's tags for the following command
    """

    def __init__(self, bot):
        self.bot = bot
        self.tags = {"global": {}, "server": {}, "user": {}}
        try:
            self.loadtags()
        except Exception as e:
            self.bot.loading_failure["tags"] = e

    @commands.command(help=LONG_HELP['tag'], brief=BRIEF_HELP['tag'], aliases=ALIASES['tag'])
    async def tag(self, ctx):
        """
        Tag command

        Parameters
        ------------
        ctx : discord.context
            The message context object
        """
        try:
            # -------------------------------- SET-UP

            # Makes the apostrophe types consistent
            # (See function documentation for explanation)
            parsed_ctx = parse.sanitize_apos(ctx.message.content)
            # Parses CLI arguments
            (arguments, message) = parse.args(parsed_ctx)

            # -------------------------------- ARGUMENTS

            # Acting on arguments
            if "help" in arguments or (len(message) == 0 and len(arguments) == 0):
                title = "!tag - User Guide"
                description = (
                            "Bot call and response. Allows the user to pair a message or attached image with a tag. " +
                            "These tags can then be used to have the bot respond with the associated content. By " +
                            "default, these tags are guild wide, but by using the user list argument (`-u`, e.g. " +
                            "`!tag -u [base] All your base are belong to us`) the user can specify personal tags. " +
                            "This allows a user to store a different value for a key than the guild value and to " +
                            "make tags that will be available for that user across guilds and in DMs.")
                helpdict = {
                    "-ap [<key>] <value>": "If the tag entered already exists, the " +
                                           "new text will be appended to the end after a space",
                    "-apnl [<key>] <value>": "If the tag entered already exists, " +
                                             "the new text will be appended to the end after a line break",
                    "-edit [<key>] <value>": "If the tag entered already exists, " +
                                             "the existing tag will be overwritten",
                    "-help": "Show this guide",
                    "-ls": "Lists the tags within the selected group. Overrides any " +
                           "other argument",
                    "-rm <key>": "removes a tag from the group",
                    "-u": "Selects your specific tag group instead of the guild " +
                          "tags for the following command"}
                await ctx.send(embed=utils.embed_from_dict(helpdict,
                                                           title=title,
                                                           description=description,
                                                           thumbnail_url=COMMAND_THUMBNAILS["tag"]))
                return

            # Rejects ambiguous argument pairs
            if "rm" in arguments and "edit" in arguments:
                await ctx.send("`-rm` and `-edit` are incompatible arguments")
                return
            elif ("apnl" in arguments or "ap" in arguments) and ("edit" in arguments or "rm" in arguments):
                await ctx.send("`ap` or `apnl` are incompatible with the arguments `-rm` or `-edit`")
                return
            elif "ap" in arguments and "apnl" in arguments:
                await ctx.send("`-ap` and `-apnl` is an ambiguous argument pair")
                return

            # flag for if the user is overwriting an existing tag
            edit = False
            # flag for if the user is appending to an existing tag
            append = False
            # flag for if the user wants a line break before their append is added
            newline = False
            # String specifying tag domain
            domain = "server"

            if ctx.guild is None or "u" in arguments:
                domain = "user"
                # MySQL parameter to specify owner of the tag
                tagowner = ctx.author.id
                # if user does not have a user tag group
                if ctx.author.id not in self.tags["user"].keys():
                    # Creates a user tag group
                    self.tags["user"][ctx.author.id] = {}
                # Changes the selected tag group to the user's tags
                selected_tags = self.tags["user"][ctx.author.id]
            else:
                # Selecting tag group (default is 'server')
                if ctx.guild.id not in self.tags["server"].keys():
                    self.tags["server"][ctx.guild.id] = {}
                # Gets domain tag group
                selected_tags = self.tags["server"][ctx.guild.id]
                # MySQL parameter to specify owner of the tag
                tagowner = ctx.guild.id

            # Adds global tags to guild tag group
            for key in self.tags["global"].keys():
                selected_tags[key] = self.tags["global"][key]

            # List the saved tags in the selected tag group
            if "ls" in arguments:
                taglist = ""
                for tagkey in sorted(selected_tags.keys()):
                    if tagkey in self.tags["global"].keys():
                        taglist += ", `" + tagkey + "`"
                    else:
                        taglist += ", " + tagkey
                if taglist == "":
                    if domain == "user":
                        await ctx.send("You do not have any saved tags")
                    else:
                        await ctx.send("This server does not have any saved tags")
                    return
                taglist = taglist[2:]  # pulls the extraneous comma off
                await ctx.send("**The tags I know are**\n" + taglist + "")
                return

            # Reject empty messages (`-ls` calls have already been handled)
            if len(message) == 0:
                await ctx.send("I see some arguments `` " + str(arguments) +
                                   " ``, but no key or value to work with :/")
                return

            # Deletes a saved tag
            if "rm" in arguments:
                key = message.lower()
                if key in selected_tags.keys():
                    del selected_tags[key]
                    await ctx.send("Okay. I deleted it")
                    self.update_tag_remove(key, tagowner, domain)
                else:  # If that tag didn't exist
                    await ctx.send("Hmmm, that's funny. I didn't see the tag `` " + message +
                                       " `` in the saved tags list.")
                return

            # ------ Set or Get ------

            # Check for modification flags
            if any(edit_arg in arguments for edit_arg in ["edit", "apnl", "ap"]):
                edit = True  # Allows modification of existing tag
            if any(append_arg in arguments for append_arg in ["apnl", "ap"]):
                append = True  # Adds new text to end of existing tag
            if "apnl" in arguments:
                newline = True  # Adds a new line before appending text

            # Setting
            if message[0] is "[":
                tag_keyvalue = parse.key_value(message, ctx.message.attachments)
                if tag_keyvalue[0] is None:
                    error_messages = {"EMPTY KEY": "There was no key to store",
                                      "UNCLOSED KEY": "You didn't close your brackets",
                                      "NO VALUE": "There was no text to save for the key provided",
                                      "WHITESPACE KEY": "Just because this bot is written in Python " +
                                                        "does not mean whitespace is an acceptable tag",
                                      "KEY STARTS WITH -": "The `-` character denotes the start of " +
                                                           "an argument and cannot be used in tag keys"}
                    await ctx.send(error_messages[tag_keyvalue[1]])
                    return
                else:
                    tagkey = tag_keyvalue[0].lower()
                    tagvalue = tag_keyvalue[1]
                    if tagkey in selected_tags.keys():
                        if tagkey in self.tags["global"].keys():
                            await ctx.send(
                                "I'm sorry, but the key `` " + tagkey +
                                " `` has already been reserved for a global tag")
                            return
                        elif edit is False:
                            await ctx.send(f"I already have a value stored for the tag `{tagkey}`. "
                                           f"Add `-edit` to overwrite existing tags")
                            return
                        elif append is True:
                            if newline is True:
                                selected_tags[tagkey] = selected_tags[tagkey] + "\n" + tagvalue
                            else:
                                selected_tags[tagkey] = selected_tags[tagkey] + " " + tagvalue
                            self.update_tag_edit(tagkey, selected_tags[tagkey], tagowner, domain)
                            await ctx.send("Edited!")
                            return
                        else:
                            selected_tags[tagkey] = tagvalue
                            self.update_tag_edit(tagkey, tagvalue, tagowner, domain)
                            await ctx.send("Edited!")
                            return
                    selected_tags[tagkey] = tagvalue
                    self.update_tag_add(tagkey, tagvalue, tagowner, domain)
                    await ctx.send("Saved!")
            # Getting
            else:
                key = message.lower()
                if key in selected_tags.keys():
                    await ctx.send(utils.trim_to_len(selected_tags[key], 2000))
                elif domain == "user":
                    await ctx.send(f"I don't think your account has a tag `{key}`. "
                                   "Type `!tag -u -ls` to see the tags I have saved for you")
                else:
                    await ctx.send(f"I don't think I have a tag `{key}` for this guild. "
                                   f"Type `!tag -ls` to see a list of this guild's tags")
        except Exception as e:
            await utils.report(self.bot, str(e), source="Tag command", ctx=ctx)

    # Posts the "No! No! No! ...NO!" JoJo video because I keep thinking the command exists
    @commands.command(hidden=True)
    async def no(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=O3WPHJEDMwc")

    # Posts the "Yes! Yes! YES!" JoJo video because people kept typing `!yes` instead of `!tag yes`
    @commands.command(hidden=True)
    async def yes(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=sq_Fm7qfRQk")

    def loadtags(self):
        """ Load tags from database """
        self.tags = {"global": {}, "server": {}, "user": {}}
        query = "SELECT * FROM Tags"
        cursor = self.bot.dbconn.execute(query)
        count = 0
        for (owner_id, key_string, value_string, domain) in cursor:
            owner_id = int(owner_id)    # ID has to be cast to int now because v1.0

            # I cannot figure out what makes tags sometimes load as str or utf-8 bytes
            if not isinstance(key_string, str):
                key_string = key_string.decode("utf-8")
            if not isinstance(value_string, str):
                value_string = value_string.decode("utf-8")

            if domain == "global":
                self.tags["global"][key_string] = value_string
            else:
                if owner_id not in self.tags[domain].keys():
                    self.tags[domain][owner_id] = {}
                self.tags[domain][owner_id][key_string] = value_string

    def update_tag_add(self, tag_key, tag_value, owner_id, domain):
        """ Adds a tag to the database

        Parameters
        -------------
        tag_key : str
            The key the tag is stored under
        tag_value : str
            The value for the new tag
        owner_id : str
            The 18 digit id representing the owner of the id
            For the user domain, this will be the user id
            For the server domain, this will be the server id
            For the global domain, it does not matter, but good practice is GLOBAL_TAG_OWNER
        domain : str
            The string which represents the domain of the tag
            "global" - Global tags. These tags are accessible on any server and cannot be edited by users
            "server" - Server tags. The default domain for the bot and accessible to all users on a server
            "user" - User tags. Follow users between servers and can be accessed with the `-u` argument
        """
        self.bot.dbconn.ensure_sql_connection()
        add_command = "INSERT INTO Tags VALUES (%s, %s, %s, %s)"
        add_data = (owner_id, tag_key, tag_value, domain)
        self.bot.dbconn.execute(add_command, add_data)
        self.bot.dbconn.commit()

    def update_tag_remove(self, tag_key, owner_id, domain):
        """ Removes a tag from the database

        Parameters
        -------------
        tag_key : str
            The key of the tag being removed
        owner_id : str
            The 18 digit id representing the owner of the id
            For the user domain, this will be the user id
            For the server domain, this will be the server id
            For the global domain, it does not matter, but good practice is GLOBAL_TAG_OWNER
        domain : str
            The string which represents the domain of the tag
            "global" - Global tags. These tags are accessible on any server and cannot be edited by users
            "server" - Server tags. The default domain for the bot and accessible to all users on a server
            "user" - User tags. Follow users between servers and can be accessed with the `-u` argument
        """
        self.bot.dbconn.ensure_sql_connection()
        remove_command = "DELETE FROM Tags WHERE Owner=%s AND KeyString=%s AND Domain=%s"
        remove_data = (owner_id, tag_key, domain)
        self.bot.dbconn.execute(remove_command, remove_data)
        self.bot.dbconn.commit()

    def update_tag_edit(self, tag_key, tag_value, owner_id, domain):
        """ Edits a tag in the database

        Parameters
        -------------
        tag_key : str
            The key the tag is stored under
        tag_value : str
            The new value for the tag
        owner_id : str
            The 18 digit id representing the owner of the id
            For the user domain, this will be the user id
            For the server domain, this will be the server id
            For the global domain, it does not matter, but good practice is GLOBAL_TAG_OWNER
        domain : str
            The string which represents the domain of the tag
            "global" - Global tags. These tags are accessible on any server and cannot be edited by users
            "server" - Server tags. The default domain for the bot and accessible to all users on a server
            "user" - User tags. Follow users between servers and can be accessed with the `-u` argument
        """
        self.bot.dbconn.ensure_sql_connection()
        edit_command = "UPDATE Tags SET ValueString=%s WHERE KeyString=%s and Owner=%s and Domain=%s"
        edit_data = (tag_value, tag_key, owner_id, domain)
        self.bot.dbconn.execute(edit_command, edit_data)
        self.bot.dbconn.commit()


def setup(bot):
    bot.add_cog(Tags(bot))
