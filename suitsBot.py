#!/usr/bin/env python

# ----------- For core functionality
import discord
from discord.ext import commands
from discord import Embed
import sys
# ----------- For commands
from datetime import datetime
import re
# ----------- Custom imports
import embedGenerator
from dbconnection import DBConnection
from constants import *
import utils
import parse
from utils import embedfromdict

# ------------------------ BOT CONSTANTS ---------------------------------

# File paths
AUTH_FILE_PATH = "PythonScripts/suitsBotOAuth.txt"

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

swear_tally = {}

last_colton = None
daily_colton = None
total_colton = None

# ------------------------ DEFINE BOT ----------------------------------


def get_prefix(client, message):
		if message.server is None:
				return ['!', '&', '?', '%', '#', ']', '..', '.']
		elif message.server.id in PREFIXES.keys():
				return PREFIXES[message.server.id]
		else:
				return '!'


bot = commands.Bot(command_prefix=get_prefix, description=BOT_DESCRIPTION)

# --------------------------- BOT EVENTS ------------------------------------


@bot.event
async def on_ready():
		print('------------\nLogged in as')
		print(bot.user.name)
		print(bot.user.id)
		bot.DEV_SERVER = bot.get_server("219267501362642944")
		bot.DEV_CHANNEL = bot.get_channel("341428321109671939")
		bot.ALERT_CHANNEL = bot.get_channel("458462631397818369")
		bot.ERROR_CHANNEL = bot.get_channel("455185027429433344")
		bot.HERESY_CHANNEL = bot.get_channel("427619361222557698")
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
		global swear_tally

		# ---------------------------- HELPER METHODS
		try:
				# -------------------------------------------
				if message.author == bot.user:
						return

				if message.author.bot:
						return

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
				if message.content == "!gn":
						if message.author.id in AUTHORIZED_IDS:
								bot.dbconn.close()
								if bot.is_voice_connected(message.server):
										await bot.voice_client_in(message.server).disconnect()  # Disconnect from voice
								await bot.send_message(message.channel, "Goodbye...")
								await bot.close()
								sys.exit(0)
						else:
								await bot.send_message(message.channel, "You do not have authority to terminate the bot")
						return

				authorid = message.author.id
				authorname = message.author.name
				if authorid not in bot.users.keys() and "users" not in bot.loading_failure.keys():
						await utils.flag(bot,
														 "Added new user on server",
														 description=str(authorid) + ":" + message.author.name,
														 message=message)
						add_user(authorid, authorname)

				if message.content in ["🖐", "✋", "🤚"]:
						await bot.send_message(message.channel, "\*clap\* :pray:" + " **HIGH FIVE!**")
						return

				if message.content == "👈":
						await bot.send_message(message.channel, ":point_right: my man!")

				if message.content == "👉":
						await bot.send_message(message.channel, ":point_left: my man!")

				if message.content[0:8].lower() == "good bot":
						await bot.send_message(message.channel, "Thank you :smile:")

				# -------------------------------------------- Parsing reddit values
				content = message.content

				# Subreddits
				sublist = []
				matches = bot.regex.find_subreddits(content)
				for match in matches:
						sub = match[0].strip()  # Get the full match from the regex tuple
						subname = sub[sub.find("r/") + 2:]  # strip off "/r/"
						if subname not in sublist:  # Check for duplicates
								sublist.append(subname)
								subembed = None
								try:
										subembed = await embedGenerator.subreddit(subname)
										if subembed is not None:
												await bot.send_message(message.channel, embed=subembed)
								except Exception as e:
										details = {} if subembed is None else subembed.to_dict()
										await utils.report(bot, str(e) + "\n" + str(details), source='subreddit detection')

				# Post links
				for embed in await embedGenerator.embeds_from_regex(bot.regex.find_posts(content), embedGenerator.reddit_post):
						await bot.send_message(message.channel, embed=embed)

				# Comment permalinks
				for embed in await embedGenerator.embeds_from_regex(bot.regex.find_comments(content),
																														embedGenerator.reddit_comment):
						await bot.send_message(message.channel, embed=embed)

				# -------------------------------------------- Amazon Links
				for embed in await embedGenerator.embeds_from_regex(bot.regex.find_amazon(content), embedGenerator.amazon):
						await bot.send_message(message.channel, embed=embed)

				# -------------------------------------------- Newegg Links
				for embed in await embedGenerator.embeds_from_regex(bot.regex.find_newegg(content), embedGenerator.newegg):
						await bot.send_message(message.channel, embed=embed)

				# -------------------------------------------- Counting Swears
				try:
						if message.channel.id != DEV_CHANNEL_ID:
								words = message.content.split()
								swears = 0
								for word in words:
										if bot.regex.is_swear(word):
												swears += 1
								if message.author.id not in swear_tally.keys():
										swear_tally[message.author.id] = [0, 0, 0.0]
										add_user_swears(message.author.id)
								talleyarray = swear_tally[message.author.id]
								talleyarray[0] += len(words)
								talleyarray[1] += swears
								talleyarray[2] = talleyarray[1] / float(talleyarray[0])
								update_user_swears(message.author.id)
				except Exception as e:
						await utils.report(bot, str(e), source="swear detection")
						return

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
						await bot.say("I'm not reading your novel, boy.\n(Message length: " + str(len(message)) + ")")
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


@bot.command(help=LONG_HELP['colton'], brief=BRIEF_HELP['colton'], aliases=ALIASES['colton'], hidden=True)
async def colton():
		global last_colton, daily_colton, total_colton
		try:
				total_colton += 1
				now = datetime.now()
				if last_colton.day != now.day:
						daily_colton = 1
						timestoday = ", which makes this his first time today"
				else:
						daily_colton += 1
						timestoday = ", which makes this " + str(daily_colton) + " times today alone!"
				await bot.say("Wow! Colton has now mentioned being forever alone {} times!\n"
											"The last time he mentioned being forever alone was **{}**"
											.format(total_colton, last_colton.strftime("%c")) + timestoday)
				last_colton = now
				utils.update_cache(bot.dbconn, "lastColton", last_colton.strftime("%s"))
				utils.update_cache(bot.dbconn, "dailyColton", str(daily_colton))
				utils.update_cache(bot.dbconn, "totalColton", str(total_colton))
		except Exception as e:
				await utils.report(bot, str(e), source="!colton command")


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
								"colton": "Check the `!colton` data",
								"dump": "A debug command for the bot to dump a variable into chat",
								"flag": "Tests the `flag` function",
								"load": "Loads an extension",
								"playing": "Sets the presence of the bot (what the bot says it's currently playing)",
								"reload": "Reloads an extension",
								"report": "Tests the `report` function",
								"serverid": "Posts the ID of the current channel",
								"swears": "Find out who swears the most",
								"test": "A catch-all command for inserting code into the bot to test",
						}
						await bot.say("`!dev` User Guide", embed=embedfromdict(helpdict, title=title, description=description))

				elif func == "channelid":
						await bot.say("Channel ID: " + ctx.message.channel.id)

				elif func == "colton":
						await bot.say("Colton has mentioned being forever alone {} times.\n"
													"The last time he mentioned being forever alone was **{}**"
													.format(total_colton, last_colton.strftime("%c")))

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

				elif func == "swears":
						sortedlist = sorted(list(swear_tally.items()), key=lambda user_tally: user_tally[1][2], reverse=True)
						message = ""
						for i, user in enumerate(sortedlist):
								message += ("**" + str(i + 1) + ".** " + bot.users[user[0]] + " - " +
														str(round(user[1][2]*100, 2)) + "%\n")
						if len(message) > 0:
								await bot.say(utils.trimtolength(message, 2000))

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
						await bot.say("Sup.")

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
		add_user_command = "INSERT INTO Users VALUES (%s, %s)"
		add_user_data = (user_id, username)
		bot.dbconn.execute(add_user_command, add_user_data)
		bot.dbconn.commit()
		bot.users[user_id] = username


def add_user_swears(user_id):
		""" Adds a user to the swear table

		Parameters
		-------------
		user_id : str
				The 18 digit user id of the user
		"""
		bot.dbconn.ensure_sql_connection()
		add_command = "INSERT INTO Swears VALUES (%s, %s, %s)"
		add_data = (user_id, 0, 0)
		bot.dbconn.execute(add_command, add_data)
		bot.dbconn.commit()


def update_user_swears(user_id):
		""" Updates the swear count for the user

		Parameters
		-------------
		user_id : str
				The 18 digit user id of the user
		"""
		bot.dbconn.ensure_sql_connection()
		add_command = "UPDATE Swears SET Words=%s, Swears=%s WHERE ID=%s"
		add_data = (swear_tally[user_id][0], swear_tally[user_id][1], user_id)
		bot.dbconn.execute(add_command, add_data)
		bot.dbconn.commit()


# --------------------- LOADING DB ----------------------------------


def load():
		""" Load everything """
		loadusers()
		loadcache()
		loadswears()


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


def loadswears():
		""" Load swear count table from database """
		global swear_tally
		try:
				query = "SELECT * FROM Swears"
				cursor = bot.dbconn.execute(query)
				for (user_id, words, swears) in cursor:
						if float(words) > 0:
								swear_tally[user_id] = [words, swears, swears / float(words)]
						else:
								swear_tally[user_id] = [words, swears, 0]
		except Exception as e:
				bot.loading_failure["swears"] = e


def loadcache():
		""" Load Cache values from database """
		global currently_playing, daily_colton, total_colton, last_colton
		try:
				currently_playing = utils.loadfromcache(bot.dbconn, "currPlaying")
				daily_colton = int(utils.loadfromcache(bot.dbconn, "dailyColton"))
				total_colton = int(utils.loadfromcache(bot.dbconn, "totalColton"))
				timestamp = utils.loadfromcache(bot.dbconn, "lastColton")
				last_colton = datetime.utcfromtimestamp(int(timestamp))
		except Exception as e:
				bot.loading_failure["cache"] = e


# -----------------------   START UP   -----------------------------------

# load all Discord, MySQL, and API credentials
tokenFile = open(AUTH_FILE_PATH, "r", encoding="utf-8")
[bot.CLIENT_ID,
 bot.CLIENT_SECRET,
 bot.BOT_TOKEN,
 bot.MYSQL_USER,
 bot.MYSQL_PASSWORD,
 bot.WOLFRAMALPHA_APPID,
 bot.JDOODLE_ID,
 bot.JDOODLE_SECRET,
 bot.REDDIT_ID,
 bot.REDDIT_SECRET,
 bot.UNSPLASH_CLIENT_ID,
 bot.YOUTUBE_KEY] = tokenFile.read().splitlines()

# Create MySQL connection
bot.dbconn = DBConnection(bot.MYSQL_USER, bot.MYSQL_PASSWORD, "suitsBot")
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
											'cogs.rand',
											'cogs.tags',
											'cogs.voice',
											'cogs.webqueries',
											'cogs.yiff']

if __name__ == "__main__":
		for extension in startup_extensions:
				try:
						bot.load_extension(extension)
						print('Loaded extenion "' + extension + '"')
				except discord.ClientException as err:
						exc = '{}: {}'.format(type(err).__name__, err)
						print('Failed to load extension {}\n{}'.format(extension, exc))

print("------------")
print("Logging in...")

# Start the bot
bot.run(bot.BOT_TOKEN)
