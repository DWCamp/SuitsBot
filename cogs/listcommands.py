from discord import Embed
from discord.abc import PrivateChannel
from discord.ext import commands
from discord.ext.commands import Cog
from constants import *
import utils
import parse
from local_config import AUTHORIZED_IDS


class ListCommands(Cog):

    """
    Commands used for modifying user generated lists

    list
      Create and edit arbitrary lists

    bestgirl
      Shortcut for editing the bestgirl list
    """

    def __init__(self, bot):
        self.bot = bot
        self.failed_to_load = None
        try:
            list_table = self.loadlists()
            self.list_engine = ListEngine(bot, list_table)
            bot.list_engine = self.list_engine
        except Exception as e:
            self.bot.loading_failure["lists"] = e

    @commands.command(help=LONG_HELP['bestgirl'], brief=BRIEF_HELP['bestgirl'],
                      aliases=ALIASES['bestgirl'])
    async def bestgirl(self, ctx):
        if "lists" in self.bot.loading_failure.keys():
            await ctx.channel.send("An error occurred while loading the lists during start up. " +
                                   "Use of this command now could cause data loss. Please contact " +
                                   "the bot owner")
            return

        title = "!bestgirl - User Guide"
        description = "A dedicated command for modifying a user's `BestGirl` list. As with the more general `!list` "\
                      "command, it allows for the storage of a user created table. In this case, the table is "\
                      "intended for listing and ranking the best female characters in any media, typically anime."
        helpdict = {"!bestgirl": "Presents your list",
                    "!bestgirl add <girl>": "Appends the entry to the end of your list",
                    "!bestgirl add [<index>] <girl>": "Appends the entry to the list at the index specified",
                    "!bestgirl clear": "Clears your list. Be very careful!",
                    "!bestgirl icon <url>/<attachment>": "Sets the thumbnail of your list to an image, either by " +
                                                         "supplying a url or attaching an image",
                    "!bestgirl move <indexA> <indexB>": "Moves the element in indexA to indexB. The item at indexB " +
                                                        "is moved down",
                    "!bestgirl multiadd <girl>; <girl>": "Appends multiple entries to the list at once. Entries are " +
                                                         "separated by a semicolon",
                    "!bestgirl remove [<index>]": "Removes the entry at the designated index from your list",
                    "!bestgirl rename [<index>] <girl>": "Replaces the entry at one index with another",
                    "!bestgirl show <userMention>": "Displays the lists for the user mentioned",
                    "!bestgirl static": "Presents the user list, but this list will not change as future edits " +
                                        "are made",
                    "!bestgirl swap <index> <index>": "Swaps the entries at the two locations",
                    "!bestgirl thumbnail <url>": "Sets a thumbnail for the list. URL must point directly to " +
                                                 "an image file",
                    "!bestgirl title <title>": "Sets the title of the list. Replying without a title resets the " +
                                               "value to the default (i.e. '<Your name>'s list')",
                    "!bestgirl help": "This command. Lists documentation"}
        embed = utils.embedfromdict(helpdict,
                                    title=title,
                                    description=description,
                                    thumbnail_url=COMMAND_THUMBNAILS["bestgirl"])
        try:
            await self.list_engine.parse(ctx, helpembed=embed, command="bestgirl", list_id="BestGirl")
        except Exception as e:
            await utils.report(self.bot, str(e), source="!bestgirl command", ctx=ctx)

    # User creation of arbitrary lists and editing them
    @commands.command(help=LONG_HELP['ls'], brief=BRIEF_HELP['ls'], aliases=ALIASES['ls'])
    async def ls(self, ctx):
        if "lists" in self.bot.loading_failure.keys():
            await ctx.channel.send("An error occurred while loading the lists during start up. " +
                                   "Use of this command now could cause data loss. Please contact " +
                                   "the bot owner")
            return

        title = "!list - User Guide"
        description = (
                    "List creation and management. Allows users to create arbitrary lists that the bot will store. " +
                    "Users can then add and remove elements, modify elements, and move elements around. Lists can " +
                    "also have unique titles and thumbnails.")
        helpdict = {"!list": "Will print the current list if there is one",
                    "help": "This command. Lists documentation",
                    "clear <id?>": "Deletes all elements from the list but does not remove the list",
                    "curr": "Prints the list the user is currently editing",
                    "create <id>": "Create a new user list with the specified ID",
                    "drop <id>": ("Deletes the table with specified ID. THIS IS PERMANENT AND CANNOT BE UNDONE. " +
                                  "Use with caution"),
                    "show": "Show the IDs for all the user's lists",
                    "use <id>": ("Move the user space to the list with that ID. In response, it will print the " +
                                 "contents of the list"),
                    "add <item>": "Adds element at the end of the list",
                    "add [<index>] <item>": "Adds element to the list at the given index",
                    "multiadd <item>;<item>": ("Adds every element of a semicolon seperated list to the end of " +
                                               "the list"),
                    "move <indexA> <indexB>": "Moves the element at indexA to indexB",
                    "remove <index>": "Removes the element at the given index",
                    "replace [<index>] <item>": "Replaces the element at that index with that item",
                    "swap <indexA> <indexB>": "Swaps the positions of the elements at indexA and indexB",
                    "thumbnail <url>": "Sets a thumbnail for the list. URL must point directly to an image file",
                    "title <title>": "Assigns the title to the list with that index"}
        helpembed = utils.embedfromdict(helpdict,
                                        title=title,
                                        description=description,
                                        thumbnail_url=COMMAND_THUMBNAILS["ls"])
        try:
            await self.list_engine.parse(ctx, helpembed=helpembed, command="list")
        except Exception as e:
            await utils.report(self.bot, str(e), source="!ls command", ctx=ctx)

    def loadlists(self):
        """ Load lists from database """

        list_user_table = {}

        # Load list metadata
        select_query = "SELECT * FROM ListDetails"
        cursor = self.bot.dbconn.execute(select_query)
        for (user_id, list_id, title, thumbnail_url) in cursor:
            user_id = int(user_id)
            list_id = list_id.decode("utf-8")
            if title is not None:
                title = title.decode("utf-8")
            else:
                title = None
            if thumbnail_url is not None:
                thumbnail_url = thumbnail_url.decode("utf-8")
            else:
                thumbnail_url = None
            if user_id not in list_user_table.keys():
                list_user_table[user_id] = {}
            user = self.bot.get_user(user_id)
            if user:
                list_user_table[user_id][list_id] = UserList(self.bot,
                                                             list_id=list_id,
                                                             username=user.name,
                                                             thumbnail_url=thumbnail_url,
                                                             title=title)
                if list_id == "BestGirl":
                    list_user_table[user_id][list_id].color = EMBED_COLORS['bestgirl']

        # Load list elements
        select_query = "SELECT * FROM Lists"
        cursor = self.bot.dbconn.execute(select_query)
        for (user_id, list_id, list_index, element) in cursor:
            user_id = int(user_id)
            list_id = list_id.decode("utf-8")
            element = element.decode("utf-8")
            if user_id not in list_user_table.keys():
                raise AttributeError(f"User `{user_id}` not found in list_user_table.keys()")
            # if list_id not in list_user_table[user_id].keys():
            #     raise AttributeError("Found element `` {} `` with ID `` {} `` for user `` {} `` with no "
            #                          "corresponding list".format(element, list_id, user_id))
            userlist = list_user_table[user_id][list_id]
            userlist.buffer(element, list_index)
        for userLists in list_user_table.values():
            for userlist in userLists.values():
                userlist.commit()

        return list_user_table


class UserList:
    """
    Data type for storing the elements and attributes of a user's list

    Parameters
    ------------
    bot : discord.bot object
        The bot object
    list_id: str
        The string which identifies the list. Unique per user
    username: str
        The name of the user who created the list
    title: Optional[str]
        The title of the list
    elements: Optional[list]
        The elements of the list
    thumbnail_url: Optional[str]
        The url of the list embed's thumbnail
    color: Optional[int]
        The color value for the list. Defaults to LIST_EMBED_COLOR
    """
    def __init__(self, bot, list_id, username="", title=None, elements=None, thumbnail_url=None,
                 color=EMBED_COLORS["list"]):
        if elements is None:
            elements = []
        if title is None:
            title = ""
        if thumbnail_url is None:
            thumbnail_url = ""
        self._bot = bot
        self.id = list_id
        self.username = username
        self.contents = elements
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.updating = None
        self.updatingMessages = []
        self.color = color
        self._bufferlist = []

    # -------------- INSTANCE METHODS

    def add(self, entry, rank=None):
        """ Add an entry to a rank

        Parameters
        ------------ 
        entry: str
            The text element to add to the list
        rank: Optional[int]
            The 1-indexed rank to add the element at. Defaults to the end of the list

        Raises
        ------------ 
        ValueError - If the rank is outside the bounds of the list
        """
        if rank is None:
            rank = len(self.contents) + 1
        if rank > len(self.contents) + 1:
            raise ValueError('Rank cannot exceed the length of the list plus 1. Rank was ' + str(rank)
                             + ", list length is " + str(len(self.contents)))
        if rank < 1:
            raise ValueError('Rank cannot be less than 0')
        self.contents.insert(rank - 1, entry)

    def buffer(self, element, index):
        """ Buffer elements
        During start up, stores the elements as it gets them in their appropriate index
        using `None` as spacers until all elements are assembled

        Parameters
        ------------ 
        element: str
            The text element to add to the list
        index: int
            The index in the list where the entry should be added

        Raises
        ------------ 
        ValueError - If an entry is buffered to an already filled position
        """
        if len(self._bufferlist) <= index:
            self._bufferlist.extend([None] * (index - len(self._bufferlist) + 1))
        if self._bufferlist[index] is not None:
            raise ValueError("List: " + self.id + "\nThere was already an element at index " + str(index) + "\n" +
                             str(self._bufferlist))
        del self._bufferlist[index]
        self._bufferlist.insert(index, element)

    def clear(self):
        """ Empties the contents of the list """
        self.contents = []

    def commit(self):
        """ Commits the buffer to contents

        Raises
        ------------ 
        ValueError - if any elements are missing
        """
        for (index, element) in enumerate(self._bufferlist):
            if element is None:
                raise ValueError("None value in buffer found at index " + str(index) + " for list id " + self.id)
        self.contents = self._bufferlist

    def isempty(self):
        """ Checks is the list is empty

        Returns
        ------------ 
        `True` if length of the list is 0
        """
        return len(self.contents) == 0

    # Returns the list of embeds which prints out the entire list
    def get_embeds(self):

        # Generates a new blank embed
        def new_embed(cont=False):
            """
             Generates a new list embed

            Parameters
            ------------
            cont : bool
                Whether or not this is a continuation of a previous embed. Defaults to false

            Returns
            ------------
            A pre-formatted embed
            """
            embed = Embed()
            if cont:
                if self.title == "":
                    embed.title = utils.trimtolength(self.id, 248) + " (cont.)"
                else:
                    embed.title = utils.trimtolength(self.title, 248) + " (cont.)"
            else:
                if self.title == "":
                    embed.title = self.id
                else:
                    embed.title = self.title
                embed.set_thumbnail(url=self.thumbnail_url)
            embed.description = ""
            embed.colour = self.color
            embed.set_footer(text="[0/2048]")
            return embed

        curr_embed = new_embed()
        embed_list = [curr_embed]

        if len(self.contents) == 0:
            curr_embed.description = "(This list is empty)"
            return embed_list

        lines = []
        for i in range(0, len(self)):
            lines.append(self.print_line(i + 1))

        while len(lines) > 0:
            # If the current embed is full, create a new one
            if len(curr_embed.description) + len(lines[0]) > 2048:
                curr_embed = new_embed(cont=True)
                embed_list.append(curr_embed)
            curr_embed.description += lines.pop(0)
            curr_embed.set_footer(text="[" + str(len(curr_embed.description)) + "/2048]")
        return embed_list

    def __len__(self):
        return len(self.contents)

    def move(self, rank_current, rank_target):
        if rank_current < 1 or rank_target < 1:
            raise ValueError('Rank cannot be less than 1.')
        if rank_current > len(self.contents) or rank_target > len(self.contents):
            raise ValueError('Rank cannot be greater than the length of the list')
        element = self.contents[rank_current - 1]
        del self.contents[rank_current - 1]
        self.contents.insert(rank_target - 1, element)
        return element

    def print_line(self, rank):
        return "**" + str(rank) + ".** " + self.contents[rank - 1] + "\n"

    def remove(self, rank):
        if rank > len(self.contents):
            raise ValueError('Index exceeds the size of the list')
        if rank < 1:
            raise ValueError('Index cannot be less than 0')
        value = self.contents[rank - 1]
        del self.contents[rank - 1]
        return value

    def replace(self, element, rank):
        if rank > len(self.contents):
            raise ValueError('Index exceeds the size of the list')
        if rank < 1:
            raise ValueError('Index cannot be less than 1')
        old_value = self.contents[rank - 1]
        self.contents[rank - 1] = element
        return old_value

    async def set_thumbnail(self, url):
        if url is not "":
            if self._bot.regex.is_url(url):
                self.thumbnail_url = url
            else:
                raise ValueError("Invalid URL")
        else:
            self.thumbnail_url = ""
        return True

    def swap(self, rank_a, rank_b):
        if rank_a < 1 or rank_b < 1:
            raise ValueError('Index cannot be less than 1.')
        if rank_a > len(self.contents) or rank_b > len(self.contents):
            raise ValueError('Index cannot be greater than the length of the list')
        element = self.contents[rank_a - 1]
        self.contents[rank_a - 1] = self.contents[rank_b - 1]
        self.contents[rank_b - 1] = element
        return [self.contents[rank_a - 1], element]

    async def update_messages(self):
        """ Updates all of the list embed messages. 
        If one of the embeds is no longer needed, the message is deleted

        Returns 
        -------------
        Returns a boolean flag for whether the list overflowed the available 
        embeds and could not be fully displayed
        """
        try:
            new_embeds = self.get_embeds()
            new_message_list = []
            for i in range(0, len(new_embeds)):
                if i < len(self.updatingMessages):
                    if self.updatingMessages[i] is None:
                        await utils.report(self._bot, "FOUND NONE MESSAGE")
                        return True
                    new_message_list.append(await self._bot.edit_message(self.updatingMessages[i], embed=new_embeds[i]))
                else:
                    self.updatingMessages = new_message_list
                    return True
            for message in self.updatingMessages[len(new_embeds):]:
                await self._bot.delete_message(message)
            self.updatingMessages = new_message_list
            return False
        except Exception as e:
            await utils.report(self._bot, str(e), source="update_messages")


class ListEngine:
    def __init__(self, bot, user_table):
        self._bot = bot
        self._dbconn = bot.dbconn
        self.user_table = user_table
        self.spaces = {}

        title = "!list - User Guide"
        description = "List creation and management. Allows users to create arbitrary lists that the self._bot will " \
                      "store. Users can then add and remove elements, modify elements, and move elements around. " \
                      "Lists can also have unique titles and thumbnails."
        helpdict = {"!list": "Will print the current list if there is one",
                    "help": "This command. Lists documentation",
                    "clear <id?>": "Deletes all elements from the list but does not remove the list",
                    "curr": "Prints the list the user is currently editing",
                    "create <id>": "Create a new user list with the specified ID",
                    "drop <id>": "Deletes the table with specified ID. THIS IS PERMANENT AND CANNOT BE "
                                 "UNDONE. Use with caution",
                    "show": "Show the IDs for all the user's lists",
                    "use <id>": "Move the user space to the list with that ID. In response, it will print the "
                                "contents of the list",
                    "add <item>": "Adds element at the end of the list",
                    "add [<index>] <item>": "Adds element to the list at the given index",
                    "multiadd <item>;<item>": "Adds every element of a semicolon seperated list to the end "
                                              "of the list",
                    "move <indexA> <indexB>": "Moves the element at indexA to indexB",
                    "remove <index>": "Removes the element at the given index",
                    "replace [<index>] <item>": "Replaces the element at that index with that item",
                    "swap <indexA> <indexB>": "Swaps the positions of the elements at indexA and indexB",
                    "thumbnail <url>": "Sets a thumbnail for the list. URL must point directly to an "
                                       "image file",
                    "title <title>": "Assigns the title to the list with that index"}
        embedcolor = EMBED_COLORS["list"]
        helpembed = utils.embedfromdict(helpdict,
                                        title=title,
                                        description=description,
                                        thumbnail_url=COMMAND_THUMBNAILS["ls"],
                                        color=embedcolor)
        self._defaultembed = helpembed

    def add_user(self, user_id):
        """
        Adds a user to the list engine. Adds the user to the user_table and
        creates an entry for their bestGirl list in the ListDetails table
        Parameters
        -------------
        user_id : string
            The Discord user id of the user being added
        """
        self.user_table[user_id] = {}
        self.create_list(user_id, "BestGirl")

    async def parse(self, ctx, helpembed=None, command="list", list_id=None):
        """ Performs list manage functions

        Parameters
        -------------
        ctx : context object
            The context object from the request. Used for author ID, author name, and the message content
        helpembed : Optional - Embed
            An embed to provide the user with assistance. Used for overriding the default help embed by commands
            abstracting `!list`. If no value is provided, the help embed for `!list` is used
        command : Optional - str
            A tag to help identify which command called listfunction. Commands abstracting `!list` should provide
            their names in this value. Defaults to "list"
        list_id : Optional - str
            The id of the list to use. Used to perform actions on lists other than the currently active list.
            If no id is provided, the id stored in self.spaces for the user will be used
        """
        # LIST -------------------------------------- PRELIMINARY PROCESSES

        author_id = ctx.author.id
        # Gets the nickname name of the author if it exists, otherwise gets the Discord name
        if isinstance(ctx.channel, PrivateChannel) or ctx.author.nick is None:
            author_name = ctx.author.name
        else:
            author_name = ctx.author.nick

        # parse message of apostrophes
        parsedctx = parse.apos(ctx.message.content)

        # separates out the function call and its parameters
        [func, parameter] = parse.func_param(parsedctx)

        # Premptively creates a list table if author does not have one
        if author_id not in self.user_table.keys():
            self.user_table[author_id] = {}
        author_lists = self.user_table[author_id]

        # Creates a 'None' entry in the self.spaces if author is not in it
        if author_id not in self.spaces.keys():
            self.spaces[author_id] = None

        # Also sets the current list
        if list_id is None:
            curr_list = self.spaces[author_id]
        else:
            curr_list = self.user_table[author_id][list_id]
        # LIST -------------------------------- FUNCTIONS

        # --------------------- DISPLAY FUNCTIONS

        # updating
        if func in ["", "updating"]:
            try:
                if curr_list is None:
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to "
                                                 "begin editing a list or `!list help` for more information")
                    return
                embeds = curr_list.get_embeds()
                curr_list.updatingMessages = []
                for embed in embeds:
                    curr_list.updatingMessages.append(await ctx.channel.send(embed=embed))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List updating command, via " + command, ctx=ctx)
            return

        # static
        if func == "static":
            try:
                if curr_list is None:  # If there is no currently active list, reject the command
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to "
                                                 "begin editing a list or `!list help` for more information")
                    return
                embeds = curr_list.get_embeds()
                for embed in embeds:
                    await ctx.channel.send(embed=embed)
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List static command, via " + command, ctx=ctx)
            return

        # --------------------- EDIT FUNCTIONS

        closed_for_dev_work = False
        if closed_for_dev_work and author_id not in AUTHORIZED_IDS:
            await ctx.channel.send(
                                         "Editing lists has been temporarily disabled because it is undergoing "
                                         "development. Attempts to use this command could fail or cause data loss")
            return

        # add <element>
        # add [<index>] <element>
        if func in ["add", "insert"]:  # X
            try:
                if curr_list is None:  # If there is no currently active list, reject the command
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to " +
                                                 "begin editing a list or `!list help` for more information")
                    return
                [element, rank] = parse.stringandoptnum(parameter)  # Get index and element
                curr_list.add(element, rank)
                self.update_list_add(author_id, curr_list.id, element, rank)
                if await curr_list.update_messages():
                    embeds = curr_list.get_embeds()
                    curr_list.updatingMessages = []
                    for embed in embeds:
                        curr_list.updatingMessages.append(await ctx.channel.send(embed=embed))
                if rank is None:
                    rank = len(curr_list)
                await ctx.channel.send(
                                             "I have now recognized `` {} `` as the number {} entry in your list"
                                             .format(element, rank))
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List add command, via " + command, ctx=ctx)
            return

        # clear
        # clear <id>
        if func == "clear":
            try:
                if list_id is not None:
                    await ctx.channel.send(
                                                 "The command `clear` is only available when using '!list'")
                    return
                list_id = parameter.lower()
                if list_id == "":  # If no ID was provided, use the currently active list
                    if curr_list is None:  # If there is no currently active list, reject the command
                        await ctx.channel.send(
                                                     "You are not currently in any list. Type `!list use <id>` to " +
                                                     "begin editing a list or `!list help` for more information")
                        return
                    list_id = curr_list.id  # Record the ID
                    curr_list.clear()  # clear the list
                else:  # If the user specified a list_id
                    if list_id not in author_lists.keys():  # If there is no list with that ID, reject the command
                        await ctx.channel.send(
                                                     "You do not have a list with the ID `` " + list_id + " ``. " +
                                                     "Type `!" + command + " show` to see your table of list IDs")
                        return
                    author_lists[list_id].clear()  # clear the list
                if curr_list is not None:
                    await curr_list.update_messages()
                self.clear_list(author_id, curr_list.id)
                await ctx.channel.send(
                                             "Your list with ID `` " + list_id + " `` has been cleared")
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List clear command, via " + command, ctx=ctx)
            return

        # curr
        if func in ["curr", "curr_list"]:
            try:
                if list_id is not None:
                    await ctx.channel.send(
                                                 "The command `" + command + "` is only available when using '!list'")
                    return
                if self.spaces[author_id] is None:  # If the user is not currently in a list
                    await ctx.channel.send("You are not currently in a list")
                else:
                    await ctx.channel.send("`" + self.spaces[author_id].id + "`")
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List curr command, via " + command, ctx=ctx)
            return

        # create <id>
        if func == "create":
            try:
                if list_id is not None:
                    await ctx.channel.send(
                                                 "The command `create` is only available when using '!list'")
                    return
                list_id = parameter.lower()
                if list_id in author_lists.keys():  # If the user already has a list with that ID, reject the command
                    await ctx.channel.send(
                                                 "You already have a list with the ID `` " + list_id +
                                                 " ``. To delete that list, use the `!list drop` command, to keep " +
                                                 "the list but clear the values, use the `!list clear` command, or " +
                                                 "type `!list help` for more information")
                    return
                if list_id == "":  # If the user did not provide an ID, reject the command
                    await ctx.channel.send("You cannot create a list with a blank ID")
                    return
                author_lists[list_id] = UserList(self._bot, list_id=list_id, username=author_name)

                self.spaces[author_id] = author_lists[list_id]  # Set the new list to the author's active list
                self.create_list(author_id, list_id)
                new_embed = await ctx.channel.send(
                                                         embed=author_lists[list_id].get_embeds()[0])
                author_lists[list_id].updating = [new_embed]
                await ctx.channel.send(
                                             "I have created a list with the ID `` " + list_id +
                                             " `` and set it to your current list")
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List create command, via " + command, ctx=ctx)
            return

        # dev
        if func == "dev":
            try:
                if curr_list is None:  # If there is no current list, reject the command
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to " +
                                                 "begin editing a list or `!list help` for more information")
                    return
                await ctx.channel.send(str(curr_list.updating))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List dev command", ctx=ctx)
            return

        # drop <id>
        if func == "drop":
            try:
                if list_id is not None:
                    await ctx.channel.send(
                                                 "The command `drop` is only available when using '!list'")
                    return
                list_id = parameter.lower()
                if list_id == "":  # If the user did not provide a list, use the currently active list
                    await ctx.channel.send(
                                                 "You must specify the ID of the list you wish to drop")
                    return
                else:  # If the user provided an ID
                    if list_id not in author_lists.keys():  # If the user provided ID doesn't exist, reject the command
                        await ctx.channel.send(
                                                     "You do not have a list with the ID `` " + list_id +
                                                     " ``. Type `!list show` to see your table of list IDs")
                        return
                if self.spaces[author_id] == author_lists[list_id]:  # If list was active list, set space to None
                    self.spaces[author_id] = None
                del author_lists[list_id]  # Drop the list
                self.drop_list(author_id, list_id)
                if curr_list is not None and curr_list.updating is not None:
                    for message in curr_list.updating:
                        await self._bot.delete_message(message)
                await ctx.channel.send(
                                             "Your list with ID `` " + list_id + " `` has been dropped")
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List drop command, via " + command, ctx=ctx)
            return

        # move <index> <index>
        if func == "move":
            try:
                if curr_list is None:  # If there is no current list, reject the command
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to " +
                                                 "begin editing a list or `!list help` for more information")
                    return
                numbers = parse.twonumbers(parameter)
                element = curr_list.move(numbers[0], numbers[1])
                self.update_list_move(author_id, curr_list.id, from_rank=numbers[0], to_rank=numbers[1])
                await curr_list.update_messages()
                await ctx.channel.send(
                                             "Alright, I moved `` " + element + " `` to index " + str(numbers[1]))
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List move command, via " + command, ctx=ctx)
            return

        # multiadd <element>;<element>;<element>...
        if func == "multiadd":
            try:
                if curr_list is None:  # If there is no active list, reject the command
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to " +
                                                 "begin editing a list or `!list help` for more information")
                    return
                else:
                    elements = parameter.split(';')
                    addition = ""
                    for (i, element) in enumerate(elements):
                        addition += "**" + str(len(curr_list) + i + 1) + ".** " + element + "\n"
                    for element in elements:  # Split the list at semicolons
                        element = element.strip()
                        if len(element) > 0:  # Add the item only if the element has text
                            curr_list.add(element)  # Add the element
                            self.update_list_add(author_id, curr_list.id, element)
                    if await curr_list.update_messages():
                        embeds = curr_list.get_embeds()
                        curr_list.updatingMessages = []
                        for embed in embeds:
                            curr_list.updatingMessages.append(await ctx.channel.send(
                                                                                          embed=embed))
                    if len(elements) == 1:
                        await ctx.channel.send(
                                                     "I have added " + str(len(elements)) + " element to your list")
                    else:
                        await ctx.channel.send(
                                                     "I have added " + str(len(elements)) + " elements to your list")
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List multiadd command, via " + command, ctx=ctx)
            return

        # remove <index>
        if func in ["remove", "delete"]:
            try:
                if curr_list is None:
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to "
                                                 "begin editing a list or `!list help` for more information")
                    return
                ranks = parameter.replace("[", "").replace("]", "").split(";")

                # Parse index strings to int values
                int_ranks = list()
                for rank in ranks:
                    try:
                        parsed_rank = int(rank)
                        if parsed_rank not in int_ranks:
                            int_ranks.append(parsed_rank)
                    except ValueError:
                        await ctx.channel.send("`" + rank + "` is not a valid index number")
                        return

                # Check for out of bounds and correct ranks
                # Ranks need to be corrected since when index 4 gets removed, index 5
                # will become index 4, so the later indices need to be shifted up one
                shifted_ranks = list()
                for rank in int_ranks:
                    # Check bounds
                    if rank > len(curr_list):
                        await ctx.channel.send(
                                                     "The index `" + str(rank) + "` exceeds the length of your list")
                        return
                    elif rank < 1:
                        await ctx.channel.send(
                                                     "The index `" + str(rank) + "` is less than 1, which is not valid")
                        return
                    for previousRank in shifted_ranks:
                        if previousRank < rank:
                            rank -= 1
                    shifted_ranks.append(rank)

                removed_elements = list()
                for rank in shifted_ranks:
                    rank = int(rank)
                    removed_elements.append(curr_list.remove(rank))
                    if len(curr_list) > 0:
                        self.update_list_remove(author_id, curr_list.id, rank)
                    else:
                        self.clear_list(author_id, curr_list.id)

                await curr_list.update_messages()
                await ctx.channel.send(
                                             "I have removed `` " + " ``, `` ".join(removed_elements) +
                                             " `` from your list")
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List remove command, via " + command, ctx=ctx)
            return

        # replace [<index>] <entry>
        if func in ["replace", "rename", "edit"]:
            try:
                if curr_list is None:
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to "
                                                 "begin editing a list or `!list help` for more information")
                    return
                [element, rank] = parse.stringandoptnum(parameter)
                if rank is None:
                    await ctx.channel.send(
                                                 "I don't see an index to modify. Make sure it is enclosed in "
                                                 "[square brackets]")
                    return
                old_val = curr_list.replace(element, rank)
                if await curr_list.update_messages():
                    embeds = curr_list.get_embeds()
                    curr_list.updatingMessages = []
                    for embed in embeds:
                        curr_list.updatingMessages.append(await ctx.channel.send(embed=embed))
                self.update_list_element(author_id, curr_list.id, rank, element)
                await ctx.channel.send(
                                             "The element `` {} `` has been renamed to `` {} ``"
                                             .format(old_val, element))
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List replace command, via " + command, ctx=ctx)
            return

        # show
        if func == "show":
            try:
                if list_id is not None:  # handles edge cases
                    if list_id == "BestGirl":
                        if len(ctx.message.mentions) == 0:
                            await ctx.channel.send(
                                                         "I don't see any mentions. Use the command `!bg help` for "
                                                         "instructions on how to use this function")
                            return
                        target_id = ctx.message.mentions[0].id
                        for embed in self.user_table[target_id]["BestGirl"].get_embeds():
                            await ctx.channel.send(embed=embed)
                    return
                if len(author_lists.keys()) == 0:
                    await ctx.channel.send(
                                                 "You have no lists stored. Type `!list create <id>` to create a "
                                                 "list a type `!list help` for more information")
                    return
                message = "Your lists are:\n```"

                longest_id_length = 0
                # get longest user list ID
                for list_id in author_lists.keys():
                    if len(list_id) > longest_id_length:
                        longest_id_length = len(list_id)

                for list_id in sorted(author_lists.keys()):
                    if list_id not in RESERVED_LIST_IDS:
                        if self.spaces[author_id] is not None and self.spaces[author_id].id == list_id:
                            message += "> "
                        else:
                            message += "  "
                        message += list_id + (" " * (longest_id_length - len(list_id))) + " | "
                        if len(author_lists[list_id]) == 1:
                            message += "1 element"
                        else:
                            message += str(len(author_lists[list_id])) + " elements"
                        message += "\n"
                message += "```"

                await ctx.channel.send(message)
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List show command, via " + command, ctx=ctx)
            return

        # swap <index> <index>
        if func == "swap":
            try:
                if curr_list is None:
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to begin " +
                                                 "editing a list or `!list help` for more information")
                    return
                numbers = parse.twonumbers(parameter)
                elements = curr_list.swap(numbers[0], numbers[1])
                self.update_list_swap(author_id, curr_list.id, numbers[0], numbers[1])
                await curr_list.update_messages()
                await ctx.channel.send(
                                             "Alright, I swapped `` {} `` with `` {} ``".format(elements[0],
                                                                                                elements[1]))
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List swap command, via " + command, ctx=ctx)
            return

        # thumbnail <url>
        # thumnail
        # icon <url>
        if func == "thumbnail" or func == "icon":
            try:
                if curr_list is None:
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to begin " +
                                                 "editing a list or `!list help` for more information")
                    return
                if len(ctx.message.attachments) == 0:
                    await curr_list.set_thumbnail(parameter)
                else:
                    await curr_list.set_thumbnail(ctx.message.attachments[0]['url'])
                self.update_list_details(author_id, curr_list.id)
                await curr_list.update_messages()
                await ctx.channel.send("Congratulations, your thumbnail has been updated")
            except ValueError as e:
                await ctx.channel.send(str(e))
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List thumbnail command, via " + command, ctx=ctx)
            return

        # title <title>
        if func == "title":
            try:
                if curr_list is None:
                    await ctx.channel.send(
                                                 "You are not currently in any list. Type `!list use <id>` to begin " +
                                                 "editing a list or `!list help` for more information")
                    return
                if len(parameter) > 256:
                    await ctx.channel.send(
                                                 "Due to Discord limitations, titles may not exceed 256 characters. " +
                                                 "Your title was " + str(len(parameter)))
                    return

                if parameter == "" and list_id is "BestGirl":
                    parameter = curr_list.username + "'s Best Girl List"

                old_title = curr_list.title
                curr_list.title = parameter  # Set the title

                self.update_list_details(author_id, curr_list.id)  # Save to database
                if curr_list is not None:
                    await curr_list.update_messages()
                if old_title == "":
                    await ctx.channel.send(
                                                 "Alright. I have set your title to `` " + parameter + " ``")
                elif parameter == "":
                    await ctx.channel.send(
                                                 "Alright. I have removed your title `` " + old_title + " ``")
                else:
                    await ctx.channel.send(
                                                 "Alright. I have changed the title from `` " +
                                                 old_title + " `` to `` " + parameter + " ``")
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List title command, via " + command, ctx=ctx)
            return

        # use <id>
        if func == "use":
            try:
                if list_id is not None:
                    await ctx.channel.send(
                                                 "The command `use` is only available when using '!list'")
                    return
                if parameter == "":  # If the user did not provide an ID to use, reject the command
                    await ctx.channel.send(
                                                 "I need an ID of a list for you to select (e.g. `!list use list_id)`")
                    return
                list_id = parameter.lower()
                if list_id not in author_lists.keys():
                    await ctx.channel.send((
                            "I don't see a list with the ID `` " + list_id +
                            " ``. Type `!list show` to see the table of list IDs"))
                    return
                self.spaces[author_id] = author_lists[list_id]  # Set the list to be active
                curr_list = author_lists[list_id]

                embeds = curr_list.get_embeds()
                curr_list.updatingMessages = []
                for embed in embeds:
                    curr_list.updatingMessages.append(await ctx.channel.send(embed=embed))

                await ctx.channel.send(
                                             "Alright, you are now using the list '" + list_id + "'")
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List use command, via " + command, ctx=ctx)
            return

        # LIST -------------------------------- HELP

        # help
        if func == "help":
            try:
                if helpembed is not None:
                    await ctx.channel.send(embed=helpembed)
                else:
                    await ctx.channel.send(embed=self._defaultembed)
            except Exception as e:
                await  utils.report(self._bot, str(e), source="List help command, via " + command, ctx=ctx)
            return

        await ctx.channel.send(
                                     "I don't recognize the function ` " + func + " `. Type `!" + command +
                                     " help` for information on this command")

        # ------------------ UPDATE LIST MYSQL DB -------------------------------

    def update_list_details(self, user_id, list_id):
        """ Synchronizes a list's details with the database

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user
        list_id : str
            The id of the list being updated
        """
        self._dbconn.ensure_sql_connection()
        update_query = "UPDATE ListDetails SET Title=%s, ThumbnailURL=%s WHERE USER=%s AND ID=%s"
        update_data = (self.user_table[user_id][list_id].title,
                       self.user_table[user_id][list_id].thumbnail_url, user_id, list_id)
        self._dbconn.execute(update_query, update_data)
        self._dbconn.commit()

    def update_list_shift(self, user_id, list_id, shift=0, from_rank=1, to_rank=0):
        """ Shifts the rank of a block of elements

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user making the edit
        list_id : str
            The id of the list being edited
        shift : Optional - int
            The amount to add to the rank of an element. Use a negative number to decrease the rank
            If a value is not provided, or the shift is 0, the elements will not be shifted.
        from_rank : Optional - int
            The rank (inclusive) to begin the shift. If no value is provided, the range begins at the start
        to_rank : Optional - int
            The rank (inclusive) to end the shift. If no value is provided, the range ends at the start
        """
        # Reject invalid parameter
        list_length = len(self.user_table[user_id][list_id])
        if shift == 0:
            return
        if from_rank > list_length:
            raise ValueError("from_rank cannot be greater than list length.\nList length is: %s\nfrom_rank was: %s"
                             .format(list_length, from_rank))
        if shift + from_rank < 1:
            raise ValueError("Shift would result in negative indices.\n" +
                             "from_rank: " + str(from_rank) + "\n" +
                             "shift: " + str(shift))

        # If no to_rank provided, assume the end of the list
        if to_rank < 1:
            to_rank = list_length

        # Shift indices
        self._dbconn.ensure_sql_connection()
        shift_command = 'UPDATE Lists SET ListIndex=ListIndex + %s ' \
                        'WHERE User=%s AND ID=%s AND ListIndex >= %s AND ListIndex <= %s;'
        shift_data = (shift, user_id, list_id, from_rank - 1, to_rank - 1)
        self._dbconn.execute(shift_command, shift_data)
        # Commit shift
        self._dbconn.commit()

    def update_list_add(self, user_id, list_id, element, rank=None):
        """ Adds an element to the list and updates other indices

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user making the edit
        list_id : str
            The id of the list being edited
        element : str
            The element to be inserted into the table
        rank : Optional - int
            The 1-indexed rank where the element will be inserted.
            If no value or None is provided, defaults to the end of the list
        """
        self._dbconn.ensure_sql_connection()
        if rank is None:
            rank = len(self.user_table[user_id][list_id])
        else:
            # Shift down the existing elements below the insertion point
            self.update_list_shift(user_id, list_id, shift=1, from_rank=rank)
        # Add the new data
        add_command = "INSERT INTO Lists VALUES (%s, %s, %s, %s)"
        add_data = (user_id, list_id, rank - 1, element)
        self._dbconn.execute(add_command, add_data)
        # Commit change
        self._dbconn.commit()

    def update_list_remove(self, user_id, list_id, rank):
        """ Removes an element from the list and updates remaining indices

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user making the edit
        list_id : str
            The id of the list being edited
        rank : int
            The 1-indexed rank of the element being removed
        """
        self._dbconn.ensure_sql_connection()
        # Remove the entry
        remove_command = "DELETE FROM Lists WHERE User=%s AND ID=%s AND ListIndex=%s"
        remove_data = (user_id, list_id, rank - 1)
        self._dbconn.execute(remove_command, remove_data)
        # Shift up the remaining elements below the removed item
        self.update_list_shift(user_id,
                               list_id,
                               shift=-1,
                               from_rank=rank + 1,
                               to_rank=len(self.user_table[user_id][list_id]) + 1)
        # Commit the change
        self._dbconn.commit()

    def update_list_move(self, user_id, list_id, from_rank, to_rank):
        """ Moves an element from one rank to another and shifts the elements in between

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user making the edit
        list_id : str
            The id of the list being edited
        from_rank : int
            The 1-indexed rank of the element being moved
        to_rank : int
            The 1-indexed rank the element is being moved to
        """
        self._dbconn.ensure_sql_connection()
        # Get the element
        element = self.user_table[user_id][list_id].contents[to_rank - 1]
        # Remove the element
        remove_command = "DELETE FROM Lists WHERE User=%s AND ID=%s AND ListIndex=%s"
        remove_data = (user_id, list_id, from_rank - 1)
        self._dbconn.execute(remove_command, remove_data)
        # Shift the elements in between
        if from_rank > to_rank:
            self.update_list_shift(user_id, list_id, shift=1, from_rank=to_rank, to_rank=from_rank)
        else:
            self.update_list_shift(user_id, list_id, shift=-1, from_rank=from_rank, to_rank=to_rank)
        # Add the element back in
        add_command = "INSERT INTO Lists VALUES (%s, %s, %s, %s)"
        add_data = (user_id, list_id, to_rank - 1, element)
        self._dbconn.execute(add_command, add_data)
        self._dbconn.commit()

    def update_list_element(self, user_id, list_id, rank, element):
        """ Updates the contents of a particular rank

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user making the edit
        list_id : str
            The id of the list being edited
        rank : int
            The 1-indexed rank of the element to update
        element : str
            The new name of the element
        """
        self._dbconn.ensure_sql_connection()
        update_command = "UPDATE Lists SET Element=%s WHERE User=%s AND ID=%s AND ListIndex=%s"
        update_data = (element, user_id, list_id, rank - 1)
        self._dbconn.execute(update_command, update_data)
        self._dbconn.commit()

    def update_list_swap(self, user_id, list_id, rank1, rank2):
        """ Swaps the rank of two elements

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user making the edit
        list_id : str
            The id of the list being edited
        rank1 : int
            The 1-indexed rank of one element being swapped
        rank2 : int
            The 1-indexed rank of the other element being swapped
        """
        self._dbconn.ensure_sql_connection()

        # Temporarily shift element at rank1 to index [-1] to prevent overlap
        update_command = "UPDATE Lists SET ListIndex=%s WHERE User=%s AND ID=%s AND ListIndex=%s"
        update_data = (-1, user_id, list_id, rank1 - 1)
        self._dbconn.execute(update_command, update_data)

        # Move element at rank2 to rank1
        update_command = "UPDATE Lists SET ListIndex=%s WHERE User=%s AND ID=%s AND ListIndex=%s"
        update_data = (rank1 - 1, user_id, list_id, rank2 - 1)
        self._dbconn.execute(update_command, update_data)

        # Move element placed at index [-1] to rank2
        update_command = "UPDATE Lists SET ListIndex=%s WHERE User=%s AND ID=%s AND ListIndex=%s"
        update_data = (rank2 - 1, user_id, list_id, -1)
        self._dbconn.execute(update_command, update_data)
        self._dbconn.commit()

    def create_list(self, user_id, list_id):
        """ Creates a list for a user

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user creating the list
        list_id : str
            The id of the list being created
        """
        self._dbconn.ensure_sql_connection()
        create_command = "INSERT INTO ListDetails VALUES (%s, %s, %s, %s)"
        create_data = (user_id, list_id, None, None)
        self.user_table[user_id][list_id] = UserList(self._bot, list_id, username=self._bot.users[user_id])
        self._dbconn.execute(create_command, create_data)
        self._dbconn.commit()

    def clear_list(self, user_id, list_id):
        """ Clears a user's list

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user
        list_id : str
            The id of the list being cleared
        """
        self._dbconn.ensure_sql_connection()
        delete_command = "DELETE FROM Lists WHERE User=%s AND ID=%s"
        delete_data = (user_id, list_id)
        self._dbconn.execute(delete_command, delete_data)
        self._dbconn.commit()

    def drop_list(self, user_id, list_id):
        """ Deletes a user's list

        Parameters
        -------------
        user_id : str
            The 18 digit user id of the user
        list_id : str
            The id of the list being dropped
        """
        self._dbconn.ensure_sql_connection()
        delete_command = "DELETE FROM Lists WHERE User=%s AND ID=%s"
        delete_data = (user_id, list_id)
        self._dbconn.execute(delete_command, delete_data)
        delete_command = "DELETE FROM ListDetails WHERE User=%s AND ID=%s"
        delete_data = (user_id, list_id)
        self._dbconn.execute(delete_command, delete_data)
        self._dbconn.commit()


def setup(bot):
    bot.add_cog(ListCommands(bot))
