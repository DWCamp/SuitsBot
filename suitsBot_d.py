#!/usr/bin/env python

# ----------- For core functionality
import discord
from discord.ext import commands
from discord import Embed
from discord.errors import NotFound

# ----------- Custom imports
from config.credentials import tokens
import embedGenerator
from scheduler import Scheduler
from dbconnection import DBConnection
from constants import *
from config.local_config import *
import utils
import parse
from cogs import images
from utils import embed_from_dict

# ------------------------ BOT VARIABLES ---------------------------------

currently_playing = "with bytes"
scribble_bank = list()

# -------------------- COMMAND WHITELIST -------------------------------

command_blacklist = {360523650912223253: ["aes",
                                          "wm",
                                          "meco",
                                          "scribble",
                                          "join",
                                          "leave",
                                          "say",
                                          "bestgirl",
                                          "anime"]}

# ------------------------ DEFINE BOT ----------------------------------


def get_prefix(client, message):
    if message.guild is None:
        return ['!', '&', '?', '%', '#', ']', '..', '.']
    elif message.guild.id in CUSTOM_PREFIXES.keys():
        return CUSTOM_PREFIXES[message.guild.id]
    else:
        return DEFAULT_COMMAND_PREFIX


bot = commands.Bot(command_prefix=get_prefix, description=BOT_DESCRIPTION, case_insensitive=True, owner_id=OWNER_ID)
utils.bot = bot  # Store the bot where other scripts can get it

# -------------------------- PERIODIC TASKS --------------------------------------


async def post_apod(curr_time):
    """
    Post the APOD to the channels defined in local_config.py
    :param curr_time: A value passed to all scheduled tasks
    """
    try:
        apod_post = await images.get_apod_embed()
        if isinstance(apod_post, str):
            for apod_channel in bot.APOD_CHANNELS:
                await apod_channel.send(apod_post)
        else:
            for apod_channel in bot.APOD_CHANNELS:
                await apod_channel.send(embed=apod_post)
    except Exception as e:
        await utils.report(bot, str(e), source="Daily APOD command")

# --------------------------- BOT EVENTS --------------------------------


@bot.event
async def on_member_join(member: discord.member):
    """ On member joining a server

    - If it joined Off-Nominal, send a DM alerting @benjaminherrin
    """
    try:
        if member.guild.id == 360523650912223253:
            # Get Ben's user object
            benjaminherrin = await bot.fetch_user(576950553289031687)
            # Send Ben the embed
            embed = Embed(title="A new user has joined Off Nominal!")
            embed.description = "Say hi!"
            embed.add_field(name="Username", value=member.name)
            embed.add_field(name="Joined on", value=member.joined_at)
            await benjaminherrin.send(embed=embed)
    except Exception as e:
        await utils.report(bot, str(e), source="on_member_join")


@bot.event
async def on_message_delete(message):
    """ On message delete:

    - Check if message was expanded by bot and, if so, delete embed
    """
    try:
        for unfurl_message_id in await embedGenerator.get_unfurls_for_trigger_message(message):
            try:
                unfurl_message = await message.channel.fetch_message(int(unfurl_message_id))
                await unfurl_message.delete()
            except NotFound:
                pass
    except Exception as e:
        await utils.report(bot, str(e), source="on_message_delete")


@bot.event
async def on_voice_state_update(member, before, after):
    """ On voice state update:

    - Leave if voice channel is now empty
    """
    try:
        # Ignore if Member wasn't leaving a channel
        if before.channel is None or before.channel is after.channel:
            return

        # Get VoiceClient for member's guild
        voice_client = member.guild.voice_client
        if voice_client is None or not voice_client.is_connected():  # Ignore if bot isn't in voice
            return

        # If there is a human user left in the channel, stay
        for member in voice_client.channel.members:
            if not member.bot:
                return
        # Otherwise, leave the channel
        voice_client.stop()
        await voice_client.disconnect()
    except Exception as e:
        await utils.report(bot, str(e), source="Voice status update")
        return


@bot.event
async def on_reaction_add(reaction, user):
    """ On a reaction added to a message:

    - If it's on an embed from SuitsBot and it's an :x: by
        the author of the message SuitsBot responded to,
        delete the embed
    """
    try:
        # Ignore reactions this bot adds
        if user == bot.user:
            return

        # Check delete emojis to see if we should delete a bot created message
        if reaction.emoji == DELETE_EMOJI:
            unfurl_message = reaction.message
            channel = unfurl_message.channel

            # Get the id of the user the embed was a response to
            unfurl_message_author_id = await embedGenerator.get_author_for_unfurl_message(unfurl_message)
            # Reject if message does not exist
            if not unfurl_message_author_id:
                return

            can_delete = False
            if unfurl_message_author_id == user.id:
                can_delete = True

            elif user.permissions_in(channel).manage_messages:
                can_delete = True

            elif reaction.count >= 6:
                can_delete = True

            if can_delete:
                try:
                    await unfurl_message.delete()
                except NotFound:
                    pass
    except Exception as e:
        await utils.report(bot, str(e), source="on_reaction_add")


@bot.event
async def on_ready():
    print('------------\nLogged in as')
    print(bot.user.name)
    print(bot.user.id)
    bot.DEV_GUILD = bot.get_guild(DEV_GUILD_ID)
    bot.DEV_CHANNEL = bot.get_channel(DEV_CHANNEL_ID)
    bot.ALERT_CHANNEL = bot.get_channel(ALERT_CHANNEL_ID)
    bot.ERROR_CHANNEL = bot.get_channel(ERROR_CHANNEL_ID)
    bot.APOD_CHANNELS = []
    for channel_id in APOD_CHANNEL_IDS:
        bot.APOD_CHANNELS.append(bot.get_channel(channel_id))
    bot.HERESY_CHANNEL = bot.get_channel(HERESY_CHANNEL_ID)
    bot.voice = None  # Voice client

    try:
        # Post restart embed
        ready_embed = Embed()
        ready_embed.title = "Bot Restart"
        ready_embed.add_field(name="Current Time", value=utils.currtime())
        ready_embed.add_field(name="discord.py version", value=str(discord.__version__), inline=False)
        ready_embed.add_field(name="Status", value="Loading Data...", inline=False)
        ready_embed.colour = EMBED_COLORS["default"]
        ready_message = await bot.DEV_CHANNEL.send(embed=ready_embed)
        status_field = len(ready_embed.fields) - 1

        """ Lists are broken, so ignore this for now """
        # # Check that data loaded well
        # for key in bot.loading_failure.keys():
        #     error = bot.loading_failure[key]
        #     report = 'Failed to load extension {}\n{}'.format(type(error).__name__, error)
        #     await utils.report(bot, 'FAILED TO LOAD {}\n{}'.format(key.upper(), report))

        # Check if added objects failed to initialize
        if isinstance(bot.regex, Exception):
            await utils.report(bot, str(bot.regex), source="Failed to load regex")
        if isinstance(bot.scheduler, Exception):
            await utils.report(bot, str(bot.scheduler), source="Failed to load scheduler")

        # Update restart embed
        ready_embed.remove_field(status_field)
        ready_embed.add_field(name="Status", value="Setting presence...", inline=False)
        await ready_message.edit(embed=ready_embed)

        print('Finalizing setup...')

        # Set presence
        try:
            await bot.change_presence(activity=discord.Game(currently_playing))
        except discord.InvalidArgument as e:
            await utils.report(bot, str(e), source="Failed to change presence")

        print('------------\nOnline!\n------------')

        ready_embed.remove_field(status_field)
        ready_embed.add_field(name="Status", value="Online!", inline=False)
        await ready_message.edit(embed=ready_embed)
    except Exception as e:
        await utils.report(bot, str(e))


@bot.event
async def on_message(message):
    # ---------------------------- HELPER METHODS
    try:
        # ------------------------------------------- FILTER OTHER BOTS
        if message.author.bot:
            return

        # ------------------------------------------- RESTART BOT
        # NOTE: NEVER ADD ANYTHING BEFORE THIS. IF THAT ADDED CODE IS BUGGED,
        # THE BOT WILL NOT BE ABLE TO RESTART
        if message.content == "!r":
            if message.author.id in AUTHORIZED_IDS:
                bot.dbconn.close()
                # if bot.is_voice_connected(message.guild):
                #     await bot.voice_client_in(message.guild).disconnect()  # Disconnect from voice
                await message.channel.send("Restarting...")
                await bot.close()
                exit(1)
            else:
                await message.channel.send("You do not have authority to restart the bot")

        # ------------------------------------------- BOT IGNORE COMMAND
        # Any message starting with "-sb" will be ignored from the bot.
        # This can be used to prevent embeds, pings, etc
        if message.content[:3].lower() == "-sb":
            return

        # ------------------------------------------- RESPOND TO EMOJI
        if message.content in ["🖐", "✋", "🤚"]:
            await message.channel.send("\*clap\* :pray:" + " **HIGH FIVE!**")
            return

        if message.content == "👈":
            await message.channel.send(":point_right: my man!")

        if message.content == "👉":
            await message.channel.send(":point_left: my man!")

        if message.content[0:8].lower() == "good bot":
            thanks = ["Thank you :smile:", "Thank you :smile:", "Aww, thanks!", ":blush:", "Oh, stop it, you :blush:",
                      "Your appreciation warms my heart :heart:"]
            await message.channel.send(utils.random_element(thanks))

        # ------------------------------------------- REACT TO MENTION
        if bot.user in message.mentions:
            await message.add_reaction(EMOJI['heart'])

        # ------------------------------------------- FILTER BLACKLISTED COMMANDS
        if message.guild is not None and message.guild.id in command_blacklist:
            if len(message.content) > 1 and message.content[0] == "!":
                spaceloc = message.content.find(" ", 2)
                if spaceloc > -1:
                    command = message.content[1:spaceloc]
                else:
                    command = message.content[1:]

                aliaslist = []
                for blockedCommand in command_blacklist[message.guild.id]:
                    aliaslist.append(blockedCommand)
                    if blockedCommand in ALIASES:
                        for alias in ALIASES[blockedCommand]:
                            aliaslist.append(alias)

                if command in aliaslist:
                    return  # Ignore blacklisted command

        # -------------------------------------------- Embed response detection
        content = message.content

        # Subreddits
        sublist = []
        matches = bot.regex.find_subreddits(content)
        for match in matches:
            sub = match[0].strip()  # Get the full match from the regex tuple
            sub_name = sub[sub.find("r/") + 2:]  # strip off "/r/"
            if sub_name not in sublist:  # Check for duplicates
                if await embedGenerator.recently_unfurled(f"{message.channel.id}-subreddits-{sub_name}"):
                    continue
                sublist.append(sub_name)
                sub_embed = None
                try:
                    sub_embed = await embedGenerator.subreddit(sub_name, message)
                    if sub_embed is not None:
                        unfurl_message = await message.channel.send(embed=sub_embed)
                        await embedGenerator.record_unfurl(message, unfurl_message)
                        await unfurl_message.add_reaction(DELETE_EMOJI)
                except Exception as e:
                    details = {} if sub_embed is None else sub_embed.to_dict()
                    await utils.report(bot, str(e) + "\n" + str(details), source='subreddit detection')
        try:
            generator_fodder = [(bot.regex.find_posts, embedGenerator.reddit_post),                 # Reddit posts
                                (bot.regex.find_comments, embedGenerator.reddit_comment),           # Reddit comments
                                # (bot.regex.find_twitter_handle, embedGenerator.twitter_handle),   # Twitter handles
                                # (bot.regex.find_twitter_id, embedGenerator.twitter_images),       # Images from tweets
                                (bot.regex.find_twitter_id, embedGenerator.twitter_response),       # Response to tweets
                                (bot.regex.find_newegg, embedGenerator.newegg),                     # Newegg links
                                (bot.regex.find_discord_message, embedGenerator.discord_message)    # Discord msg link
                                ]
            for (regex, generator) in generator_fodder:
                for embed in await embedGenerator.embeds_from_regex(regex(content), generator, message):
                    unfurl_message = await message.channel.send(embed=embed)
                    try:
                        await embedGenerator.record_unfurl(message, unfurl_message)
                    except Exception as e:
                        await utils.report(bot, str(e), source="Recording unfurl to redis DB in on_message")
                    await unfurl_message.add_reaction(DELETE_EMOJI)
        except Exception as e:
            await utils.report(bot,
                               f"{e}\n**Server:** {message.guild}\n**Message:** ```{message.content}```",
                               source="embed generation in on_message")

        # ------------------------------------------------------------

        await bot.process_commands(message)
    except Exception as e:
        await utils.report(bot, f"{e}\nServer: {message.guild}\nMessage: {message.content}", source="on_message")


# ------------------------ GENERAL COMMANDS ---------------------------------


@bot.command(help=LONG_HELP['aes'], brief=BRIEF_HELP['aes'], aliases=ALIASES['aes'])
async def aes(ctx):
    try:
        message = ctx.message.content[5:].strip().upper()
        if len(message) == 0:
            await ctx.send("I'll need a message to meme-ify (e.g. `!aes Aesthetic`)?")
        elif len(message) > 100:
            await ctx.send("I'm not reading your novel, Tolstoy.\n(Message length: " + str(len(message)) + ")")
            return
        elif len(message) > 50:
            await ctx.send(
                "You should have realized that wasn't going to work.\n(Message length: " + str(len(message)) + ")")
            return
        elif len(message) > 25:
            await ctx.send(
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
            await ctx.send(aesthetic_message)
    except Exception as e:
        await utils.report(bot, str(e), source="aes command", ctx=ctx)
        return


@bot.command(hidden=True)
async def claire(ctx):
    try:
        await ctx.send("The `!claire` command has been retired on account of Claire no longer being a virgin.")
    except Exception as e:
        await utils.report(bot, str(e), source="!claire command")


@bot.group(hidden=True)
async def dev(ctx):
    global currently_playing
    try:
        if ctx.author.id not in AUTHORIZED_IDS:
            await ctx.send("You are not authorized to use these commands")
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
            await ctx.send("`!dev` User Guide", embed=embed_from_dict(helpdict, title=title, description=description))

        elif func == "channelid":
            await ctx.send("Channel ID: " + ctx.channel.id)

        elif func == "dump":
            await ctx.send("hello")

        elif func == "flag":
            await ctx.send("Triggering flag...")
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
            await ctx.send("`` {} `` loaded.".format(parameter))

        elif func == "nick":
            try:
                if ctx.guild is None:
                    await ctx.send("I can't do that here")
                    return
                new_nick = parameter
                if new_nick == "":
                    new_nick = None
                bot_member = ctx.guild.get_member(tokens["CLIENT_ID"])
                await bot.change_nickname(bot_member, new_nick)
            except Exception as e:
                await utils.report(bot, str(e), source="!dev nick", ctx=ctx)

        elif func == "playing":
            try:
                currently_playing = parameter
                await bot.change_presence(game=discord.Game(name=currently_playing))
                utils.update_cache(bot.dbconn, "currPlaying", currently_playing)
                await ctx.send("I'm now playing `" + parameter + "`")
            except discord.InvalidArgument as e:
                await utils.report(bot,
                                   "Failed to change presence to `" + parameter + "`\n" + str(e),
                                   source="dev playing",
                                   ctx=ctx)

        elif func == "serverid":
            await ctx.send("Server ID: " + ctx.guild.id)

        elif func == "reload":
            bot.unload_extension(parameter)
            await ctx.send("`` {} `` unloaded.".format(parameter))
            try:
                bot.load_extension("cogs." + parameter)
            except (AttributeError, ImportError) as e:
                await utils.report(bot,
                                   "```py\n{}: {}\n```".format(type(e).__name__, str(e)),
                                   source="Loading extension (!dev)",
                                   ctx=ctx)
                return
            await ctx.send("`` {} `` loaded.".format(parameter))

        elif func == "report":
            await ctx.send("Triggering report...")
            await utils.report(bot, "This is a test of the report system", source="dev report command", ctx=ctx)

        elif func == "test":
            try:
                await ctx.send("hello")
            except Exception as e:
                await utils.report(bot, str(e), source="dev test", ctx=ctx)

        elif func == "unload":
            """ Unoads an extension """
            bot.unload_extension(parameter)
            await ctx.send("`` {} `` unloaded.".format(parameter))

        else:
            await ctx.send("I don't recognize the command `" + func + "`. You can type `!dev` for a list of " +
                          "available functions")
    except Exception as e:
        await utils.report(bot, str(e), source="dev command", ctx=ctx)


@bot.command(help=LONG_HELP['hello'], brief=BRIEF_HELP['hello'], aliases=ALIASES['hello'])
async def hello(ctx):
    greetings = ["Hello!", "Greetings, friend!", "How's it going?", "What's up?", "Yo.", "Hey.", "Sup.", "Howdy"]
    await ctx.send(utils.random_element(greetings))


@bot.command(aliases=['skribbl', 'scrib', 's'])
async def scribble(ctx):
    global scribble_bank
    try:
        (arguments, message) = parse.args(ctx.message.content)
        value = message.lower()

        if "ls" in arguments or len(value) == 0:
            await ctx.send(", ".join(scribble_bank))
            return
        if "rm" in arguments:
            if value not in scribble_bank:
                await ctx.send("I don't have the term `" + value + "` saved to my list")
            else:
                scribble_bank.remove(value)
                await ctx.send("Alright, I removed `" + message + "` from my list")
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
            await ctx.send("Alright, I recorded " + ", ".join([("`" + i + "`") for i in added]))
        if len(rejected) == 1:
            await ctx.send("`" + rejected[0] + "` was rejected as a duplicate")
        elif len(rejected) > 2:
            await ctx.send(", ".join([("`" + i + "`") for i in rejected]) + " were rejected as duplicates")
    except Exception as e:
        await utils.report(bot, str(e), source="scribble")


@bot.command(hidden=True, aliases=["reee", "reeee", "reeeee"])
async def ree(ctx):
    await ctx.send("***REEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
                   "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE***")


# --------------------- LOADING DB ----------------------------------


def load():
    """ Load everything """
    load_cache()


def load_cache():
    """ Load Cache values from database """
    global currently_playing, scribble_bank
    try:
        currently_playing = utils.load_from_cache(bot.dbconn, "currPlaying", "")
        scribble_bank = utils.load_from_cache(bot.dbconn, "scribble", "").split(',')
    except Exception as e:
        bot.loading_failure["cache"] = e


# -----------------------   START UP   -----------------------------------

# Create MySQL connection
bot.dbconn = DBConnection(tokens["MYSQL_USER"], tokens["MYSQL_PASSWORD"], "suitsBot")
bot.loading_failure = {}

# # Load opus library
# if not discord.opus.is_loaded():
#     discord.opus.load_opus('opus')

print("\n\n------------")
print('Loading Data...')

# Load data from database
load()

print("Loading cogs...")

# Load cogs
startup_extensions = LOCAL_COGS
startup_extensions += ['cogs.anilist',
                       'cogs.code',
                       'cogs.images',
                       'cogs.rsscrawler',
                       'cogs.rand',
                       'cogs.tags',
                       'cogs.voice',
                       'cogs.webqueries']

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
            print('Loaded extension "' + extension + '"')
        except discord.ClientException as err:
            exc = '{}: {}'.format(type(err).__name__, err)
            print('Failed to load extension {}\n{}'.format(extension, exc))

# Add regex parser
print("Building regex...")
try:
    bot.regex = parse.Regex(bot)
except Exception as exc:
    print("--- Failed to build regex ---")
    bot.regex = exc

# Add task scheduler
print('Scheduling tasks...')
try:
    bot.scheduler = Scheduler(bot)
    bot.scheduler.add_daily_task(post_apod)
except Exception as exc:
    print("--- Failed to start scheduler! ---")
    bot.scheduler = exc

# Start the bot
print("------------")
print("Logging in...")
bot.run(tokens["BOT_TOKEN"])
