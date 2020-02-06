#!/usr/bin/env python

# ----------- For core functionality
import discord
from discord.ext import commands
from discord import Embed
import sys

# ----------- Custom imports
import credentials
import embedGenerator
from scheduler import Scheduler
from dbconnection import DBConnection
from constants import *
import utils
import parse
from utils import embedfromdict

# ------------------------ BOT CONSTANTS ---------------------------------

# File paths
AUTH_FILE_PATH = "/home/dwcamp/suitsBotOAuth.txt"

DEV_CHANNEL_ID = '341428321109671939'
ALERT_CHANNEL_ID = '458462631397818369'
ERROR_CHANNEL_ID = '455185027429433344'
DEV_SERVER_ID = '219267501362642944'
HERESY_CHANNEL_ID = '427619361222557698'

# Command constants
RESERVED_LIST_IDS = ["BestGirl"]

# ---------------------------- MY SQL ------------------------------------

GLOBAL_TAG_OWNER = "----GLOBAL TAG----"

# ------------------------ GEN VARIABLES ---------------------------------

currently_playing = "with bytes"

scribble_bank = list()

# -------------------- COMMAND WHITELIST -------------------------------

command_whitelist = {"360523650912223253": ["help",
                                            "code",
                                            "dev",
                                            "gritty",
                                            "nasa",
                                            "meco",
                                            "meow",
                                            "on",
                                            "rand",
                                            "ud",
                                            "wiki",
                                            "wm",
                                            "wolf",
                                            "woof",
                                            "youtube"]}

# ------------------------ DEFINE BOT ----------------------------------


def get_prefix(client, message):
    if message.server is None:
        return ['!', '&', '?', '%', '#', ']', '..', '.']
    elif message.server.id in PREFIXES.keys():
        return PREFIXES[message.server.id]
    else:
        return '!'


bot = commands.Bot(command_prefix=get_prefix, description=BOT_DESCRIPTION)

# -------------------------- PERIODIC TASKS --------------------------------------


async def post_apod(curr_time):
    try:
        embed_icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/" +\
                     "1200px-NASA_logo.svg.png"
        api_url = "https://api.nasa.gov/planetary/apod?api_key=OSoqPlD9uDBXvXXpn4ybhFt1ulflqtmGtQnkLgAD"
        [json, status_code] = await utils.get_json_with_get(api_url)
        if status_code != 200:
            await utils.report(bot,
                               "Error with !nasa, response code " + str(status_code) + "\n" + str(json),
                               source="NASA APOD command")
            return
        if json['media_type'] == "video":
            await bot.send_message(bot.SUITS_SPACE, "**{}**\n{}\n{}".format(json['title'], json['explanation'], json['url']))
        else:
            embed = Embed().set_image(url=json['hdurl'])
            embed.title = json['title']
            embed.description = json['explanation']
            embed.set_footer(icon_url=embed_icon,
                             text="NASA Astronomy Photo of the Day https://apod.nasa.gov/apod/astropix.html")
            embed.colour = EMBED_COLORS["nasa"]
            await bot.send_message(bot.SUITS_SPACE, embed=embed)
    except Exception as e:
        await utils.report(bot, str(e), source="Daily APOD command")

# --------------------------- BOT EVENTS --------------------------------


@bot.event
async def on_member_join(member: discord.member):
    # If member of Off-Nominal server
    if member.server.id == "360523650912223253":
        # Get Ben's user object
        benjaminherrin = await bot.get_user_info("576950553289031687")
        # Send Ben the embed
        embed = Embed(title="A new user has joined Off Nominal!")
        embed.description = "Say hi!"
        embed.add_field(name="Username", value=member.name)
        embed.add_field(name="Joined on", value=member.joined_at)
        await bot.send_message(benjaminherrin, embed=embed)


@bot.event
async def on_ready():
    print('------------\nLogged in as')
    print(bot.user.name)
    print(bot.user.id)
    bot.DEV_SERVER = bot.get_server("219267501362642944")
    bot.DEV_CHANNEL = bot.get_channel("341428321109671939")
    bot.ALERT_CHANNEL = bot.get_channel("458462631397818369")
    bot.ERROR_CHANNEL = bot.get_channel("455185027429433344")
    bot.SUITS_GENERAL = bot.get_channel("349040456530657280")
    bot.SUITS_SPACE = bot.get_channel("601096185666863125")
    bot.HERESY_CHANNEL = bot.get_channel("427619361222557698")
    bot.NOMINAL_HISTORY = bot.get_channel("417876694813245441")
    bot.player = None

    try:
        # Post restart embed
        ready_embed = Embed()
        ready_embed.title = "Bot Restart"
        ready_embed.add_field(name="Current Time", value=utils.currtime())
        if len(sys.argv) == 1:
            ready_embed.add_field(name="Previous Exit Code", value="Starting from cold boot")
            ready_embed.add_field(name="Assumed cause of reboot", value="N/A")
        else:
            ready_embed.add_field(name="Previous Exit Code", value=str(sys.argv[1]))
            if sys.argv[1] == "1" or sys.argv[1] == "120":
                ready_embed.add_field(name="Assumed cause of reboot", value="Use of `!r`")
            else:
                ready_embed.add_field(name="Assumed cause of reboot", value="Random bug")
        ready_embed.add_field(name="Status", value="Loading Data...", inline=False)
        ready_embed.colour = EMBED_COLORS["default"]
        ready_message = await bot.send_message(bot.DEV_CHANNEL, embed=ready_embed)

        # Check that data loaded well
        for key in bot.loading_failure.keys():
            error = bot.loading_failure[key]
            report = 'Failed to load extension {}\n{}'.format(type(error).__name__, error)
            await utils.report(bot, 'FAILED TO LOAD {}\n{}'.format(key.upper(), report))

        # Update restart embed
        ready_embed.remove_field(3)
        ready_embed.add_field(name="Status", value="Loading web services...", inline=False)
        await bot.edit_message(ready_message, embed=ready_embed)

        print('Compiling Regex...')

        # Update restart embed
        ready_embed.remove_field(3)
        ready_embed.add_field(name="Status", value="Compiling Regex...", inline=False)
        await bot.edit_message(ready_message, embed=ready_embed)

        bot.regex = parse.Regex(bot)

        print('Scheduling tasks...')

        try:
            # Update restart embed
            ready_embed.remove_field(3)
            ready_embed.add_field(name="Status", value="Scheduling tasks...", inline=False)
            await bot.edit_message(ready_message, embed=ready_embed)

            bot.scheduler = Scheduler(bot)
            bot.scheduler.add_daily_task(post_apod)

        except Exception as e:
            await utils.report(bot, str(e), source="Failed to start scheduler")

        print('Finalizing setup...')

        # Load/initialize web content
        try:
            await bot.change_presence(game=discord.Game(name=currently_playing))
        except discord.InvalidArgument as e:
            await utils.report(bot, str(e), source="Failed to change presence")

        print('------------\nOnline!\n------------')

        ready_embed.remove_field(3)
        ready_embed.add_field(name="Status", value="Online!", inline=False)
        await bot.edit_message(ready_message, embed=ready_embed)
    except Exception as e:
        await utils.report(bot, str(e))


@bot.event
async def on_message(message):
    # ---------------------------- HELPER METHODS
    try:
        # ------------------------------------------- FILTER OTHER BOTS
        if message.author == bot.user:
            return

        if message.author.bot:
            return

        # ------------------------------------------- RESTART BOT
        # NOTE: NEVER ADD ANYTHING BEFORE THIS. IN THE EVENT THAT THE ADDED CODE IS BUGGED,
        # THE BOT WILL NOT BE ABLE TO RESTART
        if message.content == "!r":
            if message.author.id in AUTHORIZED_IDS:
                bot.dbconn.close()
                if bot.is_voice_connected(message.server):
                    await bot.voice_client_in(message.server).disconnect()  # Disconnect from voice
                await bot.send_message(message.channel, "Restarting...")
                await bot.close()
                sys.exit(1)
            else:
                await bot.send_message(message.channel, "You do not have authority to restart the bot")

        # ------------------------------------------- BOT IGNORE COMMAND
        # Any message starting with "-sb" will be ignored from the bot.
        # This can be used to prevent embeds, pings, etc
        if message.content[:3].lower() == "-sb":
            return

        # ------------------------------------------- LIST ENGINE
        # Add author to user table and ListEngine if missing
        authorid = message.author.id
        authorname = message.author.name
        # If user missing from user table
        try:
            if authorid not in bot.users.keys() and "users" not in bot.loading_failure.keys():
                sqlname = ''
                for char in authorname:
                    if char.lower() in "abcdefghijklmnopqrstuvwxyz1234567890 ?\\/\'\",.[]\{\}|!@#$%^&*()`~":
                        sqlname += char
                    else:
                        sqlname += '?'
                add_user(authorid, sqlname)
                await utils.flag(bot,
                                 "Added new user on server",
                                 description=str(authorid) + ":" + message.author.name,
                                 message=message)
        except Exception as e:
            await utils.report(bot,
                               str(e),
                               source=f"Failed to add user `{authorname}` to server {message.server.id}, tried with {sqlname}")

        # If user missing from list engine
        if authorid not in bot.list_engine.user_table.keys():
            bot.list_engine.add_user(authorid)
            await utils.flag(bot,
                             "Added user to list engine",
                             description=str(authorid) + ":" + message.author.name,
                             message=message)
        # If user missing bestgirl list
        if "BestGirl" not in bot.list_engine.user_table[authorid].keys():
            bot.list_engine.create_list(authorid, "BestGirl")
            await utils.flag(bot,
                             "Added missing BestGirl list to user",
                             description=str(authorid) + ":" + message.author.name,
                             message=message)

        # ------------------------------------------- RESPOND TO EMOJI
        if message.content in ["🖐", "✋", "🤚"]:
            await bot.send_message(message.channel, "\*clap\* :pray:" + " **HIGH FIVE!**")
            return

        if message.content == "👈":
            await bot.send_message(message.channel, ":point_right: my man!")

        if message.content == "👉":
            await bot.send_message(message.channel, ":point_left: my man!")

        if message.content[0:8].lower() == "good bot":
            thanks = ["Thank you :smile:", "Thank you :smile:", "Aww, thanks!", ":blush:", "Oh, stop it, you :blush:",
                      "Your appreciation warms my heart :heart:"]
            await bot.send_message(message.channel, utils.random_element(thanks))

        # ------------------------------------------- FILTER UN-WHITELISTED COMMANDS
        if message.server is not None and message.server.id in command_whitelist:
            if len(message.content) > 1 and message.content[0] == "!":
                spaceloc = message.content.find(" ", 2)
                if spaceloc > -1:
                    command = message.content[1:spaceloc]
                else:
                    command = message.content[1:]

                aliaslist = []
                for allowedCommand in command_whitelist[message.server.id]:
                    aliaslist.append(allowedCommand)
                    if allowedCommand in ALIASES:
                        for alias in ALIASES[allowedCommand]:
                            aliaslist.append(alias)

                if command not in aliaslist:
                    return

        # -------------------------------------------- Embed response detection
        content = message.content

        # Subreddits
        sublist = []
        matches = bot.regex.find_subreddits(content)
        for match in matches:
            sub = match[0].strip()  # Get the full match from the regex tuple
            subname = sub[sub.find("r/") + 2:]  # strip off "/r/"
            if subname not in sublist:  # Check for duplicates
                if await embedGenerator.recently_unfurled(f"{message.channel.id}-subreddits-{subname}"):
                    continue
                sublist.append(subname)
                subembed = None
                try:
                    subembed = await embedGenerator.subreddit(subname)
                    if subembed is not None:
                        await bot.send_message(message.channel, embed=subembed)
                except Exception as e:
                    details = {} if subembed is None else subembed.to_dict()
                    await utils.report(bot, str(e) + "\n" + str(details), source='subreddit detection')

        try:
            generator_fodder = [(bot.regex.find_posts, embedGenerator.reddit_post),  # Reddit posts
                                (bot.regex.find_comments, embedGenerator.reddit_comment),  # Reddit comments
                                # (bot.regex.find_twitter_handle, embedGenerator.twitter_handle),  # Twitter handles
                                # (bot.regex.find_twitter_id, embedGenerator.twitter_images),  # Images from tweets
                                (bot.regex.find_twitter_id, embedGenerator.twitter_response),  # Response to tweets
                                (bot.regex.find_amazon, embedGenerator.amazon),  # Amazon links
                                (bot.regex.find_newegg, embedGenerator.newegg)]  # Newegg links

            for (regex, generator) in generator_fodder:
                for embed in await embedGenerator.embeds_from_regex(regex(content), generator, message):
                    await bot.send_message(message.channel, embed=embed)

        except Exception as e:
            await utils.report(bot, str(e), source="embed generation in on_message")

        # ------------------------------------------------------------

        await bot.process_commands(message)
    except Exception as e:
        await utils.report(bot, str(e), source="on_message")


# ----------------------------- EVENTS --------------------------------------

@bot.event
async def on_voice_state_update(before, after):
    try:
        if after.voice.voice_channel is None and bot.is_voice_connected(before.server):
            if len(bot.voice_client_in(after.server).channel.voice_members) == 1:
                await bot.voice_client_in(after.server).disconnect()
    except Exception as e:
        await utils.report(bot, str(e), source="Voice status update")
        return

# ------------------------ GENERAL COMMANDS ---------------------------------


@bot.command(pass_context=True, help=LONG_HELP['aes'], brief=BRIEF_HELP['aes'], aliases=ALIASES['aes'])
async def aes(ctx):
    try:
        message = ctx.message.content[5:].strip().upper()
        if len(message) == 0:
            await bot.say("I'll need a message to meme-ify (e.g. `!aes Aesthetic`)?")
        elif len(message) > 100:
            await bot.say("I'm not reading your novel, Tolstoy.\n(Message length: " + str(len(message)) + ")")
            return
        elif len(message) > 50:
            await bot.say(
                "You should have realized that wasn't going to work.\n(Message length: " + str(len(message)) + ")")
            return
        elif len(message) > 25:
            await bot.say(
                "I'm not clogging up the server feed with your drivel\n(Message length: " + str(len(message)) + ")")
            return
        else:
            aesthetic_message = ""
            for char in message:
                aesthetic_message += "**" + char + "** "
            counter = 0
            for char in message:
                if char in ["_", "-"]:
                    char = "|"
                elif char == "|":
                    char = "—"

                if counter > 0:
                    aesthetic_message += "\n**" + char + "**"
                counter += 1
            await bot.say(aesthetic_message)
    except Exception as e:
        await utils.report(bot, str(e), source="aes command", ctx=ctx)
        return


@bot.command(hidden=True)
async def claire():
    try:
        await bot.say("The `!claire` command has been retired on account of Claire no longer being a virgin.")
    except Exception as e:
        await utils.report(bot, str(e), source="!claire command")


@bot.group(pass_context=True, hidden=True, )
async def dev(ctx):
    global currently_playing
    try:
        if ctx.message.author.id not in AUTHORIZED_IDS:
            await bot.say("You are not authorized to use these commands")
            return

        [func, parameter] = parse.func_param(ctx.message.content)

        if func in ["help", ""]:
            title = "`!dev` User Guide"
            description = "A list of features useful for "
            helpdict = {
                "channelid": "Posts the ID of the current channel",
                "dump": "A debug command for the bot to dump a variable into chat",
                "flag": "Tests the `flag` function",
                "load": "Loads an extension",
                "playing": "Sets the presence of the bot (what the bot says it's currently playing)",
                "reload": "Reloads an extension",
                "report": "Tests the `report` function",
                "serverid": "Posts the ID of the current channel",
                "test": "A catch-all command for inserting code into the bot to test",
            }
            await bot.say("`!dev` User Guide", embed=embedfromdict(helpdict, title=title, description=description))

        elif func == "channelid":
            await bot.say("Channel ID: " + ctx.message.channel.id)

        elif func == "dump":
            await bot.say("AT THE DUMP")

        elif func == "flag":
            await bot.say("Triggering flag...")
            await utils.flag(bot, "Test", description="This is a test of the flag ability", ctx=ctx)

        elif func == "load":
            """Loads an extension."""
            try:
                bot.load_extension("cogs." + parameter)
            except (AttributeError, ImportError) as e:
                await utils.report(bot,
                                   "```py\n{}: {}\n```".format(type(e).__name__, str(e)),
                                   source="Loading extension (!dev)",
                                   ctx=ctx)
                return
            await bot.say("`` {} `` loaded.".format(parameter))

        elif func == "nick":
            try:
                if ctx.message.server is None:
                    await bot.say("I can't do that here")
                    return
                newnick = parameter
                if newnick == "":
                    newnick = None
                botmember = ctx.message.server.get_member("340287898433748993")  # Gets the bot's own member object
                await bot.change_nickname(botmember, newnick)
            except Exception as e:
                await utils.report(bot, str(e), source="!dev nick", ctx=ctx)

        elif func == "playing":
            try:
                currently_playing = parameter
                await bot.change_presence(game=discord.Game(name=currently_playing))
                utils.update_cache(bot.dbconn, "currPlaying", currently_playing)
                await bot.say("I'm now playing `" + parameter + "`")
            except discord.InvalidArgument as e:
                await utils.report(bot,
                                   "Failed to change presence to `" + parameter + "`\n" + str(e),
                                   source="dev playing",
                                   ctx=ctx)

        elif func == "serverid":
            await bot.say("Server ID: " + ctx.message.server.id)

        elif func == "reload":
            bot.unload_extension(parameter)
            await bot.say("`` {} `` unloaded.".format(parameter))
            try:
                bot.load_extension("cogs." + parameter)
            except (AttributeError, ImportError) as e:
                await utils.report(bot,
                                   "```py\n{}: {}\n```".format(type(e).__name__, str(e)),
                                   source="Loading extension (!dev)",
                                   ctx=ctx)
                return
            await bot.say("`` {} `` loaded.".format(parameter))

        elif func == "report":
            await bot.say("Triggering report...")
            await utils.report(bot, "This is a test of the report system", source="dev report command", ctx=ctx)

        elif func == "test":
            try:
                await bot.say("hello")
            except Exception as e:
                await utils.report(bot, str(e), source="dev test", ctx=ctx)

        elif func == "unload":
            """ Unoads an extension """
            bot.unload_extension(parameter)
            await bot.say("`` {} `` unloaded.".format(parameter))

        else:
            await bot.say("I don't recognize the command `" + func + "`. You can type `!dev` for a list of " +
                          "available functions")
    except Exception as e:
        await utils.report(bot, str(e), source="dev command", ctx=ctx)


@bot.command(help=LONG_HELP['hello'], brief=BRIEF_HELP['hello'], aliases=ALIASES['hello'])
async def hello():
    greetings = ["Hello!", "Greetings, friend!", "How's it going?", "What's up?", "Yo.", "Hey.", "Sup.", "Howdy"]
    await bot.say(utils.random_element(greetings))


@bot.command(pass_context=True, aliases=['skribbl', 'scrib', 's'])
async def scribble(ctx):
    global scribble_bank
    try:
        (arguments, message) = parse.args(ctx.message.content)
        value = message.lower()

        if "ls" in arguments or len(value) == 0:
            await bot.say(", ".join(scribble_bank))
            return
        if "rm" in arguments:
            if value not in scribble_bank:
                await bot.say("I don't have the term `" + value + "` saved to my list")
            else:
                scribble_bank.remove(value)
                await bot.say("Alright, I removed `" + message + "` from my list")
            return

        if "," not in value:
            value_list = [value]
        else:
            value_list = [i.strip() for i in value.split(",")]

        added = list()
        rejected = list()
        for value in value_list:
            if value in scribble_bank:
                rejected.append(value)
            else:
                scribble_bank.append(value)
                added.append(value)
        utils.update_cache(bot.dbconn, "scribble", ",".join(scribble_bank))
        if len(added) > 0:
            await bot.say("Alright, I recorded " + ", ".join([("`" + i + "`") for i in added]))
        if len(rejected) == 1:
            await bot.say("`" + rejected[0] + "` was rejected as a duplicate")
        elif len(rejected) > 2:
            await bot.say(", ".join([("`" + i + "`") for i in rejected]) + " were rejected as duplicates")
    except Exception as e:
        await utils.report(bot, str(e), source="scribble")


@bot.command(hidden=True, aliases=["REE", "reee", "reeee", "reeeee"])
async def ree():
    await bot.say("***REEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
                  "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE***")


# ------------------- UPDATE MYSQL DB -------------------------------

def add_user(user_id, username):
    """ Adds a user to the database

    Parameters
    -------------
    user_id : str
        The 18 digit user id of the user
    username : str
        The Discord name of the user
    """
    bot.dbconn.ensure_sql_connection()
    # Add user to user table
    add_user_command = "INSERT INTO Users VALUES (%s, %s)"
    add_user_data = (user_id, username)
    bot.dbconn.execute(add_user_command, add_user_data)
    bot.users[user_id] = username

    # Add the user to the list engine
    bot.list_engine.add_user(user_id)

    bot.dbconn.commit()


# --------------------- LOADING DB ----------------------------------


def load():
    """ Load everything """
    loadusers()
    loadcache()


def loadusers():
    """ Load user table from database """
    try:
        bot.users = {}
        query = "SELECT * FROM Users"
        cursor = bot.dbconn.execute(query)
        for (ID, Name) in cursor:
            bot.users[ID] = Name
    except Exception as e:
        bot.loading_failure["users"] = e


def loadcache():
    """ Load Cache values from database """
    global currently_playing, scribble_bank
    try:
        currently_playing = utils.loadfromcache(bot.dbconn, "currPlaying", "")
        scribble_bank = utils.loadfromcache(bot.dbconn, "scribble", "").split(',')
    except Exception as e:
        bot.loading_failure["cache"] = e


# -----------------------   START UP   -----------------------------------

# load all Discord, MySQL, and API credentials
tokenFile = open(AUTH_FILE_PATH, "r", encoding="utf-8")
tokenLines = tokenFile.read().splitlines()
tokens = {}
for line in tokenLines:
    key_value = line.split(":")
    tokens[key_value[0]] = key_value[1]
credentials.set_tokens(tokens)

# Create MySQL connection
bot.dbconn = DBConnection(credentials.tokens["MYSQL_USER"], credentials.tokens["MYSQL_PASSWORD"], "suitsBot")
bot.loading_failure = {}

# Load opus library
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

print("\n\n------------")
print('Loading Data...')

# Load data from database
load()

print("Loading cogs...")

# Load cogs
startup_extensions = ['cogs.anilist',
                      'cogs.code',
                      'cogs.images',
                      'cogs.listcommands',
                      'cogs.podcasts',
                      'cogs.rand',
                      'cogs.tags',
                      'cogs.voice',
                      'cogs.webqueries',
                      'cogs.yiff']

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
            print('Loaded extension "' + extension + '"')
        except discord.ClientException as err:
            exc = '{}: {}'.format(type(err).__name__, err)
            print('Failed to load extension {}\n{}'.format(extension, exc))

print("------------")
print("Logging in...")

# Start the bot
bot.run(credentials.tokens["BOT_TOKEN"])
