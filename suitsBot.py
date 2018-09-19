#!/usr/bin/env python

# ----------- For core functionality
import discord
from discord.ext import commands
from discord import Embed
import asyncio
import traceback
# ----------- For commands
import aiohttp
from datetime import datetime
import mysql.connector
import random
import re
from urllib.parse import quote
# ----------- For subreddit parsing
import praw
# ----------- For self restarting
import sys
# ----------- For web interface
from flask import Flask

# ------------------------ BOT CONSTANTS ---------------------------------

description = """SuitsBot v3.4.6
Discord bot deployed to practice webAPI implementation and learn Discord bot scripting in Python. 
Supports a variety of different functions including 
- Call-and-response user tags
- Searching Wikipedia and AniList.co
- Creating and managing lists
- Playing audio clips in voice chat

More information at: https://github.com/DWCamp/SuitsBot/wiki
"""

currentlyPlaying = "with bytes"

CLIENT_ID = ""
CLIENT_SECRET = ""
BOT_TOKEN = ""
AUTH_FILE_PATH = "PythonScripts/suitsBotOAuth.txt"
AUHTORIZED_IDS = ['187086824588443648']
DEV_CHANNEL_ID = '341428321109671939'
ALERT_CHANNEL_ID = '458462631397818369'
ERROR_CHANNEL_ID = '455185027429433344'
DEV_SERVER_ID = '219267501362642944'
HERESY_CHANNEL_ID = '427619361222557698'

DEFAULT_EMBED_COLOR = 0x4E2368
ANIME_EMBED_COLOR = 0x1A9AFC
BEST_GIRL_EMBED_COLOR = 0x76BB01
CODE_EMBED_COLOR = 0x00EE36
ERROR_EMBED_COLOR = 0xAA0000
FLAG_EMBED_COLOR = 0xFCEF15
LIST_EMBED_COLOR = 0x00C8C8
MEOW_EMBED_COLOR = 0xFCBE41
NASA_EMBED_COLOR = 0xEE293D
PLIST_EMBED_COLOR = 0xD0D0D0
REDDIT_EMBED_COLOR = 0xFF5700
WIKI_EMBED_COLOR = 0xFFFFFF
WOOF_EMBED_COLOR = 0x9E7132
YIFF_EMBED_COLOR = 0xD4EFFF

DEV_SERVER = None
DEV_CHANNEL = None
ALERT_CHANNEL = None
ERROR_CHANNEL = None

failedToLoadLists = None
failedToLoadTags = None
failedToLoadUsers = None
failedToLoadCache = None
failedToLoadSwears = None
failedToLoadPList = None

RESERVED_LIST_IDS = ["BestGirl"]

JDOODLE_ID = None
JDOODLE_SECRET = None

REDDIT_ID = None
REDDIT_SECRET = None
REDDIT_AGENT = "SuitsGamingBot"
NSFW_Thumbnail = "https://cdn2.iconfinder.com/data/icons/freecns-cumulus/32/519791-101_Warning-512.png"
REDDIT_DEFAULT_THUMBNAIL = "https://cdn.discordapp.com/attachments/341428321109671939/490654122941349888/unknown.png"

YOUTUBE_KEY = None

# ---------------------------- MY SQL ------------------------------------

cnx = None
cursor = None
GLOBAL_TAG_OWNER = "----GLOBAL TAG----"
MYSQL_USER = None
MYSQL_PASSWORD = None

# ---------------------------- WEB WORK ------------------------------------

mutedSubreddits = ["animemes", "the_donald", "pussypassdenied", "all"]
WOLFRAMALPHA_APPID = None
wolframClient = None
requestHeaders = {'User-Agent': 'suitsBot Discord Bot - https://github.com/DWCamp',
					'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Language':'en-us'
					}
MALAUTH = None
nextYiffURL = None
nextMeowURL = None

titleSynonyms = {}
characterSynonyms = {}

meowSuccess = 0
meowAttempt = 0

reddit = None

# ---------------------------- SERVER ------------------------------------

flask_app = Flask(__name__)

@flask_app.route("/")
def hello():
	return "Hello World!"

# ------------------------ GEN VARIABLES ---------------------------------

greetings = ["Hello!", "Greetings, friend!", "How's it going?", "What's up?", "Yo.", "Hey."]
AFFIRMATIVE_RESPONSES = ['yes', 'yup', 'y', 'okay', 'ok', 'go ahead', 'affirmative', 'the affirmative',
						 'in the affirmative', 'roger', 'ja', 'si' 'go']
users = {}
plist = {}
swearRegex = None
swearTally = {}
subredditRegex = None
tags = {"global": {}, "server": {}, "user": {}}
listSpaces = {}
listUserTable = {}
QUOTE_FOLDER = "/home/dwcamp/PythonScripts/Sounds/"

lastColton = None
dailyColton = None
totalColton = None

# ------------------------	HELP TEXT	---------------------------------

longHelp = {
	"anime" : ("Things I guess"),
	"aes": ("A command for spiting out vaporwave text. Just type the command and then a string of characters " +
			"and it will print them out in the A E S T H E T I C way. Because this command involves printing one " +
			"string across multiple lines, it won't accept any input longer than 20 characters (including the " +
			"command). This also means that custom emotes and user mentions are offlimits, since the string " +
			"representation of those features is much longer than Discord will have you believe."),
	"bestGirl": ("A command for each user to manage their own best girl list. Type `!bestGirl help` for a list of " +
			"the commands you can use. An example is `!bestGirl add [<index>] <girl>`, which when used would " +
			"look like `!bestGirl add [1] Ryuko Matoi`"),
	"code": ("Executes code typed in code formatted blocks (code enclosed in triple backticks ```like this```). Supports " + 
			"67 different languages. Type `!code -help` for more information"),
	"colton": ("Records every time that Colton claims that he will be forever alone. Reports back the number of times that " +
			"day as well as the number of times overall"),
	"hello": ("A simple greeting! Say hi to the bot and she will say hi back!"),
	"join": ("Make the bot join a user in voice"),
	"jpeg": ("Send it a photo or image url and it will return a nuked version"),
	"leave": ("Makes the bot leave voice chat"),
	"ls": ("A command for each user to create arbitrary lists of different things. Functions like MySQL, where the " +
		   "user possesses multiple tables of data which the user can edit by going into and performing edit " +
		   "commands similar to those found in the `!bestGirl` command. Type `!list help` for a full list " +
		   "of the commands you can use and how they work."),
	"meow": ("Cat."),
	"nasa": ("Provides an HD image of an astronomical nature. This image is provided by NASA's Astronomy Picture Of " +
			 "the Day API and changes every midnight EST. As it is provided by a third party API, this bot " +
			 "assumes no liability for the contents of the image or accompanying text. But it's NASA, so you're " +
			 "probably fine."),
	"preferences": ("Get out of here"),
	"rand": ("Uses a random number generator to answer questions of dice rolls, coinflips, or what to do for dinner. " +
			 "An example is `!rand item A, B, C...`, where it will return a randomly selected member of a comma " +
			 "seperated list. Type `!random help` for the complete user guide."),
	"say": ("Says one of the prerecorded voice clips in chat. For a list of the available clips, type `!say -ls`. The " +
			"bot must be a member of your current voice channel for this command to work. To bring the bot to " +
			"your voice channel, use the command `!join`"),
	"tag": ("Simple call and response. After you save a tag with the command `!tag [<key>] <value>`, you can then use " +
			"the command `!tag <key>` to make the bot respond with `<value>`. Useful for common links, large meme " +
			"texts, or images. Since each key can only have one value, users also have a personal group of " +
			"key-value pairs that can be set or accessed with the command `!tag -u`. For the complete user guide, " +
			"type `!tag -help`"),
	"wiki": ("Queries Wikipedia for information about the requested subject. Returns a simple description as well as a " +
			"longer form excerpt from the article."),
	"wolf": ("Use this command to ask the bot simple WolframAlpha questions. Type `!wolf` and followed by your question " +
			"and the bot will return the WolframAlpha response"),
	"woof": ("Woof."),
	"youtube": ("Searches YouTube for the video title provided and provides a link to the first search result"),
}

briefHelp = {
	"anime" : "Provides information about anime",
	"aes": "A command for making text 'A E S T H E T I C'",
	"code" : "Arbitrary code execution",
	"colton" : "Colton said he was forever alone again",
	"bestGirl": "Best girl list manager",
	"hello": "Says hi to you",
	"join": "Join a user in voice",
	"jpeg": "For when images need more jpeg",
	"leave": "leave voice",
	"ls": "Arbitrary list creation",
	"meow": "Cat.",
	"nasa": "A stunning astonomy picture",
	"preferences": "Modify some of the bot's settings",
	"rand": "Generate a random result",
	"say": "Have the bot say dumb things in voice",
	"tag": "Have the bot repeat a message when given a key phrase",
	"wiki": "Ask Wikipedia about a subject",
	"wolf": "Ask WolframAlpha a question",
	"woof": "Woof.",
	"youtube": "Searches YouTube",
}

aliases = {
	"anime" : ["ani", "Anime", "animu", "aniem", "anilist", "AniList"],
	"aes": ["AES"],
	"bestGirl": ["bestGirls", "bestgirl", "bestgirls", "bestGrils", "bestgril", "bestgrils", "bestGril", "bg", "BG"],
	"code" : ["Code", "program", "exe", "swift", "python", "java", "cpp", "brainfuck", "golang", "ide", "IDE", 
		"cobol", "pascal", "fortran", "vbn", "scala", "bash", "php", "perl", "cpp14", "c", "csharp", "lua", 
		"rust"],
	"colton": ["Colton", "foreverAlone", "damnitcolton", "damnItColton", "DamnItColton"],
	"hello": ["hi", "hey"],
	"join": ["jion", "joni"],
	"jpeg": ["JPEG", "jpg", "JPG", "jegp", "jgp", "needsMoreJpeg", "needsMoreJpg", "needsmorejpeg", "needsmorejpg"],
	"leave": ["shut up", "fuckOff", "gtfo", "GTFO"],
	"ls": ["list", "lsit", "l", "lists"],
	"meow": ["cat", "moew", "mewo", "nyaa", "nyan"],
	"nasa": ["NASA", "APOTD", "APOD", "apod", "apotd"],
	"preferences": ["set", "setting", "settings", "settigns", "settign", "prefs", "preference", "plist", "pref", "p"],
	"rand": ["random", "ran", "randmo"],
	"say": ["voice", "speak"],
	"tag": ["tags", "Tag", "Tags"],
	"wiki" : ["wikipedia", "Wikipedia", "Wiki", "WIKI"],
	"wolf": ["wolfram", "wA", "Wolfram", "WolframAlpha", "wolframAlpha", "woflram", "wofl"],
	"woof": ["dog", "doggo", "wof", "woofer", "wouef"],
	"youtube": ["yt", "YT", "YouTube", "youTube", "Youtube", "ytube", "yuotube", "youube", "youbue"],
}

# ----------------------- COMMAND DETAILS ----------------------------------

commandThumbnails = {
	"anime" : "https://anilist.co/img/icons/logo_full.png",
	"code" : "https://cdn.discordapp.com/attachments/341428321109671939/460671554653650964/codeIcon.png",
	"bestGirl" : "https://media1.tenor.com/images/19461e616447d8b63251f41f7abc461a/tenor.gif?itemid=6112845",
	"ls" : ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/WikiProject_Council_project_list_icon.svg"
					+ "/2000px-WikiProject_Council_project_list_icon.svg.png"),
	"preferences" : "http://icons.iconarchive.com/icons/tristan-edwards/sevenesque/1024/Preferences-icon.png",
	"rand" : "https://aruzegaming.com/wp-content/uploads/2016/04/Red-Dice-Wild_CHARACTER.png",
	"tag" : "https://cdn2.iconfinder.com/data/icons/marketing-strategy/512/Loud_Speaker-512.png",
	"say" : "https://cdn.discordapp.com/attachments/341428321109671939/487265313071824926/sayIcon.png",
	"wiki" : "https://www.wikipedia.org/portal/wikipedia.org/assets/img/Wikipedia-logo-v2@2x.png",
}

# ------------------------ HELPER CLASSES ----------------------------------

"""
Data type for storing the information about an anime show return from AniList.co queries
"""
class Anime:
	"""Adds a zero to the front of a number if it's less than 10"""
	def formatDate(date):
		if date is None:
			return "--"
		elif date < 10:
			return "0" + str(date)
		return str(date)

	"""Converts a string to title case"""
	def titleCase(content):
		if content is None:
			return None
		splitContent = content.split("_")
		combinedContent = ""
		for word in splitContent:
			combinedContent += word[:1].upper() + word[1:].lower() + " "
		return combinedContent.strip()

	"""
	Constructor for the Anime data object

	Media - The JSON dictionary returned by the AniList.co query
	"""
	def __init__(self, Media):
		self.characters = list()
		for character in Media['characters']['nodes']:
			if character['name']['first'] is None:
				self.characters.append(character['name']['native'])
			elif character['name']['last'] is None:
				self.characters.append(character['name']['first'])
			else:
				self.characters.append(character['name']['first'] + " " + character['name']['last'])
		if Media['description'] is None:
			self.description = "*(This media has no description)*"
		else:
			self.description = Media['description'].replace("<br>", "")
		self.duration = Media['duration']
		self.endDate = (str(Media['endDate']['year']) + "/" 
			+ Anime.formatDate(Media['endDate']['month']) + "/" 
			+ Anime.formatDate(Media['endDate']['day']))
		self.episodes = Media['episodes']
		if len(Media['genres']) > 0:
			self.genres = ", ".join(Media['genres'])
		else:
			self.genres = None
		self.image = Media['coverImage']['medium']
		self.score = Media['averageScore']
		self.source = Anime.titleCase(Media['source'])
		self.startDate = (Anime.formatDate(Media['startDate']['year']) + "/" 
			+ Anime.formatDate(Media['startDate']['month']) + "/" 
			+ Anime.formatDate(Media['startDate']['day']))
		self.status = Anime.titleCase(Media['status'])
		self.studios = list()
		for studio in Media['studios']['nodes']:
			self.studios.append(studio['name'])
		self.tags = list()
		for tag in Media['tags']:
			if not tag['isGeneralSpoiler']:
				self.tags.append(tag['name'])

		if Media['title']['english'] is None:
			if Media['title']['romaji'] is None:
				self.title = "<None>"
			else:
				self.title = Media['title']['romaji']
		else:
			self.title = Media['title']['english']

		#Parse enum value to normal looking string
		if Media['format'] == "TV_SHORT":
			self.format = "TV Short"
		elif Media['format'] == "MOVIE":
			self.format = "Movie"
		elif Media['format'] == "SPECIAL":
			self.format = "Special"
		elif Media['format'] == "MUSIC":
			self.format = "Music video"
		else:
			self.format = Media['format']

	"""Creates an embed object from a summary of the object's data and returns it"""
	def embed(self):
		animeEmbed = Embed()
		if self.image is not None:
			animeEmbed.set_thumbnail(url=self.image)
		animeEmbed.title = self.title
		animeEmbed.description = trimToLength(self.description, 2047)
		if self.genres is not None:
			animeEmbed.add_field(name="Genre", value=self.genres)
		if self.score is None:
			animeEmbed.add_field(name="Score", value="--/100")
		else:
			animeEmbed.add_field(name="Score", value=str(self.score) + "/100")
		animeEmbed.set_footer(text="Data retrieved using the https://anilist.co API",
								icon_url="https://anilist.co/img/icons/logo_full.png")
		animeEmbed.color = ANIME_EMBED_COLOR
		return animeEmbed

	"""Creates an embed from the entire set of the object's data and returns it"""
	def infoEmbed(self):
		animeEmbed = Embed().set_thumbnail(url=self.image)
		animeEmbed.title = self.title
		if self.format is not None:
			animeEmbed.add_field(name="Format", value=self.format)
		if self.source is not None:
			animeEmbed.add_field(name="Source", value=self.source)
		if self.format == "TV" and self.episodes is not None:
			animeEmbed.add_field(name="Episodes", value=self.episodes)
		if self.duration is not None:
			animeEmbed.add_field(name="Duration", value=str(self.duration) + " minutes")

		if self.format == "TV":
			if self.startDate is not None:
				animeEmbed.add_field(name="Start Date", value=self.startDate)
			if self.status == "Releasing":
				animeEmbed.add_field(name="Status", value="Currently Airing")
			elif self.status == "Finished":
				animeEmbed.add_field(name="End Date", value=self.endDate)
		else:
			if self.startDate is not None:
				animeEmbed.add_field(name="Release Date", value=self.startDate)

		if len(self.studios) == 1:
			animeEmbed.add_field(name="Studio", value=self.studios[0])
		elif len(self.studios) > 1:
			animeEmbed.add_field(name="Studios", value=", ".join(self.studios))

		animeEmbed.add_field(name="Score", value=str(self.score) + "/100")

		if len(self.characters) > 0:
			animeEmbed.add_field(name="Main Characters", value=", ".join(self.characters), inline=False)

		if len(self.tags) > 0:
			animeEmbed.add_field(name="Tags", value=", ".join(self.tags), inline=False)

		animeEmbed.set_footer(text="Data retrieved using the https://anilist.co API",
							  icon_url="https://anilist.co/img/icons/logo_full.png")
		animeEmbed.color = ANIME_EMBED_COLOR
		return animeEmbed

"""
Data type for storing the information about an anime character return from AniList.co queries
"""
class Character:
	"""
	Constructor

	Character - The JSON dictionary returned by the AniList.co query
	"""
	def __init__(self, Character):
		if Character['name']['first'] is None:
			self.name = Character['name']['native']
		elif Character['name']['last'] is None:
			self.name = Character['name']['first']
		else:
			self.name = Character['name']['first'] + " " + Character['name']['last']
		self.image = Character['image']['large']
		self.native = Character['name']['native']
		self.alternative = Character['name']['alternative']
		self.description = trimToLength(Character['description'].replace("~!", "").replace("!~", ""), 2047)
		self.media = list()
		for media in Character['media']['nodes']:
			if media['title']['english'] is None:
				self.media.append(media['title']['romaji'])
			else:
				self.media.append(media['title']['romaji'])

	"""Returns an embed containing the character's data"""
	def embed(self):
		characterEmbed = Embed().set_thumbnail(url=self.image)
		characterEmbed.title = self.name
		characterEmbed.description = self.description
		if self.native is not None:
			characterEmbed.add_field(name="Name in native language", value=self.native)
		if len(self.alternative) > 0 and self.alternative[0] != "":
			characterEmbed.add_field(name="Alternative Names", value=", ".join(self.alternative))
		if len(self.media) > 0:
			characterEmbed.add_field(name="Appeared in", value=trimToLength(", ".join(self.media), 2000))
		characterEmbed.set_footer(text="Data retrieved using the https://anilist.co API",
								icon_url="https://anilist.co/img/icons/logo_full.png")
		characterEmbed.color = ANIME_EMBED_COLOR
		return characterEmbed

	"""Returns an embed containing the character's data. This method was included to make the class interchangable with Anime"""
	def infoEmbed(self):
		return self.embed()

"""
Data type for storing the elements and attributes of a user's list
"""
class UserList():
	def __init__(self, listID=None, userName=None, title=None, elements=None, thumbnail_url=None, color=0):
		if elements is None:
			elements = []
		if title is None:
			title = ""
		if thumbnail_url is None:
			thumbnail_url = ""
		self.id = listID
		self.userName = userName
		self.contents = elements
		self.title = title
		self.thumbnail_url = thumbnail_url
		self.updating = None
		self.color = color
		self.bufferList = []

	# -------------- INSTANCE METHODS

	def add(self, entry, rank=None):
		if rank is None:
			rank = len(self.contents) + 1
		if rank > len(self.contents) + 1:
			raise ValueError('Rank cannot exceed the length of the list plus 1. Rank was ' + str(rank)
							 + ", list length is " + len(self.contents))
		if rank < 1:
			raise ValueError('Rank cannot be less than 0')
		self.contents.insert(rank - 1, entry)

	# During start up, stores the elements as it gets them in their appropriate index
	# using `None` as spacers until all elements are assembled
	def buffer(self, element, index):
		if len(self.bufferList) <= index:
			self.bufferList.extend([None] * (index - len(self.bufferList) + 1))
		if self.bufferList[index] is not None:
			raise ValueError("List: " + self.id + "\nThere was already an element at index " 
				+ str(index) + "\n" + str(self.bufferList))
		del self.bufferList[index]
		self.bufferList.insert(index, element)

	def clear(self):
		self.contents = []

	def commit(self):
		for (index, element) in enumerate(self.bufferList):
			if element is None:
				raise ValueError("None value in buffer found at index " + str(index) + " for list id " + self.id)
		self.contents = self.bufferList

	def count(self):
		return len(self.contents)

	def empty(self):
		return len(self.contents) == 0

	def getEmbed(self):
		listEmbed = Embed()
		if self.title == "":
			if self.id == "BestGirl":
				listEmbed.title = self.userName + "'s Best Girl List"
			else:
				listEmbed.title = self.id
		else:
			listEmbed.title = self.title
		print
		listEmbed.description = trimToLength(self.print(), 5000)
		listEmbed.set_thumbnail(url=self.thumbnail_url)
		listEmbed.color = self.color
		return listEmbed

	async def update(self):
		if self.updating is not None:
			self.updating = await bot.edit_message(self.updating, embed=self.getEmbed())

	def move(self, rankCurrent, rankTarget):
		if rankCurrent < 1 or rankTarget < 1:
			raise ValueError('Rank cannot be less than 1.')
		if rankCurrent > len(self.contents) or rankTarget > len(self.contents):
			raise ValueError('Rank cannot be greater than the length of the list')
		element = self.contents[rankCurrent - 1]
		del self.contents[rankCurrent - 1]
		self.contents.insert(rankTarget - 1, element)
		return element

	def print(self):
		if len(self.contents) == 0:
			return "(This list is empty)"
		statement = ""
		for index, element in enumerate(self.contents):
			statement += "**" + str(index + 1) + ".** " + element + "\n"
		return statement

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
		oldValue = self.contents[rank - 1]
		self.contents[rank - 1] = element
		return oldValue

	async def set_thumbnail(self, url):
		if url is not "":
			status_code = await checkURL(url)
			if status_code == 200:
				self.thumbnail_url = url
			else:
				raise ValueError("Invalid URL")
		else:
			self.thumbnail_url = ""
		return True

	def swap(self, rankA, rankB):
		if rankA < 1 or rankB < 1:
			raise ValueError('Index cannot be less than 1.')
		if rankA > len(self.contents) or rankB > len(self.contents):
			raise ValueError('Index cannot be greater than the length of the list')
		element = self.contents[rankA - 1]
		self.contents[rankA - 1] = self.contents[rankB - 1]
		self.contents[rankB - 1] = element
		return [self.contents[rankA - 1], element]

	# -------------- GLOBAL METHODS
	# Takes a string containing two numbers, optionally inside of brackets, and returns an array of the numbers parsed to integers
	def parseTwoNumbers(string):
		# Pull out the two numbers
		numbers = string.split(" ")
		if len(numbers) < 2:
			raise ValueError("There were less than two numbers")
		numbers = numbers[:2]
		# Remove brackets, if the function was called with brackets
		if numbers[0][0] == "[":
			closeBracketLoc = numbers[0].find("]")
			if closeBracketLoc == -1:
				raise ValueError("You never closed the brackets on the first number")
			numbers[0] = numbers[0][1:closeBracketLoc]
		if numbers[1][0] == "[":
			closeBracketLoc = numbers[1].find("]")
			if closeBracketLoc == -1:
				raise ValueError("You never closed the brackets on the second number")
			numbers[1] = numbers[1][1:closeBracketLoc]
		try:
			numbers[0] = int(numbers[0])
		except:
			raise ValueError("'" + numbers[0] + "' is not a number")
		try:
			numbers[1] = int(numbers[1])
		except:
			raise ValueError("'" + numbers[1] + "' is not a number")
		return numbers

	# Takes a string containing a string in brackets followed by a string not in brackets and returns an array of those elements
	def parseTwoStrings(string):
		if string[0] != "[":
			raise ValueError("I'm not seeing your target index. Use the help command for more information")
		closeBracketLoc = string.find("]")
		if closeBracketLoc == -1:
			raise ValueError("You never closed that bracket")
		firstElement = string[1:closeBracketLoc]
		secondElement = string[closeBracketLoc + 1:].strip()
		return [firstElement, secondElement]

	# Takes a string containing a string and possibly a number before it in brackets and returns them e.g. '[1] test' or 'test again'
	def parseStringAndOptionalNum(string):
		if string[0] == "[":
			closeBracketLoc = string.find("]")
			if closeBracketLoc == -1:
				raise ValueError("You never closed your brackets")
			try:
				index = int(string[1:closeBracketLoc])
			except:
				raise ValueError("Could not parse the number '" + string[1:closeBracketLoc] + "'")
			element = string[closeBracketLoc + 1:].strip()
			return [element, index]
		else:
			return [string, None]

	# Takes a string containing a number that may or may not be in brackets and returns it as an integer
	def parseNumber(string):
		if string[0] == "[":
			closeBracketLoc = string.find("]")
			if closeBracketLoc == -1:
				raise ValueError("You never closed that bracket")
			try:
				index = int(string[1:closeBracketLoc])
				return index
			except:
				raise ValueError("Could not parse the number '" + string[1:closeBracketLoc] + "'")
		else:
			try:
				index = int(string)
				return index
			except:
				raise ValueError("Could not parse the number '" + string + "'")



# ------------------------  HELPER METHODS  ---------------------------------

"""Returns a random element from a list"""
def returnRandomElement(array):
	return array[random.randint(0, len(array) - 1)]

"""Returns the name of the author sending a message, defaulting to the nickname if it exists"""
def getAuthorName(message):
	if message.channel.is_private or message.author.nick is None:
		return message.author.name
	return message.author.nick

"""Returns the name of a member, defaulting to the nickname if it exists"""
def getMemberName(member):
	if member.nick is None:
		return member.name
	return member.nick

"""Returns a human readable printout of the current time"""
def currTime():
	def formatTime(time):
		if time < 10:
			return "0" + str(time)
		return str(time)

	now = datetime.now()
	if now.hour % 12 > 0:
		return formatTime(now.hour % 12) + ":" + formatTime(now.minute) + ":" + formatTime(now.second) + " PM"
	else:
		return formatTime(now.hour) + ":" + formatTime(now.minute) + ":" + formatTime(now.second) + " AM"

"""
Creates an embeded object from a dictionary

dictionary - A [String:String] dictionary where the keys are the field names and the values are the field values
title - The title of the embed
description - The description of the embed
thumbnail_url - A string which holds a url to the image which will become the embed thumbnail
color - The embed color
"""
def dictToEmbed(dictionary, title=None, description=None, thumbnail_url=None, color=DEFAULT_EMBED_COLOR):
	embed = Embed()
	if title is not None:
		embed.title = title
	if thumbnail_url is not None:
		embed.set_thumbnail(url=thumbnail_url)
	if description is not None:
		embed.description = description
	if color is not None:
		embed.color = color

	for key in dictionary.keys():
		embed.add_field(name=key, value=dictionary[key], inline=False)
	return embed

"""Parses out the function and parameter from the content of a message"""
def functionParameter(string):
	message = stripCommand(string)
	spaceLoc = message.find(" ")

	# Seperates the function from the parameter
	if spaceLoc > 0:
		function = message[:spaceLoc].lower()
		parameter = message[spaceLoc + 1:].strip()
	else:
		function = message.lower()
		parameter = ""
	return [function, parameter]

"""Returns a string forward loaded with spaces to make it a provided length"""
def padToLength(string, length):
	return string + (" " * (length - len(string)))

"""
Send an urgent message to the dev along with a strack trace

alert - The thing being reported
source - The method which triggered the action (optional)
ctx - The context object of the message which triggered the flag (optional)
"""
async def report(alert, source=None, ctx=None):
	errorEmbed = Embed()
	if ctx is None:
		errorEmbed.title = "Alert"
		errorEmbed.color = ERROR_EMBED_COLOR
		errorEmbed.add_field(name="Alert", value=alert, inline=False)
		await bot.send_message(ERROR_CHANNEL, embed=errorEmbed)
		return
	errorEmbed.title = "ERROR REPORT"
	errorEmbed.color = ERROR_EMBED_COLOR
	errorEmbed.add_field(name="Alert", value=alert, inline=False)
	errorEmbed.add_field(name="Author", value=ctx.message.author.name, inline=False)
	errorEmbed.add_field(name="Time", value=currTime(), inline=False)
	if ctx.message.channel.is_private:
		errorEmbed.add_field(name="Channel", value="Private", inline=False)
	else:
		errorEmbed.add_field(name="Channel", value=ctx.message.server.name + " / " + ctx.message.channel.name,
							 inline=False)
	if source is not None:
		errorEmbed.add_field(name="Source", value=source, inline=False)
	errorEmbed.add_field(name="Message", value=ctx.message.content, inline=False)
	stackTrace = reversed(traceback.format_stack()[:-1])
	stackTrace = "```" + trimToLength("".join(stackTrace), 2042) + "```"
	errorEmbed.description = stackTrace
	await bot.send_message(ERROR_CHANNEL, embed=errorEmbed)

"""
Send a non-urgent message to the dev

alert - The thing being flagged
description - A description of what went wrong as well as any stack trace or additional text (optional)
ctx - The context object of the message which triggered the flag (optional)
message - The message object which triggered the flag, used in case a context object is not available (optional)
"""
async def flag(alert, description="(No description provided)", ctx=None, message=None):
	try:
		if message is None:
			if ctx is None:
				await bot.send_message(ALERT_CHANNEL, "Alert:\n" + alert + "\n---\n" + description)
				return
			message = ctx.message

		flagEmbed = Embed()
		flagEmbed.title = alert
		flagEmbed.color = FLAG_EMBED_COLOR
		flagEmbed.add_field(name="Author", value=message.author.name, inline=False)
		flagEmbed.add_field(name="Time", value=currTime(), inline=False)
		if message.channel.is_private:
			flagEmbed.add_field(name="Channel", value="Private", inline=False)
		else:
			flagEmbed.add_field(name="Channel", value=message.server.name + " / " + message.channel.name,
								 inline=False)
		flagEmbed.add_field(name="Message", value=message.content, inline=False)
		if description is not None:
			flagEmbed.description = trimToLength(description, 2048)
		await bot.send_message(ALERT_CHANNEL, embed=flagEmbed)
	except Exception as e:
		await report(str(e) + "\n\nAlert:\n" + alert, source="Error when producing flag", ctx=ctx)

"""Removes the command invocation from the front of a message"""
def stripCommand(content):
	spaceLoc = content.find(" ")
	breakLoc = content.find("\n")
	if breakLoc >= 0 and spaceLoc >= 0:
		endTag = min(breakLoc, spaceLoc)
	else:
		endTag = max(breakLoc, spaceLoc)

	if endTag == -1:
		message = ""
	else:
		message = content[endTag:].strip()
	return message

"""Limits the length of a string to a maximum value"""
def trimToLength(content, length):
	content = str(content)
	if length < 2:
		return "…"
	if len(content) > length:
		return content[:length - 1] + "…"
	return content

# ------------- Parse User Input

# Takes a time in "00:00" or "0:00" format and returns it as a time and minutes integer
# Returns [None, None] if the time is not parsable
def parseTime(time):
	colonLoc = time.find(":")
	if colonLoc != -1 and len(time) == colonLoc + 3:
		try:
			hours = int(time[0:colonLoc])
			minutes = int(time[colonLoc + 1:])
			return hours, minutes
		except:
			return None, None
	return None, None


# Parses out the different kinds of apostrophes so that the user doesn't have to consider them
# Also parses quotation marks
# Returns a string which is just the parameter but all types of apostrophes are parsed to be the vertical apostrophe -> '
def parseApos(string):
	string = string.replace("’", "'")
	string = string.replace("‘", "'")
	string = string.replace("”", '"')
	string = string.replace("“", '"')
	string = string.replace("„", '"')
	return string

# Returns an array of [x, (y + attachment URLs)] when given the string "[x] y" and an array of attachments
def parseKeyValue(message, attachments=[]):
	end = message.find("]")
	if end == 1:  # no tag key
		return [None, "EMPTY KEY"]
	if end == -1:  # unclosed tag key
		return [None, "UNCLOSED KEY"]
	tagKey = message[1:end]
	if len(message) < (end + 3):
		if len(attachments) == 0:
			return [None, "NO VALUE"]
		tagValue = ""
		for attachment in attachments:
			tagValue += "\n" + attachment['url']
		return [tagKey.lower(), tagValue]
	endOffset = 2
	if message[end + 1] != " ":  # Starts the tagValue immediately after the closing bracket if there isn't a space
		endOffset = 1
	tagValue = message[(end + endOffset):]  # Sets the value of the tag
	if tagKey.isspace():
		return [None, "WHITESPACE KEY"]
	elif tagKey[0] == "-":
		return [None, "KEY STARTS WITH -"]
	for attachment in attachments:
		tagValue += "\n" + attachment['url']
	return [tagKey, tagValue]


# ------------- MySQL

"""Closes the connection to the MySQL database"""
def closeConnector():
	# Close MySQL connection
	cursor.close()
	cnx.close()

"""Ensures the database connection is still active and, if not, reconnects"""
def ensureSQLConnection():
	global cnx, cursor
	if not cnx.is_connected():
		cnx = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, database='suitsBot')
		cursor = cnx.cursor(buffered=True)


# ------------- Web

"""
Requests JSON data using a GET request and returns the data as a JSON dictionary and HTTP response. 
If the request fails, the JSON dictionary is None.

url - the url to request from
headers - values to insert into the request headers
params - parameters passed in the request
contentType - content type of the returned json
"""
async def get_JSON_with_GET(url, headers=requestHeaders, params={}, contentType=None):
	async with aiohttp.ClientSession(headers=headers) as session:
		async with session.get(url, params=params) as resp:
			if resp.status is 200:
				json = await resp.json(content_type=contentType)
				return [json, resp.status]	
			return [None, resp.status]

"""
Requests JSON data using a POST request and returns the data as a JSON dictionary and HTTP response. 
If the request fails, the JSON dictionary is None.

url - the url to request from
headers - values to insert into the request headers
params - parameters passed in the request
json - JSON dictionary posted to the url
"""
async def get_JSON_with_POST(url, headers=requestHeaders, params={}, json={}):
	async with aiohttp.ClientSession(headers=headers) as session:
		async with session.post(url, params=params, json=json) as resp:
			json = await resp.json()
			return [json, resp.status]

"""
Returns the HTML body at a url, as well as the HTTP response

url - the url to request from
headers - values to insert into the request headers
params - parameters passed in the request
"""
async def getHTML(url, headers=requestHeaders, params={}):
	async with aiohttp.ClientSession(headers=headers) as session:
		async with session.get(url, params=params) as resp:
			text = await resp.text()
			return [text, resp.status]

"""
Returns the XML body at a url, as well as the HTTP response

url - the url to request from
headers - values to insert into the request headers
params - parameters passed in the request
"""
async def getXML(url, headers=requestHeaders, params={}):
	async with aiohttp.ClientSession(headers=headers) as session:
		async with session.get(url, params=params) as resp:
			text = await resp.text()
			return [text, resp.status]

"""
Validates that a URL provided points to a reachable URL

url - the url to request from
headers - values to insert into the request headers
params - parameters passed in the request
"""
async def checkURL(url, headers=requestHeaders, params={}):
	async with aiohttp.ClientSession(headers=headers) as session:
		try:
			async with session.get(url, params=params) as resp:
				return resp.status
		except:
			return None
 
"""Gets the url of a random image from e621.net, caches the value, and returns it"""
async def getYiffImageURL():
	global nextYiffURL
	[rawHTML, status_code] = await getHTML("https://e621.net/post/random")
	imageStartLoc = rawHTML.find('data-sample_url') + 17
	while imageStartLoc < 1:
		[rawHTML, status_code] = await getHTML("https://e621.net/post/random")
		imageStartLoc = rawHTML.find('data-sample_url') + 17
	imageEndLoc = rawHTML[imageStartLoc:].find('"') + imageStartLoc
	url = rawHTML[imageStartLoc:imageEndLoc]
	cacheYiffURL(url)
	nextYiffURL = url

"""Gets the url of a random image from aws.random.cat and caches the value"""
async def getMeowImageURL():
	global nextMeowURL, meowAttempt, meowSuccess
	json = None
	counter = 0
	while json is None and counter < 100:
		[json, status_code] = await get_JSON_with_GET("http://aws.random.cat/meow")
		meowAttempt += 1
		counter += 1
	nextMeowURL = json['file']
	meowSuccess += 1
	cacheMeowSuccessRate()
	cacheMeowURL(nextMeowURL)

"""Takes the name of a subreddit and returns the PRAW Subreddit object if it exists, otherwise returns None"""
def getSubredditEmbed(subredditName):
	if subredditName in mutedSubreddits:
		return None
	try:
		subredditList = reddit.subreddits.search_by_name(subredditName, include_nsfw=False, exact=True)
		subreddit = subredditList.pop()
		subEmbed = Embed()
		subEmbed.color = REDDIT_EMBED_COLOR
		subEmbed.title = subreddit.display_name
		subEmbed.url = "https://www.reddit.com/r/" + subredditName

		if subreddit.over18:
			subEmbed.set_thumbnail(url=NSFW_Thumbnail)
			subEmbed.description = "This subreddit is listed as NSFW"
			return subEmbed

		if subreddit.header_img is not None:
			subEmbed.set_thumbnail(url=subreddit.header_img)
		elif subreddit.icon_img is not None:
			subEmbed.set_thumbnail(url=subreddit.icon_img)
		elif subreddit.banner_img is not None:
			subEmbed.set_thumbnail(url=subreddit.banner_img)
		else:
			subEmbed.set_thumbnail(url=REDDIT_DEFAULT_THUMBNAIL)
		subEmbed.description = trimToLength(subreddit.public_description, 2000)
		subEmbed.add_field(name="Subscribers", value=subreddit.subscribers)
		timeString = datetime.utcfromtimestamp(subreddit.created_utc).strftime('%Y-%m-%d')
		subEmbed.add_field(name="Subreddit since", value=timeString)
		return subEmbed
	except Exception as e:
		return None

"""Converts HTML tags to their corresponding Markdown symbols"""
def HTMLtoMarkdown(htmlText):
	htmlText = htmlText.replace("<b>", "**").replace("</b>", "**")
	htmlText = htmlText.replace("<i>", "*").replace("</i>", "*")
	htmlText = htmlText.replace("<li>", " - ").replace("</li>", "")
	htmlText = htmlText.replace("</p>", "\n").replace("<p>", "")
	htmlText = htmlText.replace("<br>", "\n").replace("<br />", "")
	stripHTMLTags(htmlText)
	return htmlText

"""Removes HTML tags which are not markdown related"""
def stripHTMLTags(htmlText):
	htmlText = htmlText.replace("<ul>", "").replace("</ul>", "")
	htmlText = htmlText.replace("<sup>", "").replace("</sup>", "")
	htmlText = htmlText.replace("<b>", "").replace("</b>", "")
	htmlText = htmlText.replace("<i>", "").replace("</i>", "")
	htmlText = htmlText.replace("<li>", "").replace("</li>", "")
	htmlText = htmlText.replace("</p>", "").replace("<p>", "")
	#Removes every tag named
	for tag in ["span"]:
		htmlText = htmlText.replace("</" + tag + ">", "")
		tagLoc = htmlText.find("<" + tag)
		i = 0
		while tagLoc > -1 and i < 50:
			i += 1
			endTagLoc = htmlText[tagLoc:].find(">") + tagLoc
			htmlText = htmlText[:tagLoc] + htmlText[endTagLoc + 1:]
			tagLoc = htmlText.find("<" + tag)

	#Remove the tag and its contents for every tag named
	for tag in ["small"]:
		tagLoc = htmlText.find("<" + tag)
		i = 0
		while tagLoc > -1 and i < 50:
			i += 1
			endTagLoc = htmlText[tagLoc:].find("/" + tag + ">") + tagLoc
			htmlText = htmlText[:tagLoc] + htmlText[endTagLoc + (2 + len(tag)):]
			tagLoc = htmlText.find("<" + tag)

	return htmlText

# ------------------------ START UP SCRIPT ---------------------------------

print("\n\n------------")
bot = commands.Bot(command_prefix='!', description=description)

if not discord.opus.is_loaded():
	# the 'opus' library here is opus.dll on windows
	# or libopus.so on linux in the current directory
	# you should replace this with the location the
	# opus library is located in and with the proper filename.
	# note that on windows this DLL is automatically provided for you
	discord.opus.load_opus('opus')

print("Logging in...")

@bot.event
async def on_ready():
	global DEV_SERVER, DEV_CHANNEL, ALERT_CHANNEL, ERROR_CHANNEL, nextYiffURL, reddit

	print('------------\nLogged in as')
	print(bot.user.name)
	print(bot.user.id)
	DEV_SERVER = bot.get_server(DEV_SERVER_ID)
	DEV_CHANNEL = bot.get_channel(DEV_CHANNEL_ID)
	ALERT_CHANNEL = bot.get_channel(ALERT_CHANNEL_ID)
	ERROR_CHANNEL = bot.get_channel(ERROR_CHANNEL_ID)
	bot.player = None

	# Post restart embed
	readyEmbed = Embed()
	readyEmbed.title = "Bot Restart"
	readyEmbed.add_field(name="Current Time", value=currTime())
	if len(sys.argv) == 1:
		readyEmbed.add_field(name="Previous Exit Code", value="Starting from cold boot")
		readyEmbed.add_field(name="Assumed cause of reboot", value="N/A")
	else:
		readyEmbed.add_field(name="Previous Exit Code", value=str(sys.argv[1]))
		if sys.argv[1] == "1" or sys.argv[1] == "120":
			readyEmbed.add_field(name="Assumed cause of reboot", value="Use of `!r`")
		else:
			readyEmbed.add_field(name="Assumed cause of reboot", value="Random bug")
	readyEmbed.add_field(name="Status", value="Loading Data...", inline=False)
	readyEmbed.color = DEFAULT_EMBED_COLOR
	readyMessage = await bot.send_message(DEV_CHANNEL, embed=readyEmbed)

	print('------------\nLoading Data...')

	# Load data from database
	load()
	if failedToLoadTags is not None:
		await report('FAILED TO LOAD TAGS\n' + str(failedToLoadTags))
	if failedToLoadUsers is not None:
		await report('FAILED TO LOAD USERS\n' + str(failedToLoadUsers))
	if failedToLoadLists is not None:
		await report('FAILED TO LOAD USER LISTS\n' + str(failedToLoadLists))
	if failedToLoadCache is not None:
		await report('FAILED TO LOAD CACHE\n' + str(failedToLoadCache))
	if failedToLoadSwears is not None:
		await report('FAILED TO LOAD SWEARS\n' + str(failedToLoadSwears))
	if failedToLoadPList is not None:
		await report('FAILED TO LOAD PLIST\n' + str(failedToLoadPList))

	# Update restart embed
	readyEmbed.remove_field(3)
	readyEmbed.add_field(name="Status", value="Loading web services...", inline=False)
	await bot.edit_message(readyMessage, embed=readyEmbed)

	print('------------\nFinalizing setup...')

	# Load/initialize web content
	try:
		await bot.change_presence(game=discord.Game(name=currentlyPlaying))
	except:
		pass
	reddit = praw.Reddit(client_id=REDDIT_ID, client_secret=REDDIT_SECRET, user_agent=REDDIT_AGENT)

	print('------------\nOnline!\n------------')

	readyEmbed.remove_field(3)
	readyEmbed.add_field(name="Status", value="Online!", inline=False)
	await bot.edit_message(readyMessage, embed=readyEmbed)

@bot.event
async def on_message(message):
	global swearTally, subredditRegex, swearRegex

	# ---------------------------- HELPER METHODS
	try:
		def isSwear(word):
			global swearRegex
			word =  word.lower()
			if swearRegex is None:
				swearRegex = re.compile('.*(fu+c(c|k)|sh+i+t)')
			if swearRegex.match(word) is not None:
				return True

			punctuation = "!@#$%^&*()\{\}\\;:,.<>/?`~|-=_+\"'"
			for letter in punctuation:
				word = word.replace(letter, "")
			word = word.strip()

			#Any word that even contains these strings is probably a curse
			#'Fuck' and 'shit' are already parsed by the regex above
			fullSwears = ["asshole", "bitch", "cock", "cunt", "damn", 
					"dammit", "dick", "faggot", "piss", "pussy"]
			#These strings aren't curses unless they're isolated
			partialSwears = ["ass", "fag", "hell"] 

			for swear in fullSwears:
				if word.find(swear) >= 0:
					return True

			if word in partialSwears:
				return True
			return False

		# -------------------------------------------
		if message.author == bot.user:
			return

		if message.content == "!r":
			if message.author.id in AUHTORIZED_IDS:
				closeConnector()
				if bot.is_voice_connected(message.server):
					await bot.voice_client_in(message.server).disconnect()  # Disconnect from voice
				await bot.send_message(message.channel, "Restarting...")
				await bot.close()
				sys.exit(1)
			else:
				await bot.send_message(message.channel, "You do not have authority to restart the bot")
		if message.content == "!gn":
			if message.author.id in AUHTORIZED_IDS:
				closeConnector()
				if bot.is_voice_connected(message.server):
					await bot.voice_client_in(message.server).disconnect()  # Disconnect from voice
				await bot.send_message(message.channel, "Goodbye...")
				await bot.close()
				sys.exit(0)
			else:
				await bot.send_message(message.channel, "You do not have authority to terminate the bot")
			return

		authorID = message.author.id
		authorName = message.author.name
		if authorID not in users.keys() and failedToLoadUsers is None:
			await flag("Added new user on server", description=str(authorID) + ":" + message.author.name, message=message)
			addUser(authorID, authorName)

		if message.content in ["🖐", "✋", "🤚"]:
			await bot.send_message(message.channel, "\*clap\* :pray:" + " **HIGH FIVE!**")
			return

		if message.content == "👈":
			await bot.send_message(message.channel, ":point_right: my man!")

		if message.content == "👉":
			await bot.send_message(message.channel, ":point_left: my man!")

		if message.content[0:8].lower() == "good bot":
			await bot.send_message(message.channel, "Thank you :smile:")

		# -------------------------------------------- Parsing subreddits
		start = -1
		lowerContent = message.content.lower()

		if subredditRegex is None:
			subredditRegex = re.compile('\\/?r\\/\\w+')

		subs = re.findall(subredditRegex, lowerContent)

		if len(subs) > 0:
			subs = set(subs)
			for sub in subs:
				subName = sub[sub.find("r/") + 2:] #strip off "/r/"
				subEmbed = getSubredditEmbed(subName)
				if subEmbed is not None:
					await bot.send_message(message.channel, embed=subEmbed)

		# -------------------------------------------- Counting Swears
		try:
			if message.channel.id != DEV_CHANNEL_ID:
				words = message.content.split()
				swears = 0
				for word in words:
					if isSwear(word):
						swears += 1
				if message.author.id not in swearTally.keys():
					swearTally[message.author.id] = [0, 0, 0.0]
					addUserSwears(message.author.id)
				tallyArray = swearTally[message.author.id]
				tallyArray[0] += len(words)
				tallyArray[1] += swears
				tallyArray[2] = tallyArray[1] / float(tallyArray[0])
				updateUserSwears(message.author.id)
		except Exception as e:
			await report(str(e), source="swear detection", ctx=ctx)
			return

		# ------------------------------------------------------------

		await bot.process_commands(message)
	except Exception as e:
		await report(str(e), source="on_message")


# ----------------------------- EVENTS --------------------------------------

@bot.event
async def on_voice_state_update(before, after):
	try:
		if after.voice.voice_channel is None and bot.is_voice_connected(after.server):
			if len(bot.voice_client_in(after.server).channel.voice_members) == 1:
				await bot.voice_client_in(after.server).disconnect()
	except Exception as e:
		await report(str(e), source="aes command", ctx=ctx)
		return

# ------------------------ GENERAL COMMANDS ---------------------------------

@bot.command(pass_context=True, help=longHelp['aes'], brief=briefHelp['aes'], aliases=aliases['aes'])
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
			messageToSay = ""
			for char in message:
				messageToSay += "**" + char + "** "
			counter = 0
			for char in message:
				if char in ["_", "-"]:
					char = "|"
				elif char == "|":
					char = "—"

				if counter > 0:
					messageToSay += "\n**" + char + "**"
				counter += 1
			await bot.say(messageToSay)
	except Exception as e:
		await report(str(e), source="aes command", ctx=ctx)
		return

# Bot interfaces with AniList.co's API
@bot.command(pass_context=True, help=longHelp['anime'], brief=briefHelp['anime'], aliases=aliases['anime'])
async def anime(ctx):
	global titleSynonyms, characterSynonyms

	ANILIST_API_URL = 'https://graphql.anilist.co'

	animeQuery = '''
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
'''
	characterQuery = '''
query ($name: String) {
	Character (search: $name) {
		name {
		  first
		  last
		  native
		  alternative
		}
		image {
		  large
		}
		description
		media(sort: TITLE_ENGLISH, type: ANIME) {
		  nodes {
			title {
			  english
			  romaji
			}
		  }
		}
	}
}
'''

	def checkForExistingSynonym(newTerm, synonymDict):
		for term in synonymDict.keys():
			if newTerm in synonymDict[term]:
				return term
		return None
	
	try:
		# removes the "!anime" envocation portion of the message
		message = stripCommand(ctx.message.content)

		# Parsing commands
		commands = []
		i = 0;
		while i < len(message) and message[i] == "-":  # Looks for commands
			command = ""
			i += 1
			# iterates over charcters until it finds the end of the command
			while i < len(message) and message[i].isalnum():
				command = command + message[i]
				i += 1;
			commands.append(command.lower())
			i += 1
		searchTerm = message[i:].strip()  # Removes commands from the message

		if "dev" in commands:
			await bot.say(characterSynonyms)
			return

		# Explain all the commands to the user
		if "help" in commands or searchTerm == "help":
			title = "!anime - User Guide"
			description = ("A search tool for anime shows and characters. This command uses the AniList.co API to return " +
				"details on the search term provided for the show/character whose name is provide with the command (e.g. " +
				"`!anime Kill la Kill`). For shows, information like a show description, air date, rating, and genre information " +
				"will be returned. For characters, the bot provides a description, their nicknames, and the media they've " +
				"been in.\n\nThe bot uses a synonym engine to make it easier to find popular characters and allow for searching " + 
				"for entries using unofficial nicknames (e.g. `!anime klk` redirects to `!anime Kill la Kill`). The bot's " +
				"synonym table can be modified by users to allow for a more complete table of synonyms")
			commandDict = {"<search>": "Searches the database for an anime",
							"-help": "Displays this message",
							"-add [<Synonym>] <Search Value>": ("Adds a synonym to the list. Will search "
												+ "for `Search Value` when a user types `Synonym`. Can be used "
												+ "with the `-char` command to create character synonyms. "
												+ "`<Synonym>` also supports semicolon-delinated lists"),
							"-char <search>": "Searches the database for a character page",
							"-info <search>": "Shows the complete details for an anime. Has no effect on `-char` searches",
							"-ls" : ("Lists the anime synonym table. If used with the `-char` command, " 
												+ "it lists the character synonym table"),
							"-raw <search>" : "Disables synonym correction for search terms",
							"-remove <Search Value>": ("Removes a synonym from the list. Can be used with " 
												+ " the `-char` command to remove character synonyms")}
			await bot.say(embed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["anime"]))
			return

		if "ls" in commands:
			if "char" in commands:
				searchDict = characterSynonyms
				title = "Character name synonyms"
			else:
				searchDict = titleSynonyms
				title = "Anime title synonyms"
			message = ""
			for changeTo in sorted(list(searchDict.keys())):
				message += "**" + changeTo + "** <- " + ", ".join(searchDict[changeTo]) + "\n"
			embed = Embed()
			embed.title = title
			embed.description = trimToLength(message, 2040)
			embed.color = ANIME_EMBED_COLOR
			await bot.say(embed=embed)
			return

		if "add" in commands and "remove" in commands:
			await bot.say(("I don't know how you possibly expect me to both add and " + 
							"remove a synonym in the same command"))

		if "char" in commands:
			synonymDict = characterSynonyms
			charInsert = "-char "
			searchType = "character"
		else:
			synonymDict = titleSynonyms
			charInsert = ""
			searchType = "anime"

		# Add search synonym
		if "add" in commands:
			tagKeyValue = parseKeyValue(searchTerm)
			if tagKeyValue[0] is None:
				errorMessages = {
					"EMPTY KEY":"There was no synonym for the search value",
					"UNCLOSED KEY":"You didn't close your brackets",
					"NO VALUE":"There was no search value to save for the synonym",
					"WHITESPACE KEY":"Just because this bot is written in Python does not mean whitespace is an acceptable synonym",
					"KEY STARTS WITH -":"The `-` character denotes the start of a command and cannot be used in synonyms"}
				await bot.say(errorMessages[tagKeyValue[1]])
				return
			changeFrom = tagKeyValue[0].lower()
			changeTo = tagKeyValue[1]
			collision = checkForExistingSynonym(changeFrom, synonymDict)
			if collision is None:
				if changeTo not in synonymDict.keys():
					synonymDict[changeTo] = list()
				changeFromList = changeFrom.split(";")
				for element in changeFromList:
					synonymDict[changeTo].append(element.strip())
					addSynonym(searchType.upper(), changeTo, element)
				await bot.say("All " + searchType + " searches for `" + "` or `".join(changeFromList) + "` will now correct to `" + changeTo + "`")
			else:
				await bot.say(("The synonym `" + changeFrom + "` already corrects to `" + collision +"`. Pick a different word/phrase " +
								"or remove the existing synonym with the command `!anime -remove " + changeFrom + "`"))
			return

		# Remove search synonym
		if "remove" in commands:
			collision = checkForExistingSynonym(searchTerm, synonymDict)
			if collision is not None:
				synonymDict[collision].remove(searchTerm)
				if len(synonymDict[collision]) == 0:
					del synonymDict[collision]
				removeSynonym(searchType.upper(), collision, searchTerm)
				await bot.say("Alright, `" + searchTerm + "` will no longer correct to `" + collision + "` for " + searchType + " searches")
			else:
				await bot.say(("The synonym you searched for does not exist. Check your use (or lack thereof) of the `-char` "
									+ "command, or use the `-ls` command to make sure you're spelling everything right"))
			return

		if searchTerm == "":
			await bot.say("I don't see a search term to look up. Type `!anime -help` for a user guide")
			return

		if "char" in commands:
			if "raw" not in commands:
				for key in characterSynonyms.keys():
					if searchTerm.lower() in characterSynonyms[key]:
						searchTerm = key
			characterVariables = {'name': searchTerm}
			[json, status] = await get_JSON_with_POST(ANILIST_API_URL, json={'query': characterQuery, 'variables': characterVariables})
			if "json" in commands:
				await bot.say(trimToLength(json, 2000))
			if status == 200:
				dataObject = Character(json['data']['Character'])
		else:
			if "raw" not in commands:
				for key in titleSynonyms.keys():
					if searchTerm.lower() in titleSynonyms[key]:
						searchTerm = key
			animeVariables = {'title': searchTerm}
			[json, status] = await get_JSON_with_POST(ANILIST_API_URL, json={'query': animeQuery, 'variables': animeVariables})
			if "json" in commands:
				await bot.say(trimToLength(json, 2000))
			if status == 200:
				dataObject = Anime(json['data']['Media'])
		
		if status != 200:
			if status == 500:
				await flag("500 Server Error on search term " + searchTerm, description=str(json), ctx=ctx)
				await bot.say("`500 Server Error`. The AniList servers had a brief hiccup. Try again in a little bit")
			elif status == 404:
				await flag("Failed to find result for search term " + searchTerm, description=str(json), ctx=ctx)
				await bot.say("I found no results for `" + searchTerm + "`")
			elif status == 400:
				await report(str(json), source="Error in `!anime` search for term " + searchTerm, ctx=ctx)
				await bot.say("The bot made an error. My bad. A bug report has been automatically submitted")
			else:
				await report(str(json), source="Unknown Error Type", ctx=ctx)
				await bot.say("Something went wrong and I don't know why")
			return

		if "info" in commands:
			await bot.say(embed = dataObject.infoEmbed())
		else:	
			await bot.say(embed = dataObject.embed())
	except Exception as e:
		await report(str(e), source="!anime command", ctx=ctx)


# List your best girls!
@bot.command(pass_context=True, help=longHelp['bestGirl'], brief=briefHelp['bestGirl'], aliases=aliases['bestGirl'])
async def bestGirl(ctx):
	title = "!bestGirl - User Guide"
	description = ("A dedicated command for modifying a user's `BestGirl` list. As with the more general `!list` command, " + 
		"it allows for the storage of a user created table. In this case, the table is intended for listing and ranking " +
		"the best female characters in any media, typically anime.")
	commandDict = {"!bestGirl": "Presents your list",
			   "!bestGirl add <girl>": "Appends the entry to the end of your list",
			   "!bestGirl add [<index>] <girl>": "Appends the entry to the list at the index specified",
			   "!bestGirl clear": "Clears your list. Be very careful!",
			   "!bestGirl icon <url>/<attachment>": ("Sets the thumbnail of your list to an image, either by " + 
			   		"supplying a url or attaching an image"),
			   "!bestGirl move <indexA> <indexB>": "Moves the element in indexA to indexB. The item at indexB is moved down",
			   "!bestGirl multiadd <girl>; <girl>": "Appends multiple entries to the list at once. Entries are seperated by a semicolon",
			   "!bestGirl remove [<index>]": "Removes the entry at the designated index from your list",
			   "!bestGirl rename [<index>] <girl>": "Replaces the entry at one index with another",
			   "!bestGirl show <userMention>": "Displays the lists for the user mentioned",
			   "!bestGirl static": "Presents the user list, but this list will not change as future edits are made",
			   "!bestGirl swap <index> <index>": "Swaps the entries at the two locations",
			   "!bestGirl thumbnail <url>": "Sets a thumbnail for the list. URL must point directly to an image file",
			   "!bestGirl title <title>": ("Sets the title of the list. Replying without a title resets " 
			   								+ "the value to the default (i.e. '<Your name>'s list')"),
			   "!bestGirl help": "This command. Lists documentation"}
	helpEmbed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["bestGirl"])
	await listHelper(ctx, helpEmbed=helpEmbed, command="bestGirl", listID="BestGirl")


# Arbitrary code execution
@bot.command(pass_context=True, help=longHelp['code'], brief=briefHelp['code'], aliases=aliases['code'])
async def code(ctx):

	langs = {
		"c":["C (GCC 8.1.0)", "c", 3],
		"clisp":["CLISP (GNU CLISP 2.49.93 - GNU 8.1.0)", "clisp", 2],
		"cpp":["C++ (GCC 8.1.0)", "cpp", 3],
		"cpp14":["C++ 14 (GCC 8.1.0)", "cpp14", 2],
		"csharp":["C# (mono 5.10.1)", "csharp", 2],
		"haskell":["Hasell (ghc 8.2.2)", "haskell", 2],
		"java":["Java 10.0.1", "java", 2],
		"kotlin":["Kotlin 1.2.40 (JRE 10.0.1)", "kotlin", 1],
		"lua":["Lua 5.3.4", "lua", 1],
		"nodejs":["NodeJS 10.1.0", "nodejs", 2],
		"pascal":["Pascal (fpc-3.0.4)", "pascal", 2],
		"perl":["Perl 5.26.2", "perl", 2],
		"php":["PHP 7.2.5", "php", 2],
		"python2":["Python 2.7.15", "python2", 1],
		"python":["Python 3.6.5", "python3", 2],
		"go":["GO Lang 1.10.2", "go", 2],
		"scala":["Scala 2.12.5", "scala", 3],
		"scheme":["Scheme (Gauche 0.9.4)", "scheme", 1],
		"sql":["SQLite 3.23.1", "sql", 2],
		"swift":["Swift 4.1", "swift", 2],
		"r":["R Language 3.5.0", "r", 0],
		"ruby":["Ruby 2.5.1p57", "ruby", 2],
		"rust":["RUST 1.25.0", "rust", 2]
	}

	esolangs = {
		"ada":["Ada (GNATMAKE 8.1.0)", "ada", 2],
		"gccasm":["Assembler - GCC (GCC 8.1.0)", "gccasm", 1],
		"nasm":["Assembler - NASM 2.13.03", "nasm", 2],
		"bash":["Bash shell 4.4.19", "bash", 2],
		"bc":["BC 1.07.1", "", 1],
		"brainfuck":["Brainfuck (bfc-0.1)", "brainfuck", 0],
		"c99":["C-99 (GCC 8.1.0)", "c99", 2],
		"clojure":["Clojure 1.9.0", "clojure", 1],
		"cobol":["COBOL (GNU COBOL 2.2.0)", "cobol", 1],
		"coffeescript":["CoffeeScript 2.3.0", "coffeescript", 2],
		"d":["D (DMD64 D Compiler v2.071.1)", "d", 0],
		"dart":["Dart 1.24.3", "dart", 2],
		"elixir":["Elixir 1.6.4", "elixir", 2],
		"fsharp":["F# 4.1", "fsharp", 0],
		"factor":["Factor 8.29", "factor", 2],
		"falcon":["Falcon 0.9.6.8 (Chimera)", "falcon", 0],
		"fantom":["Fantom 1.0.69", "fantom", 0],
		"forth":["Forth (gforth 0.7.3)", "forth", 0],
		"fortran":["Fortran (GNU 8.1.0)", "fortran", 2],
		"freebasic":["FREE BASIC 1.05.0", "freebasic", 1],
		"groovy":["Groovy 2.4.15 (JVM 10.0.1)", "", 2],
		"hack":["Hack (HipHop VM 3.13.0)", "hack", 0],
		"icon":["Icon 9.4.3", "icon", 0],
		"intercal":["Intercal 0.30", "intercal", 0],
		"lolcode":["LOLCODE 0.10.5", "lolcode", 0],
		"nemerle":["Nemerle 1.2.0.507", "nermerle", 0],
		"nim":["Nim 0.18.0", "nim", 2],
		"objc":["Objective C (GCC 8.1.0)", "", 2],
		"ocaml":["Ocaml 4.03.0", "ocaml", 0],
		"octave":["Octave (GNU 4.4.0)", "octave", 2],
		"mozart":["OZ Mozart 2.0.0 (OZ 3)", "", 0],
		"picolisp":["Picolist 18.5.11", "picolisp", 2],
		"pike":["Pike v8.0", "pike", 0],
		"prolog":["Prolog (GNU Prolog 1.4.4)", "prolog", 0],
		"smalltalk":["SmallTalk (GNU SmallTalk 3.2.92)", "smalltalk", 0],
		#"spidermonkey":["SpiderMonkey 45.0.2", "spidermonkey", 1],
		"racket":["Racket 6.12", "racket", 1],
		"rhino":["Rhino JS 1.7.7.1", "rhino", 0],
		"tcl":["TCL 8.6.8", "tcl", 2],
		"unlambda":["Unlambda 0.1.3", "unlambda", 0],
		"vbn":["VB.Net (mono 5.10.1)", "vbn", 2],
		"verilog":["VERILOG 10.2", "verilog", 2],
		"whitespace":["Whitespace 0.3", "whitespace", 0],
		#"yabasic":["YaBasic 2.769", "yabasic", 0], #TAKEN OUT SO THE LANG LIST DOESN'T EXCEED MESSAGE CHAR LIMIT
	}

	creditsCheckURL = "https://api.jdoodle.com/v1/credit-spent"
	executeURL = "https://api.jdoodle.com/v1/execute"

	try:
		# removes the "!anime" envocation portion of the message
		message = stripCommand(ctx.message.content)

		# Parsing commands
		commands = []
		i = 0;
		while i < len(message) and message[i] == "-":  # Looks for commands
			command = ""
			i += 1
			# iterates over charcters until it finds the end of the command
			while i < len(message) and message[i].isalnum():
				command = command + message[i]
				i += 1;
			commands.append(command.lower())
			i += 1
		message = message[i:].strip()  # Removes commands from the message
		# Explain all the commands to the user
		if "help" in commands or (len(message) == 0 and len(commands) == 0):
			title = "!code - User Guide"
			description = ("Remote code execution. Allows users to write code and submit it to the bot for remote execution, " +
				"after which the bot prints out the results, any error codes, the execution time, and mmemory consumption. " +
				"The command supports 65 different languages, including Java, Python 2/3, PHP, Swift, C++, Rust, and Go.\n\n" +
				"To invoke execution, include a block of code using the multiline Discord code format " + 
				"( https://support.discordapp.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline- ). " +
				"To use this formatting, use three backticks (`, the key above the tab key), followed immediately (no spaces!) " +
				"by the language tag, followed by a linebreak, followed by your code. Close off the code block with three more " + 
				"backticks. It's a little complicated, I apologize. It's Discord's formatting rules, not mine.\n\n**Be advised**\n" + 
				"Remote execution will time out after 5 seconds and does not support external libraries or access to the internet.")

			commandDict = {"-help":"Shows this user guide",
							"-full":"Shows the full list of supported languages",
							"-lang":"Shows the common languages supported by this command",
							}
			await bot.say(embed=dictToEmbed(commandDict, title=title, description=description, 
				thumbnail_url=commandThumbnails["code"]))
			return

		if "ls" in commands or "full" in commands:
			message = "`Name` (`compiler version`) - `tag`\n---------"
			for tag in langs.keys():
				name = langs[tag][0] # Name
				message += "\n**" + name + "** : " + tag
			if "full" in commands:
				message += "\n---------"
				for tag in esolangs.keys():
					name = esolangs[tag][0] # Name
					message += "\n**" + name + "** : " + tag
			await bot.say(trimToLength(message, 2000))
			return

		if "dev" in commands:
			[json, responseCode] = await get_JSON_with_POST(url=creditsCheckURL, json={
				"clientId": JDOODLE_ID, 
				"clientSecret": JDOODLE_SECRET})
			if "used" not in json.keys():
				await report(json, "Failed to get credit count for JDOODLE account", ctx=ctx)
				await bot.say("Forces external to your request have caused this command to fail.")
				return
			await bot.say(json['used'])
			return

		arguments = list()
		'''ADD IMPLEMENTATION OF ARGUMENT LIST PARSING HERE'''

		if "```" in message:
			trimmedMessage = message[message.find("```") + 3:]
			if "```" in trimmedMessage:
				trimmedMessage = trimmedMessage[:trimmedMessage.find("```")]
				splitMessage = trimmedMessage.split("\n", maxsplit = 1)
				if len(trimmedMessage) == 0:
					await bot.say("You need to put code inside the backticks")
					return
				if trimmedMessage[0] not in [" ", "\n"] and len(splitMessage) > 1:
					[language, code] = splitMessage
					language = language.strip()
					for key in esolangs.keys():
						langs[key] = esolangs[key]
					if language.lower() in langs.keys():
						response = await get_JSON_with_POST(url=executeURL, json={
							"clientId": JDOODLE_ID, 
							"clientSecret": JDOODLE_SECRET,
							"script": code,
							"language" : langs[language.lower()][1],
							"versionIndex" : langs[language.lower()][2]
						})
						[json, responseCode] = response
						if responseCode == 429:
							await report(json, "Bot has reached its JDOODLE execution limit", ctx=ctx)
							await bot.say("The bot has reached its code execution limit for the day.")
							return
						outputEmbed = Embed()
						if "error" in json.keys():
							outputEmbed.description = json['error']
							outputEmbed.title = "ERROR"
							outputEmbed.color = ERROR_EMBED_COLOR
							await bot.say(embed = outputEmbed)
							return
						outputEmbed.title = "Output"
						outputEmbed.color = CODE_EMBED_COLOR
						outputEmbed.add_field(name="CPU Time", value=str(json['cpuTime']) + " seconds")
						outputEmbed.add_field(name="Memory Usage", value=json['memory'])
						if len(json['output']) > 2046:
							outputEmbed.description = "``` " + trimToLength(json['output'], 2040) + "```"
						else:
							outputEmbed.description = "``` " + json['output'] + "```"
						await bot.say(embed = outputEmbed)
					else:
						await bot.say(("I don't know the language '" + language + "'. Type `!code -full` to see the " + 
							"list of languages I support, or type `!code -ls` to see the most popular ones"))
				else:
					await bot.say(("There was no language tag. Remember to include the language tag immediately after the" + 
							" opening backticks. Type `!code -ls` or `!code -full` to find your language's tag"))
			else:
				await bot.say("You didn't close your triple backticks")
		else:
			await bot.say("I don't see any code")
	except Exception as e:
		await report(str(e), source="!code command", ctx=ctx)

@bot.command(pass_context=True, help=longHelp['colton'], brief=briefHelp['colton'], aliases=aliases['colton'], hidden=True)
async def colton(ctx):
	global lastColton, dailyColton, totalColton

	totalColton += 1
	now = datetime.now()
	messageAddition = "!"
	if lastColton.day != now.day:
		dailyColton = 1
		messageAddition = ", which makes this his first time today"
	else:
		dailyColton += 1
		messageAddition = ", which makes this " + str(dailyColton) + " times today alone!"
	await bot.say(("Wow! Colton has now mentioned being forever alone " + str(totalColton) + " times!\n" + 
		"The last time he mentioned being forever alone was **" + lastColton.strftime("%c") + "**" + messageAddition))
	lastColton = now
	cacheColton()

@bot.command(help=longHelp['hello'], brief=briefHelp['hello'], aliases=aliases['hello'])
async def hello():
	await bot.say(returnRandomElement(greetings))


# User creation of arbitrary lists and editing them
@bot.command(pass_context=True, help=longHelp['ls'], brief=briefHelp['ls'], aliases=aliases['ls'])
async def ls(ctx):
	title = "!list - User Guide"
	description = ("List creation and management. Allows users to create arbitrary lists that the bot will store. " +
		"Users can then add and remove elements, modify elements, and move elements around. Lists can also have unique " +
		"titles and thumbnails.")
	commandDict = {"!list": "Will print the current list if there is one",
						   "help": "This command. Lists documentation",
						   "clear <id?>": "Deletes all elements from the list but does not remove the list",
						   "curr": "Prints the list the user is currently editing",
						   "create <id>": "Create a new user list with the specified ID",
						   "drop <id>": "Deletes the table with specified ID. THIS IS PERMANENT AND CANNOT BE UNDONE. Use with caution",
						   "show": "Show the IDs for all the user's lists",
						   "use <id>": "Move the user space to the list with that ID. In response, it will print the contents of the list",
						   "add <item>": "Adds element at the end of the list",
						   "add [<index>] <item>": "Adds element to the list at the given index",
						   "multiadd <item>;<item>": "Adds every element of a semicolon seperated list to the end of the list",
						   "move <indexA> <indexB>": "Moves the element at indexA to indexB",
						   "remove <index>": "Removes the element at the given index",
						   "replace [<index>] <item>": "Replaces the element at that index with that item",
						   "swap <indexA> <indexB>": "Swaps the positions of the elements at indexA and indexB",
						   "thumbnail <url>": "Sets a thumbnail for the list. URL must point directly to an image file", 
						   "title <title>": "Assigns the title to the list with that index",}
	helpEmbed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["ls"])
	await listHelper(ctx, helpEmbed=helpEmbed, command="list")

@bot.command(pass_context = True, help = longHelp['meow'], brief = briefHelp['meow'], aliases = aliases['meow'])
async def meow(ctx):
	global nextMeowURL
	# await bot.say("I don't do that anymore")
	try:
		if nextMeowURL is None:
			await getMeowImageURL()
		if nextMeowURL is None:
			await bot.say("This command is having a problem. Try again in a bit.")
			return
		embededCat = Embed().set_image(url=nextMeowURL)
		nextMeowURL = None
		embededCat.color = MEOW_EMBED_COLOR
		await bot.say(embed=embededCat)
		await getMeowImageURL()
	except Exception as e:
		await report(str(e), source="Meow command", ctx=ctx)


# Present the astronomy picture of the day
@bot.command(help=longHelp['nasa'], brief=briefHelp['nasa'], aliases=aliases['nasa'])
async def nasa():
	try:
		[json, status_code] = await get_JSON_with_GET(
			"https://api.nasa.gov/planetary/apod?api_key=OSoqPlD9uDBXvXXpn4ybhFt1ulflqtmGtQnkLgAD")
		if json['media_type'] == "video":
			await bot.say("**" + json['title'] + "**\n" + json['explanation'] + "\n" + json['url'])
		else:
			embed = Embed().set_image(url=json['hdurl'])
			embed.title = json['title']
			embed.description = json['explanation']
			embed.set_footer(
				icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/1200px-NASA_logo.svg.png",
				text="Courtesy of NASA Astronomy Photo of the Day https://apod.nasa.gov/apod/astropix.html")
			embed.color = NASA_EMBED_COLOR
			await bot.say(embed=embed)
	except Exception as e:
		await report(str(e), source="NASA APOD command", ctx=ctx)


# Modify the settings of the bot
@bot.command(pass_context=True, aliases=aliases['preferences'], hidden=True)
async def preferences(ctx):
	global plist

	if ctx.message.author.id not in AUHTORIZED_IDS:
		await bot.say("This command is restricted to dev use only")
		return

	# removes the "!preferences" envocation portion of the message and grabs the function and parameter
	[function, parameter] = functionParameter(ctx.message.content)

	debugMode = False
	if debugMode == True:
		await bot.say("Function: " + function + "\nContent: " + parameter)

	if function == "add":
		[keyType, value] = parseKeyValue(parameter)
		if ":" not in keyType:
			await bot.say("I don't see a value type in the key declaration")
			return
		[key, typeCode] = keyType.split(":")
		await bot.say(key + "\n" + typeCode)
		return

	if function == "load":
		if len(parameter) == 0:
			await bot.say("Supported targetes are 'tags' and 'lists'")
		target = parameter.lower().strip()
		if parameter == "tags":
			loadTags()
			if failedToLoadTags is None:
				await bot.say("Loaded.")
			else:
				await bot.say(str(failedToLoadTags))
		elif parameter == "lists":
			loadLists()
			if failedToLoadLists is None:
				await bot.say("Loaded.")
			else:
				await bot.say(str(failedToLoadLists))
		return

	if function == "set":
		(key, value) = parseKeyValue(parameter)
		await bot.say("I saw: set [" + key + "] to [" + value + "]")
		return

	if function == "ls":
		pListEmbed = Embed()
		pListEmbed.title = "Prefence Settings"
		pListEmbed.color = PLIST_EMBED_COLOR
		keyCount = 0
		for key in sorted(list(plist.keys())):
			pListEmbed.add_field(name=key, value=plist[key], inline=False)
			keyCount += 1
			if keyCount == 25:
				await bot.say(embed=pListEmbed)
				pListEmbed = Embed()
				pListEmbed.title = "Prefence Settings (cont.)"
				pListEmbed.color = PLIST_EMBED_COLOR
				keyCount = 0
		await bot.say(embed=pListEmbed)
		return


	# !preferences help
	if function == "help":
		commandDict = {"!preferences help": "Displays this message",
						"!preferences load A" : "Refreshes database values. Supported targets are 'lists' and 'tags'",
						"!preferences ls" : "Prints all stored plist values",
						"!preferences set [A] B" : "Sets a plist value"}
		await bot.say("`!preferences` User Guide", embed=dictToEmbed(commandDict, thumbnail_url=commandThumbnails["preferences"]))
		return

	if function == "":
		await bot.say("Type `!preferences help` for information on this command")
	return


# Randomizer
@bot.command(pass_context=True, help=longHelp['rand'], brief=briefHelp['rand'], aliases=aliases['rand'])
async def rand(ctx):
	try:
		# RAND -------------------------------------- PRELIMINARY PROCESSES

		# removes the "!rand" envocation portion of the message
		[function, parameter] = functionParameter(ctx.message.content)
			
		debugMode = False
		if debugMode == True:
			await bot.say("Function: " + function + "\nContent: " + parameter)

		# RAND -------------------------------------- HELPER METHODS
		# RAND -------------------------------- FUNCTIONS

		# !rand coin
		if function == "coin":
			await bot.say(returnRandomElement(["Heads!", "Tails!"]))
			return

		# !rand item <item>, <item>, <item>
		if function == "item":
			if len(parameter) == 0:
				await bot.say("I need a comma delinated list (e.g. '!random item A, B, C, D, E' etc.) to pick from")
				return
			itemList = list(filter(None, parameter.split(",")))
			if len(itemList) == 0:
				await bot.say("There aren't any items here for me to choose from!")
				return
			elif len(itemList) == 1:
				await bot.say("There's only one item. That's an easy choice: " + itemList[0])
				return
			await bot.say("I choose... " + returnRandomElement(itemList).strip())
			return

		# rand num
		# rand num <num>
		# rand num <num> <num>
		if function == "num" or function == "number":
			if len(parameter) == 0:
				await bot.say(str(random.random()))
				return
			numbers = parameter.split(" ")
			if len(numbers) == 1:
				try:
					bound = int(numbers[0])
				except:
					await bot.say("I can't seem to parse '" + numbers[0] + "'")
					return
				await bot.say(str(random.randint(0, bound)))
			else:
				try:
					lowerBound = int(numbers[0])
				except:
					await bot.say("I can't seem to parse '" + numbers[0] + "'")
					return
				try:
					upperBound = int(numbers[1])
				except:
					await bot.say("I can't seem to parse '" + numbers[1] + "'")
					return
				if upperBound < lowerBound:
					temp = upperBound
					upperBound = lowerBound
					lowerBound = temp
				message = str(random.randint(lowerBound, upperBound))
				if len(numbers) > 2:
					message += "\n\nFYI, this function takes a maximum of two only arguments"
				await bot.say(message)
			return

		# !rand roll <num>d<sides>, <num>d<sides>
		if function == "roll":
			dice = list(filter(None, parameter.split(",")))
			total = 0
			message = ""
			for die in dice:
				die = die.strip()
				dLoc = die.find("d")
				# if there is no "d"
				if dLoc == -1:
					await bot.say("I don't see a 'd' in the argument '" + die + "'.")
					return

				# if there is no number in front of the "d", it is assumed to be one
				if dLoc == 0:
					count = "1"
					sides = die[1:]
				# if there is no number after the "d", the bot rejects it
				elif (dLoc + 1) == len(die):
					await bot.say(
						"I don't see a number after 'd' in the argument '" + die + "'. I need to know a number of sides")
					return
				else:
					count = die[0:dLoc]
					sides = die[dLoc + 1:]

				try:
					sides = int(sides)
				except:
					await bot.say("I'm sorry, but '" + sides + "' isn't a parsable integer...")
					return
				try:
					count = int(count)
				except:
					await bot.say("I'm sorry, but '" + count + "' isn't a parsable integer...")
					return

				if count > 100000:
					await bot.say(str(
						count) + " dice is a *lot*. I think rolling that many would hurt my head  :confounded:\nPlease don't make me do it.")
					return
				diceSum = 0
				for i in range(0, count):
					diceSum += random.randint(1, sides)
				total += diceSum
				message += str(count) + " d" + str(sides) + ": I rolled " + str(diceSum) + "\n"
			if len(dice) > 1:
				await bot.say(message + "Total: " + str(total))
			else:
				await bot.say(message)
			return

		# RAND -------------------------------- HELP

		if function == "":
			await bot.say("Type `!rand help` for information on this command")
	except Exception as e:
		await report(str(e), source="Rand command", ctx=ctx)

	# !rand help
	if function == "help":
		title = "!rand - User Guide"
		description = ("Randomizer. This command is used for randomization in several circumstances. From coin flips " +
			"and dice rolls to random numbers and picking from lists, let the bot generate random numbers for you.\n\n" + 
			"**WARNING**\nThis command is only pseudorandom and not cryptographically secure")
		commandDict = {"!rand": "No function. Will present this help list",
					   "!rand help": "This command. Shows user guide",
					   "!rand coin": "Flips a coin",
					   "!rand item <A>, <B>, <C>...": "Returns a random item from a comma delinated list",
					   "!rand num": "Returns a random decimal",
					   "!rand num <A>": "Returns a random integer from 0 to A",
					   "!rand num <A> <B>": "Returns a random integer between A and B",
					   "!rand roll <num>d<sides>,...": ("Rolls the number of n-sided dice presented." 
					   			+ " Multiple dice types can be rolled with a comma seperated list"),}
		await bot.say(embed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["rand"]))
		return

	await bot.say(
		"I don't recognize the function `" + function + "`. Type `!rand help` for information on this command")


# Bot call and response
@bot.command(pass_context=True, help=longHelp['tag'], brief=briefHelp['tag'], aliases=aliases['tag'])
async def tag(ctx):
	global tags

	# ------------------------------------------------- COMMAND LOGIC
	try:
		parsedCTX = parseApos(ctx.message.content)
		message = stripCommand(parsedCTX) #removes the command invocation from the message content

		if message is "":  # handles an empty command
			await bot.say("Type `!tag help` for help using this command")

		# Parsing commands
		commands = []
		i = 0;
		while i < len(message) and message[i] == "-":  # Looks for commands
			command = ""
			i += 1
			# iterates over charcters until it finds the end of the command
			while i < len(message) and message[i].isalnum():
				command = command + message[i]
				i += 1;
			commands.append(command.lower())
			i += 1
		message = message[i:].strip()  # Removes commands from the message

		# Selecting tag group
		if ctx.message.server.id not in tags["server"].keys():
			tags["server"][ctx.message.server.id] = {}
		if ctx.message.server is not None:
			selectedTags = tags["server"][ctx.message.server.id]  # makes the server tags the selected tag group
		for key in tags["global"].keys():
			selectedTags[key] = tags["global"][key]
		edit = False  # flag for if the user is overwriting an existing tag
		append = False  # flag for if the user is appending to an existing tag
		newLine = False  # flag for if the user wants a line break before their append is added
		domain = "server"
		tagOwner = ctx.message.server.id  # Parameter passed to the MySQL update function to specify owner of the tag
		if "u" in commands:  # if the "-u" command is invoked
			domain = "user"
			tagOwner = ctx.message.author.id
			if ctx.message.author.id not in tags["user"].keys():  # if that user does not have a user tag group
				tags["user"][ctx.message.author.id] = {}  # Creates a user tag group
			selectedTags = tags["user"][ctx.message.author.id]  # Changes the selected tag group to the user's tags

		# Acting on commands
		if "help" in commands:  # provides help using this command
			title = "!tag - User Guide"
			description = ("Bot call and response. Allows the user to pair a message or attached image with a tag. These " +
				"tags can then be used to have the bot respond with the associated content. By default, these tags are " +
				"server wide, but by using the user list command (`-u`, e.g. `!tag -u [base] All your base are belong to us`) " +
				"the user can specify personal tags. This allows a user to store a different value for a key than the server " +
				"value and to make tags that will be available for that user across servers and in DMs.")
			commandDict = {
				"-ap [<key>] <value>": "If the tag entered already exists, the new text will be appended to the end after a space",
				"-apnl [<key>] <value>": "If the tag entered already exists, the new text will be appended to the end after a line break",
				"-edit [<key>] <value>": "If the tag entered already exists, the existing tag will be overwritten",
				"-help": "Show this command",
				"-ls": "Lists the tags within the selected group",
				"-rm <key>": "removes a tag from the group",
				"-u": "Selects your specific tag group instead of the server tags for the following command"}
			await bot.say(embed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["tag"]))
			return
		if "ls" in commands:  # lists the saved tags in the selected tag group
			tagList = ""
			for tag in sorted(selectedTags.keys()):
				if tag in tags["global"].keys():
					tagList += ", `" + tag + "`"
				else:
					tagList += ", " + tag
			if tagList == "":
				if domain == "user":
					await bot.say("You do not have any saved tags")
				else:
					await bot.say("This server does not have any saved tags")
				return
			tagList = tagList[2:]  # pulls the extraneous comma off
			await bot.say("**The tags I know are**\n" + tagList + "")
			return
		if "edit" in commands:
			edit = True  # sets the editing flag for "true", so that if the tag already exists it will be overwritten
		if "ap" in commands:
			edit = True
			append = True
		if "apnl" in commands:
			edit = True
			append = True
			newLine = True
		if "rm" in commands:  # deletes a saved tag
			key = message.lower()
			if key in selectedTags.keys():
				del selectedTags[key]
				await bot.say("Okay. I deleted it")
				updateTagRemove(key, tagOwner, domain)
			else:  # If that tag didn't exist
				await bot.say("Hmmm, that's funny. I didn't see the tag `` " + message + " `` in the saved tags list.")
			return

		# Acting on tag primary message
		if len(message) == 0:
			if len(commands) > 0:
				await bot.say("I see some commands, but no key or value to work with :/")
			return
		if message[0] is "[":  # If the user is setting the tag
			tagKeyValue = parseKeyValue(message,
										ctx.message.attachments)  # returns an array of the parsed key and value of the tag
			if tagKeyValue[0] is None:
				errorMessages = {
					"EMPTY KEY":"There was no key to store",
					"UNCLOSED KEY":"You didn't close your brackets",
					"NO VALUE":"There was no text to save for the key provided",
					"WHITESPACE KEY":"Just because this bot is written in Python does not mean whitespace is an acceptable tag",
					"KEY STARTS WITH -":"The `-` character denotes the start of a command and cannot be used in tag keys"}
				await bot.say(errorMessages[tagKeyValue[1]])
				return
			else:
				tagKey = tagKeyValue[0].lower()
				tagValue = tagKeyValue[1]
				if tagKey in selectedTags.keys():
					if tagKey in tags["global"].keys():
						await bot.say(
							"I'm sorry, but the key `` " + tagKey + " `` has already been reserved for a global tag")
						return
					elif edit is False:
						await bot.say(
							"I already have a value stored for the tag `` " + tagKey + " ``. Add `-edit` to overwrite existing tags")
						return
					elif append is True:
						if newLine is True:
							selectedTags[tagKey] = selectedTags[tagKey] + "\n" + tagValue
						else:
							selectedTags[tagKey] = selectedTags[tagKey] + " " + tagValue
						updateTagEdit(tagKey, selectedTags[tagKey], tagOwner, domain)
						await bot.say("Edited!")
						return
					else:
						selectedTags[tagKey] = tagValue
						updateTagEdit(tagKey, tagValue, tagOwner, domain)
						await bot.say("Edited!")
						return
				selectedTags[tagKey] = tagValue
				updateTagAdd(tagKey, tagValue, tagOwner, domain)
				await bot.say("Saved!")
		else:
			message = message.lower()
			if message in selectedTags.keys():
				await bot.say(trimToLength(str(selectedTags[message]), 2000))
			else:
				await bot.say(
					"I don't think I have a tag `" + message + "`. Type `!tag -ls` to see the tags I have saved")
	except Exception as e:
		await report(str(e), source="Tag command", ctx=ctx)

# Returns a description of an item from Wikipedia
@bot.command(pass_context=True, help=longHelp['wiki'], brief=briefHelp['wiki'], aliases=aliases['wiki'])
async def wiki(ctx):

	# ---------------------------------------------------- HELPER METHODS

	async def searchForTerm(searchTerm):
		wikiSearchURL = "http://en.wikipedia.org/w/api.php?action=query&format=json&prop=&list=search&titles=&srsearch=" + quote(searchTerm)
		wikiSearchJSON = await get_JSON_with_GET(wikiSearchURL) # Looks for articles matching the search term
		if wikiSearchJSON[0]['query']['searchinfo']['totalhits'] == 0:
			return None
		return wikiSearchJSON[0]['query']['search'][0]['title'] # Makes the title URL friendly

	async def queryArticle(articleTitle):
		quotedArticleTitle = quote(articleTitle) # Makes the title URL friendly
		wikiQueryURL = ("http://en.wikipedia.org/w/api.php?action=query&format=json&prop=info%7Cextracts%7Cdescription&titles=" 
			+ quotedArticleTitle + "&exlimit=max&explaintext=1&exsectionformat=plain")
		response = await get_JSON_with_GET(wikiQueryURL) # Gets the article details
		if "-1" in response[0]['query']['pages'].keys() : # Wikipedia returns a '-1' for the page if it found nothing
			return None
		response = list(response[0]['query']['pages'].values())[0] # Gets the first result
		if "extract" not in response.keys(): #If the returned result isn't usable
			await report(trimToLength(response, 2000), source="Wiki command found no useful article", ctx=ctx) #Figure out why it's not usable
			return None
		title = response['title']
		extract = response['extract']
		if 'description' in response.keys(): #Some articles don't have summaries
			description = response['description']
		else:
			description = None
		return [title, extract, description]

	async def parseSections(articleTitle):
		quotedArticleTitle = quote(articleTitle) # Makes the title URL friendly
		wikiParseURL = "http://en.wikipedia.org/w/api.php?action=parse&format=json&page=" + quotedArticleTitle + "&prop=sections"
		response = await get_JSON_with_GET(wikiParseURL) # Gets the article details
		if "error" in response[0].keys():
			return None
		tableOfContents = "```"
		for header in response[0]["parse"]["sections"]:
			tableOfContents += "\n" + (" " * header["toclevel"]) + stripHTMLTags(header["line"])
		return tableOfContents + "```"

	def getSection(sectionTitle, extract):
		extractSplits = extract.split("\n\n\n")
		for extractSection in extractSplits:
			if extractSection.startswith(sectionTitle + "\n"):
				return extractSection
		return None

	# ---------------------------------------------------- COMMAND LOGIC	

	try:
		message = stripCommand(ctx.message.content)
		# Parsing commands
		commands = []
		i = 0;
		while i < len(message) and message[i] == "-":  # Looks for commands
			command = ""
			i += 1
			# iterates over charcters until it finds the end of the command
			while i < len(message) and message[i].isalnum():
				command = command + message[i]
				i += 1;

			if command == "h":
				command = "help"
			elif command == "f":
				command = "full"
			elif command == "s":
				command = "sections"
			commands.append(command.lower())
			i += 1

		# Act on commands
		if "help" in commands:  # provides help using this command
			title = "`!wiki` User Guide"
			description = ("Wikipedia search engine. Searches wikipedia for an article with the title provided and returns " +
				"the opening section or the full article text. Additionally, it can return the sections of an article or " +
				"the text of a designated section.\n\nFor ease of use, all commands can be shortened to their first letter " +
				" (e.g. `!wiki -s [History] Discord (software)`)")
			commandDict = {
				"-help" : "Displays this user guide. Gives instructions on how to use the command and its features",
				"-full <title>" : "Displays the full extract of the article, up to the embed character limit",
				"-sections <title>" : "Displays the section titles for the article",
				"-sections [<section>] <title>" : "Displays the contents of that section of the article"}
			await bot.say(embed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["wiki"]))
			return

		searchTerm = message[i:].strip()  # Removes commands from the message and makes it the search term
		if "sections" in commands:
			if searchTerm[0] == "[":
				[section, searchTerm] = parseKeyValue(searchTerm)
				if section is None:
					errorMessages = {
						"EMPTY KEY":"I see no section title to search for",
						"UNCLOSED KEY":"You didn't close your brackets",
						"NO VALUE":"I see no article to look for",
						"WHITESPACE KEY":"Whitespace is not a valid section header",
						"KEY STARTS WITH -":"The `-` character denotes the start of a command"}
					await bot.say(errorMessages[searchTerm])
					return
			else:
				section = None

		if searchTerm == "":
			await bot.say("I need a term to search")
			return
		quotedSearchTerm = quote(searchTerm) #Makes the search term URL friendly
		articleTitle = await searchForTerm(searchTerm)
		if articleTitle is None:
			await bot.say("I found no articles matching the term '" + searchTerm + "'")

		if "sections" in commands:
			if section is None:
				await bot.say(await parseSections(articleTitle))
			else:
				[title, extract, summary] = await queryArticle(articleTitle)
				extractSection = getSection(section, extract)
				if extractSection is None:
					await bot.say("I didn't find a section title `" + section + "`")
				else:
					wikiEmbed = Embed()
					wikiEmbed.title = title
					wikiEmbed.description = trimToLength(extractSection, 2048)
					wikiEmbed.add_field(name="Full Article", 
						value="http://en.wikipedia.org/wiki/" + quote(title) + "#" + quote(section), inline=False)
					wikiEmbed.color = WIKI_EMBED_COLOR
					await bot.say(embed=wikiEmbed)
			return

		[title, extract, summary] = await queryArticle(articleTitle)
		wikiEmbed = Embed()
		wikiEmbed.title = title
		if "full" in commands:
			description = trimToLength(extract, 2048)
		else:
			description = trimToLength(extract[:extract.find("\n")], 2048);
		wikiEmbed.description = description
		wikiEmbed.add_field(name="Full Article", value="http://en.wikipedia.org/wiki/" + quote(title), inline=False)
		wikiEmbed.color = WIKI_EMBED_COLOR # Make the embed white
		await bot.say(embed=wikiEmbed)
	except Exception as e:
		await report(str(e), source="Wiki command", ctx=ctx)

# Interfaces with the WolframAlpha API
@bot.command(pass_context=True, help=longHelp['wolf'], brief=briefHelp['wolf'], aliases=aliases['wolf'])
async def wolf(ctx):
	try:
		# removes the "!wolf" invocation portion of the message
		message = stripCommand(ctx.message.content)

		if message == "":
			await bot.say("You must pass in a question to get a response")
			return

		async with aiohttp.ClientSession() as session:
			async with session.get("http://api.wolframalpha.com/v1/result?appid=" + WOLFRAMALPHA_APPID + "&i=" + quote(
					message)) as resp:
				if resp.status is 501:
					await bot.say(
						"WolframAlpha could not understand the question '" + message + "' because " + resp.reason)
					return
				data = await resp.content.read()
				await bot.say(data.decode("utf-8"))
	except Exception as e:
		await report(str(e), source="Wolf command", ctx=ctx)

# Interfaces with the WolframAlpha API
@bot.command(pass_context=True, help=longHelp['woof'], brief=briefHelp['woof'], aliases=aliases['woof'])
async def woof(ctx):
	# await bot.say("I don't do that anymore")
	try:
		json = await get_JSON_with_GET("https://dog.ceo/api/breeds/image/random")
		if 'status' not in json[0].keys() or json[0]['status'] != "success":
			await bot.say("I have encountered an error. Please contact the bot creator")
			await flag("Error with random dog api", description=json, ctx=ctx)
			return
		embededDog = Embed().set_image(url=json[0]['message'])
		embededDog.color = WOOF_EMBED_COLOR
		await bot.say(embed=embededDog)
	except Exception as e:
		await report(str(e), source="Woof command", ctx=ctx)

# Posts the "Yes! Yes! YES!" JoJo video because people kept typing `!yes` instead of `!tag yes`
@bot.command(pass_context=True, hidden=True)
async def yes(ctx):
	await bot.say("https://www.youtube.com/watch?v=sq_Fm7qfRQk")

# Post a random furry porn picture from e621.net OwO
@bot.command(pass_context=True, hidden=True)
async def yiff(ctx):
	global nextYiffURL
	memeQuotes = ["glom", "OwO", "*notices bulge*", "What's this?",
				  "#OwO#", "UwU", "Want to see my fursona?", "*pounces on you*",
				  "Don't kinkshame me", "furries < scalies", "furries > scalies",
				  "I own three copies of Zootopia on Blu-Ray", "KNOT ME DADDY",
				  "Look how wide I can gape my anus...", "My fur suit is arriving next Monday"]
	try:
		if ctx.message.content.strip() in ["!yiff help", "!yiff -help"]:
			await bot.say("There is no help for any of us in this god forsaken world.")
			return
		if nextYiffURL is None:
			await getYiffImageURL()
		embededPhoto = Embed().set_image(url=nextYiffURL)
		embededPhoto.color = YIFF_EMBED_COLOR
		await bot.send_message(bot.get_channel(HERESY_CHANNEL_ID), returnRandomElement(memeQuotes), embed=embededPhoto)
		await getYiffImageURL()
	except Exception as e:
		await report(str(e), source="yiff command", ctx=ctx)

# Search youtube for a video
@bot.command(pass_context=True, help=longHelp['youtube'], brief=briefHelp['youtube'], aliases=aliases['youtube'])
async def youtube(ctx):
	try:
		query = stripCommand(ctx.message.content)
		requestURL = "https://www.googleapis.com/youtube/v3/search"
		params = {"part":"id",
		"maxResults":1,
		"q":query,
		"relevanceLanguage":"en-us",
		"type":"video",
		"videoEmbeddable":"true",
		"fields":"items(id(playlistId,videoId))",
		"key":YOUTUBE_KEY}
		[json, responseCode] = await get_JSON_with_GET(requestURL, params=params)
		if responseCode != 200:
			await report("Failed to find video with search '" + query + "'", source="youtube command", ctx=ctx)
			await bot.say("There was a problem retrieving that video")
			return
		await bot.say("https://www.youtube.com/watch?v=" + json['items'][0]['id']['videoId'])
	except Exception as e:
		await report(str(e), source="youtube command", ctx=ctx)

###### VOICE

@bot.command(pass_context=True, hidden=True, help=longHelp['join'], brief=briefHelp['join'], aliases=aliases['join'])
async def join(ctx):
	"""Makes suitsBot join the voice channel."""
	authorVoiceChannel = ctx.message.author.voice_channel  # Gets the voice channel the author is in
	if authorVoiceChannel is None:  # Ignores the command if the author is not in voice
		await bot.say("You are not in a voice channel right now")
		return
	if bot.is_voice_connected(ctx.message.server):
		voiceChannel = bot.voice_client_in(ctx.message.server).channel
		if voiceChannel == authorVoiceChannel:  # Ignores the command if the bot is already in the author's voice channel
			await bot.say("I'm already in your voice channel")
			return
		else:  # If the bot is connected to a different voice channel than the author
			bot.player.stop()  # stops any active voice clip
			voice = bot.voice_client_in(ctx.message.server)
			await voice.move_to(authorVoiceChannel)  # Moves the bot to the new channel
	else:  # If the bot is not connected to voice
		voice = await bot.join_voice_channel(authorVoiceChannel)  # Joins the author's voice channel
	await bot.say("Joining voice channel...")
	player = voice.create_ffmpeg_player(QUOTE_FOLDER + 'hello_there_obi.mp3')  # Creates an ffmpeg player
	bot.player = player
	player.start()  # Plays joining voice clip


@bot.command(pass_context=True, help=longHelp['say'], brief=briefHelp['say'], aliases=aliases['say'])
async def say(ctx):
	# List of quote files
	quotes = {"anthem": ["**SOYUZ NERUSHIMY RESPUBLIK SVOBODNYKH SPLOTILA NAVEKI VELIKAYA RUS'!**", "anthem.mp3"],
			  "austin": ["IT'S ME, AUSTIN!", "itsMeAustin.mp3"],
			  "beat my dick": ["Good evening Twitter, it's ya boi EatDatPussy445.", "beatTheFuck.wav"],
			  "bold strategy": ["It's a bold strategy cotton, let's see if it pays off for 'em",
								"bold-strategy-cotton.mp3"],
			  "cavalry": ["*britishness intensifies*", "cheersLove.ogg"],
			  "deja vu": ["Ever get that feeling of deja vu?", "dejaVu.ogg"],
			  "disco": ["Reminder: You can stop media using the `!say -stop` command", "platinumDisco.mp3"],
			  "do it" : ["*Do it*", "doIt.mp3"],
			  "everybody": ["Se *no*!", "everybody.wav"],
			  "hentai": ["It's called hentai, and it's *art*", "itsCalledHentai.mp3"],
			  "hello there": ["**GENERAL KENOBI**", "hello_there_obi.mp3"],
			  "heroes never die": ["Heroes never die!", "heroesNeverDie.ogg"],
			  "high noon": ["It's hiiiiiigh nooooooon...", "itsHighNoon.ogg"],
			  "how": ["**I MADE MY MISTAKES**", "howCould.mp3"],
			  "i tried so hard" : ["Woah there, don't cut yourself on that edge", "inTheEnd.mp3"],
			  "it was me": ["Ko! No! Dio! Da!", "itWasMeDio.mp3"],
			  "laser sights": ["*Fooking laser sights*", "fookin-laser-sights.mp3"],
			  "leroy": ["LEEEEEEROOOOOOOOOOOOOY", "leroy.mp3"],
			  "love": ["AND IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII...", "iWillAlwaysLoveYou.mp3"],
			  "nerf this": ["It's nerf or nothing", "nerfThis.ogg"],
			  "nani": ["NANI SORE!?", "nani-sore.mp3"],
			  "nico": [
				  "Nico Nico-nii~ Anata no Heart ni Nico Nico-nii, Egao todokeru Yazawa Nico Nico~ Nico-nii te oboeteru Love Nico~ XD",
				  "nico_nico_nii.mp3"],
			  "nyan": [
				  "Naname nanajyuunana-do no narabi de nakunaku inanaku nanahan nanadai nannaku narabete naganagame.\nOwO",
				  "nyan.mp3"],
			  "omg": ["OH MY GOD!", "omg.mp3"],
			  "oof": ["OOF!", "oof.mp3"],
			  "pingas": ["Pingas.", "pingas.mp3"],
			  "rimshot": ["Badum, tiss", "rimshot.mp3"],
			  "roundabout": ["To be continued...", "roundabout.mp3"],
			  "sanic": ["goTtA gO faSt!", "sanic.mp3"],
			  "satania": ["BWAHAHAHA!", "sataniaLaugh.mp3"],
			  "sob": ["SON OF A BITCH!", "sob.mp3"],
			  "somebody": ["What are you doing in my swamp?!", "somebodyClipping.wav"],
			  "star destroyers" : ["**IT BROKE NEW GROUND**", "starDestroyers.mp3"],
			  "stop": ["It's time to stop!", "stop.mp3"],
			  "tea": ["I've got fucking tea, ya dickhead!", "gotTea.wav"],
			  "trash": ["**Endless trash**", "Endless Trash.mp3"],
			  "violin": ["*sadness intensifies*", "sadViolin.mp3"],
			  "wake me up": ["**I CAN'T WAKE UP**", "wakeMeUp.mp3"],
			  "winky face": [":wink:", "winkyFace.ogg"],
			  "wow": ["Wow", "wow.mp3"],
			  "yeah": ["*Puts on sunglasses*", "yeah.mp3"],
			  "yes": ["YES YES YES YES... **YES**!", "yes.mp3"],
			  "your way": ["Don't lose your waaaaaaaaay!", "dontloseyourway.mp3"],
			  "zaworldo": ["ZA WARLDO!", "za_warudo.mp3"]}
	try:
		# removes the "!say" envocation portion of the message
		content = ctx.message.content
		endCommand = content.find(" ")
		if endCommand == -1:
			message = ""
		else:
			message = content[endCommand:].strip()

		# Parsing commands
		commands = []
		i = 0;
		while i < len(message) and message[i] == "-":  # Looks for commands
			command = ""
			i += 1
			# iterates over charcters until it finds the end of the command
			while i < len(message) and message[i].isalnum():
				command = command + message[i]
				i += 1;
			commands.append(command.lower())
			i += 1
		key = message[i:].strip().lower()  # Removes commands from the message

		##------------------------------ NO AUDIO COMMANDS
		# Acting on commands
		if "help" in commands:  # provides help using this command
			title = "`!say` User Guide"
			description = ("Plays an audio clip in voice. If not already in the user's voice channel, " + 
				"the bot will automatically join the voice channel of the user issuing the command. " + 
				"The bot holds a list of stored audio files which can be summoned using predefined tags " + 
				"(the list of tags can be viewed using the `!say -ls` command). If an audio clip is currently " +
				"playing, another tag cannot be started. If all users leave the audio channel the bot " + 
				"is in, the bot will leave as well. If the user is not in a voice channel, the command " + 
				"will be rejected")
			commandDict = {
				"!say <tag>": "Plays the predetermined audio clip for that tag. Make sure your spelling is correct!",
				"!say -help": "Shows this list",
				"!say -ls": "Lists the tags for all the available audio clips",
				"!say -stop": "Stops the current voice clip"}
			await bot.say(embed=dictToEmbed(commandDict, title=title, description=description, thumbnail_url=commandThumbnails["say"]))
			return
		if "ls" in commands:
			message = "The audio clips I know are: \n"
			for quoteKey in quotes.keys():
				message += quoteKey + ", "
			await bot.say(message[:-2])
			return
		if "stop" in commands:
			if not bot.player.is_playing():
				await bot.say("I'm not saying anything...")
			else:
				bot.player.stop()
				await bot.say("Shutting up.")
			return

		##------------------------------ AUDIO INITIALIZATION
		if key == "":
			await bot.say(
				("You need to type the name of an audio clip for me to say. Type `!say -ls` for a " 
					+ "list of my audio clips or type `!say -help` for a full list of my commands"))
			return

		if key not in quotes.keys():
			await bot.say(
				"I don't see an audio clip called '" + key + "'. Type `!say -ls` for a list of my audio clips")
			return

		authorVoiceChannel = ctx.message.author.voice_channel  # Gets the voice channel the author is in
		if authorVoiceChannel is None:  # Ignores the command if the author is not in voice
			await bot.say("You are not in a voice channel right now")
			return

		if bot.is_voice_connected(ctx.message.server):
			voiceChannel = bot.voice_client_in(ctx.message.server).channel
			if voiceChannel != authorVoiceChannel:  # Ignores the command if the bot is already in the author's voice channel
				bot.player.stop()  # stops any active voice clip
				voice = bot.voice_client_in(ctx.message.server)
				await voice.move_to(authorVoiceChannel)  # Moves the bot to the new channel
		else:  # If the bot is not connected to voice
			voice = await bot.join_voice_channel(authorVoiceChannel)  # Joins the author's voice channel

		##------------------------------ PLAYING AUDIO

		if bot.player is not None and bot.player.is_playing():  # Ignores command if bot is already playing a voice clip
			await bot.say("Currently processing other voice command")
			return

		await bot.say(quotes[key][0])  # Responds with the text of the voice clip
		voice = bot.voice_client_in(ctx.message.server)  # Gets the active voice client
		player = voice.create_ffmpeg_player(
			QUOTE_FOLDER + quotes[key][1])  # Gets the voice clip and creates a ffmpeg player
		bot.player = player  # Assigns the player to the bot
		player.start()  # Plays the voice clip
	except Exception as e:
		await report(str(e), source="Say command", ctx=ctx)


@bot.command(pass_context=True, help=longHelp['leave'], brief=briefHelp['leave'], aliases=aliases['leave'])
async def leave(ctx):
	"""Makes Liberty Prime leave the voice channel."""
	if bot.is_voice_connected(ctx.message.server):
		await bot.voice_client_in(ctx.message.server).disconnect()  # Disconnect from voice
		await bot.say('I have disconnected from voice channels in this server.')
	else:  # If the bot is not connected to voice, do nothing
		await bot.say('I am not connected to any voice channel on this server.')

###### DEV
@bot.group(pass_context=True, hidden=True, )
async def dev(ctx):
	global currentlyPlaying
	try:
		if ctx.message.author.id not in AUHTORIZED_IDS:
			await bot.say("You are not authorized to use these commands")
			return

		[function, parameter] = functionParameter(ctx.message.content)

		if function in ["help", ""]:
			title = "`!dev` User Guide"
			description = "A list of features useful for "
			helpDict = {
				"channelid":"Posts the ID of the current channel",
				"flag":"Tests the `flag` function",
				"meow":"The current meow success rate",
				"playing":"Sets the presence of the bot (what the bot says it's currently playing)",
				"report":"Tests the `report` function",
				"serverid":"Posts the ID of the current channel",
				"swears":"Find out who swears the most",
				"test":"A catch-all command for inserting code into the bot to test.",
			}
			await bot.say("`!dev` User Guide", embed=dictToEmbed(helpDict, title=title, description=description))

		elif function == "channelid":
			await bot.say("Channel ID: " + ctx.message.channel.id)

		elif function == "flag":
			await bot.say("Triggering flag...")
			await flag("Test", description="This is a test of the flag ability", ctx=ctx)

		elif function == "meow":
			await bot.say(("Current `!meow` success rate:\n" + 
				str(meowSuccess) + " successes\n" +
				str(meowAttempt) + " attempts\n" +
				"For a total success rate of " + str(100*meowSuccess/meowAttempt)[:5] + "%"))

		elif function == "playing":
			try:
				currentlyPlaying = parameter
				await bot.change_presence(game=discord.Game(name=currentlyPlaying))
				cacheCurrPlaying()
				await bot.say("I'm now playing `" + parameter + "`")
			except Exception as e:
				await bot.say("Failed to change presence to `" + parameter + "`")

		elif function == "serverid":
			await bot.say("Server ID: " + ctx.message.server.id)

		elif function == "swears":
			sortedList = sorted(list(swearTally.items()), key=lambda userTally: userTally[1][2], reverse=True)
			message = ""
			for i, user in enumerate(sortedList):
				message += "**" + str(i + 1) + ".** " + users[user[0]] + " - " + str(round(user[1][2]*100, 2)) + "%\n"
			if len(message) > 0:
				await bot.say(trimToLength(message, 2000))

		elif function == "report":
			await bot.say("Triggering report...")
			await report("This is a test of the report system", source="dev report command", ctx=ctx)

		elif function == "test":
			subredditList = reddit.subreddits.search_by_name(parameter, include_nsfw=False, exact=True)
			subreddit = subredditList.pop()
			await bot.say((
				"Header: " + str(subreddit.header_img) + "\n" + 
				"Banner: " + str(subreddit.banner_img) + "\n" + 
				"Icon: " + str(subreddit.icon_img) + "\n"
			))

		else:
			await bot.say("I don't recognize the command `" + function + "`. You can type `!dev` for a list of available functions")
	except Exception as e:
		await report(str(e), source="dev command", ctx=ctx)


# -------------------- COMMAND METHODS ----------------------------------

async def listHelper(ctx, helpEmbed=None, command="list", listID=None):
	global listUserTable, listSpaces
	# LIST -------------------------------------- PRELIMINARY PROCESSES

	if failedToLoadLists is not None:
		await bot.say(
			("An error occurred while loading the lists during start up. " 
				+ "Use of this command now could cause data loss. Please contact the bot owner"))
		return

	# Retrieves message details
	authorName = getAuthorName(ctx.message)
	authorID = ctx.message.author.id

	# parse message of apostrophes
	parsedCTX = parseApos(ctx.message.content)

	# separates out the function call and its parameters
	[function, parameter] = functionParameter(parsedCTX)

	# Premptively creates a list table if author does not have one
	if authorID not in listUserTable.keys():
		listUserTable[authorID] = {}
	authorLists = listUserTable[authorID]

	# Creates a 'None' entry in the listSpaces if author is not in it
	if authorID not in listSpaces.keys():
		listSpaces[authorID] = None

	# Also sets the current list
	if listID is None:
		currList = listSpaces[authorID]
	else:
		currList = listUserTable[authorID][listID]
	# LIST -------------------------------- FUNCTIONS

	# --------------------- DISPLAY FUNCTIONS

	# updating
	if function in ["", "updating"]:
		try:
			if currList is None:
				await bot.say(
					("You are not currently in any list. Type `!" + command + " use <id>` to begin editing a list or `!" 
					+ command + " help` for more information"))
				return
			currList.updating = await bot.say(embed=currList.getEmbed())
		except Exception as e:
			await report(str(e), source="List updating command, via " + command, ctx=ctx)
		return

	# static
	if function == "static":
		try:
			if currList is None:  # If there is no currently active list, reject the command
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			await bot.say(embed=listSpaces[authorID].getEmbed())
		except Exception as e:
			await report(str(e), source="List static command, via " + command, ctx=ctx)
		return

	# --------------------- EDIT FUNCTIONS

	closedForDevWork = False
	if closedForDevWork and ctx.message.author.id not in AUHTORIZED_IDS:
		await bot.say(
			("Editing lists has been temporarily disabled because it is undergoing development." 
				+ " Attempts to use this command could fail or cause data loss"))
		return

	# add <element>
	# add [<index>] <element>
	if function in ["add", "insert"]:  # X
		try:
			if currList is None:  # If there is no currently active list, reject the command
				await bot.say(
					("You are not currently in any list. Type `!" + command + " use <id>` to begin editing a list or `!" 
						+ command + " help` for more information"))
				return
			[element, rank] = UserList.parseStringAndOptionalNum(parameter)  # Get index and element
			if rank is None:
				rank = currList.count() + 1
			currList.add(element, rank)  # Add element at index
			updateListAdd(authorID, currList.id, rank, element)
			await currList.update()
			await bot.say("I have now recognized `` " + element + " `` as the number " + str(rank) + " entry in your list")
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List add command, via " + command, ctx=ctx)
		return

	# clear
	# clear <id>
	if function == "clear":  # X
		try:
			if listID is not None:
				await bot.say("The command `clear` is only available when using '!list'")
				return
			listID = parameter.lower()
			if listID == "":  # If no ID was provided, use the currently active list
				if currList is None:  # If there is no currently active list, reject the command
					await bot.say(
						("You are not currently in any list. Type `!" + command + " use <id>` to begin editing a list or `!" 
							+ command + " help` for more information"))
					return
				listID = currList.id  # Record the ID
				currList.clear()  # clear the list
			else:  # If the user specified a listID
				if listID not in authorLists.keys():  # If there is no list with that ID, reject the command
					await bot.say(
						"You do not have a list with the ID `` " + listID + " ``. Type `!" + command + " show` to see your table of list IDs")
					return
				authorLists[listID].clear()  # clear the list
			if currList is not None:
				await currList.update()
			clearList(authorID, currList.id)
			await bot.say("Your list with ID `` " + listID + " `` has been cleared")
		except Exception as e:
			await report(str(e), source="List clear command, via " + command, ctx=ctx)
		return

	# curr
	if function in ["curr", "currlist"]:
		try:
			if listID is not None:
				await bot.say("The command `" + command + "` is only available when using '!list'")
				return
			if listSpaces[authorID] is None:  # If the user is not currently in a list
				await bot.say("You are not currently in a list")
			else:
				await bot.say("`" + listSpaces[authorID].id + "`")
		except Exception as e:
			await report(str(e), source="List curr command, via " + command, ctx=ctx)
		return

	# create <id>
	if function == "create":  # X
		try:
			if listID is not None:
				await bot.say("The command `create` is only available when using '!list'")
				return
			listID = parameter.lower()
			if listID in authorLists.keys():  # If the user already has a list with that ID, reject the command
				await bot.say(
					"You already have a list with the ID `` " + listID + " ``. To delete that list, use the `!list drop` command, " +
					"to keep the list but clear the values, use the `!list clear` command, or type `!list help` for more information")
				return
			if listID == "":  # If the user did not provide an ID, reject the command
				await bot.say("You cannot create a list with a blank ID")
				return
			authorLists[listID] = UserList(listID=listID, userName=users[authorID],
										   color=LIST_EMBED_COLOR)  # Create the list and add it to the authors list dictionary
			listSpaces[authorID] = authorLists[listID]  # Set the new list to the author's active list
			createList(authorID, listID)
			authorLists[listID].updating = await bot.say(embed=authorLists[listID].getEmbed())
			await bot.say("I have created a list with the ID `` " + listID + " `` and set it to your current list")
		except Exception as e:
			await report(str(e), source="List create command, via " + command, ctx=ctx)
		return

	# dev
	if function == "dev":
		try:
			await bot.say(str(type(currList.title)))
		except Exception as e:
			await report(str(e), source="List dev command", ctx=ctx)
		return

	# drop <id>
	if function == "drop":
		try:
			if listID is not None:
				await bot.say("The command `drop` is only available when using '!list'")
				return
			listID = parameter.lower()
			if listID == "":  # If the user did not provide a list, use the currently active list
				await bot.say("You must specify the ID of the list you wish to drop")
				return
			else:  # If the user provided an ID
				if listID not in authorLists.keys():  # If the user provided ID doesn't exist, reject the command
					await bot.say(
						"You do not have a list with the ID `` " + listID + " ``. Type `!list show` to see your table of list IDs")
					return
			if listSpaces[authorID] == authorLists[listID]:  # If that list was the active list, set the active list to none
				listSpaces[authorID] = None
			del authorLists[listID]  # Drop the list
			dropList(authorID, listID)
			if currList is not None:
				await bot.delete_message(currList.updating)
			await bot.say("Your list with ID `` " + listID + " `` has been dropped")
		except Exception as e:
			await report(str(e), source="List drop command, via " + command, ctx=ctx)
		return

	# move <index> <index>
	if function == "move":
		try:
			if currList is None:  # If there is no current list, reject the command
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			numbers = UserList.parseTwoNumbers(parameter)
			element = currList.move(numbers[0], numbers[1])
			updateListMove(authorID, currList.id, fromRank=numbers[0], toRank=numbers[1])
			await currList.update()
			await bot.say("Alright, I moved `` " + element + " `` to index " + str(numbers[1]))
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List move command, via " + command, ctx=ctx)
		return

	# multiadd <element>;<element>;<element>...
	if function == "multiadd":
		try:
			if currList is None:  # If there is no active list, reject the command
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			else:
				elementsAdded = 0
				for element in parameter.split(";"):  # Split the list at semicolons
					element = element.strip()
					if len(element) > 0:  # Add the item only if the element has text
						currList.add(element)  # Add the element
						elementsAdded += 1
						updateListAdd(authorID, currList.id, currList.count(), element)
				await currList.update()
				if elementsAdded == 1:
					await bot.say("I have added " + str(elementsAdded) + " element to your list")
				else:
					await bot.say("I have added " + str(elementsAdded) + " elements to your list")
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List multiadd command, via " + command, ctx=ctx)
		return

	# remove <index>
	if function in ["remove", "delete"]:
		try:
			if currList is None:
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			ranks = parameter.replace("[", "").replace("]", "").split(";")

			#Parse index strings to int values
			intRanks = list()
			for rank in ranks:
				try:
					parsedRank = int(rank)
					if parsedRank not in intRanks:
						intRanks.append(parsedRank)
				except ValueError as e:
					await bot.say("`" + rank + "` is not a valid index number")
					return

			# Check for out of bounds and correct ranks
			# Ranks need to be corrected since when index 4 gets removed, index 5 
			# will become index 4, so the later indices need to be shifted up one
			shiftedRanks = list()
			for rank in intRanks:
				#Check bounds
				if rank > currList.count():
					await bot.say("The index `" + str(rank) + "` exceeds the length of your list")
					return
				elif rank < 1:
					await bot.say("The index `" + str(rank) + "` is less than 1, which is not valid")
					return
				for previousRank in shiftedRanks:
					if previousRank < rank:
						rank -= 1
				shiftedRanks.append(rank)

			removedElements = list()
			for rank in shiftedRanks:
				rank = int(rank)
				removedElements.append(currList.remove(rank))
				if currList.count() > 0:
					updateListRemove(authorID, currList.id, rank)
				else:
					clearList(authorID, currList.id)

			await currList.update()
			await bot.say("I have removed `` " + " ``, `` ".join(removedElements) + " `` from your list")
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List remove command, via " + command, ctx=ctx)
		return

	# replace [<index>] <entry>
	if function in ["replace", "rename", "edit"]:
		try:
			if currList is None:
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			[element, rank] = UserList.parseStringAndOptionalNum(parameter)
			if rank is None:
				await bot.say("I don't see an index to modify. Make sure it is enclosed in [square brackets]")
				return
			oldVal = currList.replace(element, rank)
			await currList.update()
			updateListElement(authorID, currList.id, rank, element)
			await bot.say("The element `` " + oldVal + " `` has been renamed to `` " + element + " ``")
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List replace command, via " + command, ctx=ctx)
		return

	# show
	if function == "show":
		try:
			if listID is not None: #handles edge cases
				if listID == "BestGirl":
					if len(ctx.message.mentions) == 0:
						await bot.say("I don't see any mentions. Use the command `!bg help` for instructions on how to use this function")
						return
					targetID = ctx.message.mentions[0].id
					await bot.say(embed=listUserTable[targetID]["BestGirl"].getEmbed())
				return
			if len(authorLists.keys()) == 0:
				await bot.say(
					"You have no lists stored. Type `!list create <id>` to create a list a type `!list help` for more information")
				return
			message = "Your lists are:\n```"

			maxIDLength = 0
			# get longest user list ID
			for listID in authorLists.keys():
				if len(listID) > maxIDLength:
					maxIDLength = len(listID)

			for listID in authorLists.keys():
				if listID not in RESERVED_LIST_IDS:
					if listSpaces[authorID] is not None and listSpaces[authorID].id == listID:
						message += "> "
					else:
						message += "  "
					message += listID + (" " * (maxIDLength - len(listID))) + " | "
					if authorLists[listID].count() == 1:
						message += "1 element"
					else:
						message += str(authorLists[listID].count()) + " elements"
					message += "\n"
			message += "```"

			await bot.say(message)
		except Exception as e:
			await report(str(e), source="List show command, via " + command, ctx=ctx)
		return

	# swap <index> <index>
	if function == "swap":
		try:
			if currList is None:
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			numbers = UserList.parseTwoNumbers(parameter)
			elements = currList.swap(numbers[0], numbers[1])
			updateListRank(authorID, currList.id, elements[0], numbers[0])
			updateListRank(authorID, currList.id, elements[1], numbers[1])
			await currList.update()
			await bot.say("Alright, I swapped `` " + elements[0] + " `` with `` " + elements[1] + " ``")
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List swap command, via " + command, ctx=ctx)
		return

	# thumbnail <url>
	# thumnail
	# icon <url>
	if function == "thumbnail" or function == "icon":
		try:
			if currList is None:
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			if len(ctx.message.attachments) == 0:
				await currList.set_thumbnail(parameter)
			else:
				await currList.set_thumbnail(ctx.message.attachments[0]['url'])
			updateListDetails(authorID, currList.id)
			await currList.update()
			await bot.say("Congratulations, your thumbnail has been updated")
		except ValueError as e:
			await bot.say(str(e))
		except Exception as e:
			await report(str(e), source="List thumbnail command, via " + command, ctx=ctx)
		return

	# title <title>
	if function == "title":
		try:
			if currList is None:
				await bot.say(
					"You are not currently in any list. Type `!list use <id>` to begin editing a list or `!list help` for more information")
				return
			oldTitle = currList.title
			currList.title = parameter  # Set the title
			updateListDetails(authorID, currList.id)  # Save to database
			if currList is not None:
				await currList.update()
			if oldTitle == "":
				await bot.say(
				"Alright. I have set your title to `` " + parameter + " ``")
			elif parameter == "":
				await bot.say(
				"Alright. I have removed your title `` " + oldTitle + " ``")
			else:
				await bot.say(
					"Alright. I have changed the title from `` " + oldTitle + " `` to `` " + parameter + " ``")
		except Exception as e:
			await report(str(e), source="List title command, via " + command, ctx=ctx)
		return

	# use <id>
	if function == "use":
		try:
			if listID is not None:
				await bot.say("The command `use` is only available when using '!list'")
				return
			if parameter == "":  # If the user did not provide an ID to use, reject the command
				await bot.say("I need an ID of a list for you to select (e.g. `!list use listID)`")
				return
			listID = parameter.lower()
			if listID not in authorLists.keys():  # If there is no user list for the ID provided, try a global list
				await bot.say(
					"I don't see a list with the ID `` " + listID + " ``. Type `!list show` to see the table of list IDs")
				return
			listSpaces[authorID] = authorLists[listID]  # Set the list to be active
			currList = authorLists[listID]
			currList.updating = await bot.say(embed=currList.getEmbed())
			await bot.say("Alright, you are now using the list '" + listID + "'")
		except Exception as e:
			await report(str(e), source="List use command, via " + command, ctx=ctx)
		return

	# LIST -------------------------------- HELP

	# help
	if function == "help":
		try:
			if helpEmbed is not None:
				await bot.say(embed=helpEmbed)
			else:
				await report("Found no helpEmbed for " + command, source=command, ctx=ctx)
				await bot.say("I'm sorry, I don't seem to be able to find the help information for this command. The bot owner has been notified.")
		except Exception as e:
			await report(str(e), source="List help command, via " + command, ctx=ctx)
		return

	await bot.say(
		"I don't recognize the function ` " + function + " `. Type `!" + command + " help` for information on this command")


# ------------------- UPDATE CACHE MYSQL DB ----------------------------------

def cacheColton():
	ensureSQLConnection()
	cacheCommand = ("UPDATE Cache SET Value=%s WHERE ID=%s")
	cacheData = (lastColton.strftime("%s"), "lastColton")
	cursor.execute(cacheCommand, cacheData)
	cacheData = (dailyColton, "dailyColton")
	cursor.execute(cacheCommand, cacheData)
	cacheData = (totalColton, "totalColton")
	cursor.execute(cacheCommand, cacheData)
	cnx.commit()

def cacheCurrPlaying():
	ensureSQLConnection()
	cachePlayingCommand = ("UPDATE Cache SET Value=%s WHERE ID=%s")
	cachePlayingData = (currentlyPlaying, "currPlaying")
	cursor.execute(cachePlayingCommand, cachePlayingData)
	cnx.commit()

def cacheMeowURL(meowURL):
	ensureSQLConnection()
	cacheMeowCommand = ("UPDATE Cache SET Value=%s WHERE ID=%s")
	cacheMeowData = (meowURL, "meowURL")
	cursor.execute(cacheMeowCommand, cacheMeowData)
	cnx.commit()

def cacheMeowSuccessRate():
	ensureSQLConnection()
	cacheMeowCommand = ("UPDATE Cache SET Value=%s WHERE ID=%s")
	cacheMeowData = (str(meowSuccess) + "/" + str(meowAttempt), "meowFailRate")
	cursor.execute(cacheMeowCommand, cacheMeowData)
	cnx.commit()

def cacheYiffURL(yiffURL):
	ensureSQLConnection()
	cacheYiffCommand = ("UPDATE Cache SET Value=%s WHERE ID=%s")
	cacheYiffData = (yiffURL, "yiffURL")
	cursor.execute(cacheYiffCommand, cacheYiffData)
	cnx.commit()

# ------------------- UPDATE PLIST MYSQL DB ----------------------------------

# Updates the value of a preference in the plist table
def updatePList(name, data):
	ensureSQLConnection()
	updatePListCommand = ("UPDATE PList SET data=%s WHERE name=%s") 
	updatePListData = (data, name)
	cursor.execute(updatePListCommand, updatePListData)
	cnx.commit()

# Adds a preference to the plist table
def addPList(name, data):
	ensureSQLConnection()
	addPListCommand = ("INSERT INTO PList VALUES (%s, %s)")
	addPListData = (name, data)
	cursor.execute(addPListCommand, addPListData)
	cnx.commit()

# Removes a preference from the plist table
def removePList(name):
	ensureSQLConnection()
	removePListCommand = ("DELETE FROM PList WHERE Name=%s")
	removePListData = (name)
	cursor.execute(removePListCommand, removePListData)
	cnx.commit()

# ------------------- UPDATE SYNONYM MYSQL DB -------------------------------

def addSynonym(synonymType, changeTo, changeFrom):
	ensureSQLConnection()
	addCommand = ("INSERT INTO Synonyms VALUES (%s, %s, %s)")
	addData = (synonymType, changeTo, changeFrom)
	cursor.execute(addCommand, addData)
	cnx.commit()

def removeSynonym(synonymType, changeTo, changeFrom):
	ensureSQLConnection()
	deleteCommand = ("DELETE FROM Synonyms WHERE Type=%s AND ChangeTo=%s AND ChangeFrom=%s")
	deleteData = (synonymType, changeTo, changeFrom)
	cursor.execute(deleteCommand, deleteData)
	cnx.commit()

# ------------------- UPDATE SWEARS MYSQL DB -------------------------------

def addUserSwears(userID):
	ensureSQLConnection()
	addCommand = ("INSERT INTO Swears VALUES (%s, %s, %s)")
	addData = (userID, 0, 0)
	cursor.execute(addCommand, addData)
	cnx.commit()

def updateUserSwears(userID):
	ensureSQLConnection()
	addCommand = ("UPDATE Swears SET Words=%s, Swears=%s WHERE ID=%s")
	addData = (swearTally[userID][0], swearTally[userID][1], userID)
	cursor.execute(addCommand, addData)
	cnx.commit()

# -------------------- UPDATE USER MYSQL DB ----------------------------------

def addUser(userID, userName):
	ensureSQLConnection()
	addUserCommand = ("INSERT INTO Users VALUES (%s, %s)")
	addUserData = (userID, userName)
	cursor.execute(addUserCommand, addUserData)
	cnx.commit()
	users[userID] = userName
	listUserTable[userID] = {"BestGirl": UserList(listID="BestGirl", userName=userName, color=BEST_GIRL_EMBED_COLOR)}
	createList(userID, "BestGirl")
	tags["user"][userID] = {}


# -------------------- UPDATE TAGS MYSQL DB ----------------------------------

def updateTagRemove(tagKey, userID, domain):
	ensureSQLConnection()
	removeCommand = ("DELETE FROM Tags WHERE Owner=%s AND KeyString=%s AND Domain=%s")
	removeData = (userID, tagKey, domain)
	cursor.execute(removeCommand, removeData)
	cnx.commit()


def updateTagAdd(tagKey, tagValue, userID, domain):
	ensureSQLConnection()
	addCommand = ("INSERT INTO Tags VALUES (%s, %s, %s, %s)")
	addData = (userID, tagKey, tagValue, domain)
	cursor.execute(addCommand, addData)
	cnx.commit()


def updateTagEdit(tagKey, tagValue, userID, domain):
	ensureSQLConnection()
	editCommand = ("UPDATE Tags SET ValueString=%s WHERE KeyString=%s and Owner=%s and Domain=%s")
	editData = (tagValue, tagKey, userID, domain)
	cursor.execute(editCommand, editData)
	cnx.commit()


# ------------------ UPDATE LIST MYSQL DB -------------------------------

# Updates the title of the given user's list
def updateListDetails(userID, listID):
	ensureSQLConnection()
	updateQuery = "UPDATE ListDetails SET Title=%s, ThumbnailURL=%s WHERE USER=%s AND ID=%s"
	updateData = (listUserTable[userID][listID].title, listUserTable[userID][listID].thumbnail_url, userID, listID)
	cursor.execute(updateQuery, updateData)
	cnx.commit()


# Shifts the rank of a block of elements
def updateListShift(userID, listID, shift=0, fromRank=0, toRank=-1):
	ensureSQLConnection()
	# If no toRank provided, assume the end of the list
	if toRank < 0:
		toRank = listUserTable[userID][listID].count()
	# Creates the range to iterate over
	rankRange = range(fromRank - 1, toRank)
	# Ranks must be shifted in the opposite order if they're shifting in the opposite direction
	if shift > 0:
		rankRange = reversed(rankRange)
	# Shift ranks
	for index in rankRange:
		shiftCommand = ("UPDATE Lists SET ListIndex=%s WHERE User=%s AND ID=%s AND ListIndex=%s")
		shiftData = (index + shift, userID, listID, index)
		cursor.execute(shiftCommand, shiftData)
	# Commit shift
	cnx.commit()


# Adds an element to the list and updates other indices
def updateListAdd(userID, listID, rank, element):
	ensureSQLConnection()
	# Shift down the existing elements below the item to be inserted
	updateListShift(userID, listID, shift=1, fromRank=rank)
	# Add the new data
	addCommand = ("INSERT INTO Lists VALUES (%s, %s, %s, %s)")
	addData = (userID, listID, rank - 1, element)
	cursor.execute(addCommand, addData)
	# Commit change
	cnx.commit()


# Removes an element from the list and updates remaining indices
def updateListRemove(userID, listID, rank):
	ensureSQLConnection()
	# Remove the entry
	removeCommand = ("DELETE FROM Lists WHERE User=%s AND ID=%s AND ListIndex=%s")
	removeData = (userID, listID, rank - 1)
	cursor.execute(removeCommand, removeData)
	# Shift up the remaining elements below the removed item
	updateListShift(userID, listID, shift=-1, fromRank=rank, toRank=listUserTable[userID][listID].count() + 1)
	# Commit the change
	cnx.commit()


# Moves an element from one rank to another and shifts the elements in between
def updateListMove(userID, listID, fromRank, toRank):
	ensureSQLConnection()
	# Get the element
	element = listUserTable[userID][listID].contents[toRank - 1]
	# Remove the element
	removeCommand = ("DELETE FROM Lists WHERE User=%s AND ID=%s AND ListIndex=%s")
	removeData = (userID, listID, fromRank - 1)
	cursor.execute(removeCommand, removeData)
	# Shift the elements in between
	if fromRank > toRank:
		updateListShift(userID, listID, shift=1, fromRank=toRank, toRank=fromRank)
	else:
		updateListShift(userID, listID, shift=-1, fromRank=fromRank, toRank=toRank)
	# Add the element back in
	addCommand = ("INSERT INTO Lists VALUES (%s, %s, %s, %s)")
	addData = (userID, listID, toRank - 1, element)
	cursor.execute(addCommand, addData)
	cnx.commit()


# Updates the contents of a particular rank
def updateListElement(userID, listID, rank, element):
	ensureSQLConnection()
	updateCommand = ("UPDATE Lists SET Element=%s WHERE User=%s AND ID=%s AND ListIndex=%s")
	updateData = (element, userID, listID, rank - 1)
	cursor.execute(updateCommand, updateData)
	cnx.commit()


# Updates the element at a particular rank
def updateListRank(userID, listID, element, rank):
	ensureSQLConnection()
	updateCommand = ("UPDATE Lists SET ListIndex=%s WHERE User=%s AND ID=%s AND Element=%s ")
	updateData = (rank - 1, userID, listID, element)
	cursor.execute(updateCommand, updateData)
	cnx.commit()


# Clears a user's list
def createList(userID, listID):
	createCommand = ("INSERT INTO ListDetails VALUES (%s, %s, %s, %s)")
	createData = (userID, listID, None, None)
	cursor.execute(createCommand, createData)
	cnx.commit()


# Clears a user's list
def clearList(userID, listID):
	deleteCommand = ("DELETE FROM Lists WHERE User=%s AND ID=%s")
	deleteData = (userID, listID)
	cursor.execute(deleteCommand, deleteData)
	cnx.commit()


# Clears a user's list
def dropList(userID, listID):
	deleteCommand = ("DELETE FROM Lists WHERE User=%s AND ID=%s")
	deleteData = (userID, listID)
	cursor.execute(deleteCommand, deleteData)
	deleteCommand = ("DELETE FROM ListDetails WHERE User=%s AND ID=%s")
	deleteData = (userID, listID)
	cursor.execute(deleteCommand, deleteData)
	cnx.commit()


# --------------------- LOADING ----------------------------------

def load():
	loadUsers()
	loadTags()
	loadLists()
	loadSynonyms()
	loadCache()
	loadSwears()
	loadPList()

# -------------Load tags (MySQL)
def loadUsers():
	global listUserTable, failedToLoadUsers
	try:
		query = ("SELECT * FROM Users")
		cursor.execute(query)
		for (ID, Name) in cursor:
			users[ID] = Name
			listUserTable[ID] = {}
			listUserTable[ID]["BestGirl"] = UserList(listID="BestGirl", userName=Name, color=BEST_GIRL_EMBED_COLOR)
	except Exception as e:
		failedToLoadUsers = e


# -------------Load tags (MySQL)
def loadTags():
	global tags, failedToLoadTags
	try:
		query = ("SELECT * FROM Tags")
		cursor.execute(query)
		for (Owner, KeyString, ValueString, Domain) in cursor:
			KeyString = KeyString.decode("utf-8")
			ValueString = ValueString.decode("utf-8")
			if Domain == "global":
				tags["global"][KeyString] = ValueString
			else:
				if Owner not in tags[Domain].keys():
					tags[Domain][Owner] = {}
				tags[Domain][Owner][KeyString] = ValueString
	except Exception as e:
		failedToLoadTags = e


# -------------Load general lists
def loadLists():
	global listUserTable, failedToLoadLists
	try:
		selectQuery = ("SELECT * FROM ListDetails")
		cursor.execute(selectQuery)
		for (User, ID, Title, ThumbnailURL) in cursor:
			ID = ID.decode("utf-8")
			if Title is not None:
				Title = Title.decode("utf-8")
			else:
				Title = None
			if ThumbnailURL is not None:
				ThumbnailURL = ThumbnailURL.decode("utf-8")
			else:
				ThumbnailURL = None
			listUserTable[User][ID] = UserList(listID=ID, userName=users[User], color=LIST_EMBED_COLOR,
					thumbnail_url=ThumbnailURL, title=Title)
			if ID == "BestGirl":
				listUserTable[User][ID].color = BEST_GIRL_EMBED_COLOR

		selectQuery = ("SELECT * FROM Lists")
		cursor.execute(selectQuery)
		for (User, ID, ListIndex, Element) in cursor:
			ID = ID.decode("utf-8")
			Element = Element.decode("utf-8")
			if User not in listUserTable.keys():
				raise AttributeError("User `" + User + "` not found in listUserTable.keys()")
			if ID not in listUserTable[User].keys():
				raise AttributeError(
					"Found element `" + Element + "` with ID `" + ID + "` for user `" + User + "` with no corresponding list")
			userList = listUserTable[User][ID]
			userList.buffer(Element, ListIndex)
		for userLists in listUserTable.values():
			for userList in userLists.values():
				userList.commit()

	except Exception as e:
		failedToLoadLists = e

def loadSynonyms():
	global titleSynonyms, characterSynonyms
	query = ("SELECT * FROM Synonyms")
	cursor.execute(query)
	for (Type, ChangeTo, ChangeFrom) in cursor:
		ChangeFrom = ChangeFrom.decode("utf-8")
		ChangeTo = ChangeTo.decode("utf-8")
		if Type == "ANIME":
			if ChangeTo not in titleSynonyms.keys():
				titleSynonyms[ChangeTo] = list()
			titleSynonyms[ChangeTo].append(ChangeFrom)
		elif Type == "CHARACTER":
			if ChangeTo not in characterSynonyms.keys():
				characterSynonyms[ChangeTo] = list()
			characterSynonyms[ChangeTo].append(ChangeFrom)
		
def loadCache():
	global failedToLoadCache, currentlyPlaying, nextYiffURL, nextMeowURL, meowSuccess, meowAttempt, lastColton, dailyColton, totalColton
	try:
		query = ("SELECT * FROM Cache")
		cursor.execute(query)
		for (ID, Value) in cursor:
			Value = Value.decode("utf-8")
			if ID == "currPlaying":
				currentlyPlaying = Value
			elif ID == "meowFailRate":
				[meowSuccess, meowAttempt] = Value.split("/")
				meowSuccess = int(meowSuccess)
				meowAttempt = int(meowAttempt)
			elif ID == "meowURL":
				nextMeowURL = Value
			elif ID == "yiffURL":
				nextYiffURL = Value
			elif ID == "lastColton":
				lastColton = datetime.utcfromtimestamp(int(Value))
			elif ID == "dailyColton":
				dailyColton = int(Value)
			elif ID == "totalColton":
				totalColton = int(Value)
	except Exception as e:
		failedToLoadCache = e

def loadSwears():
	global failedToLoadSwears, swearTally
	try:
		query = ("SELECT * FROM Swears")
		cursor.execute(query)
		for (ID, Words, Swears) in cursor:
			swearTally[ID] = [Words, Swears, Swears / float(Words)]
	except Exception as e:
		failedToLoadCache = e

def loadPList():
	global failedToLoadPList, plist
	try:
		query = ("SELECT * FROM PList")
		cursor.execute(query)
		for (Name, Data) in cursor:
			plist[Name] = Data.decode("utf-8")
	except Exception as e:
		failedToLoadPList = e


# -----------------------   TERMINATION   -----------------------------------

# load oauth credentials
tokenFile = open(AUTH_FILE_PATH, "r", encoding="utf-8")
[CLIENT_ID, CLIENT_SECRET, BOT_TOKEN, MYSQL_USER, MYSQL_PASSWORD, 
WOLFRAMALPHA_APPID, JDOODLE_ID, JDOODLE_SECRET, REDDIT_ID, REDDIT_SECRET,
YOUTUBE_KEY] = tokenFile.read().splitlines()

# Create MySQL connection
cnx = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, database='suitsBot')
cursor = cnx.cursor(buffered=True)

bot.run(BOT_TOKEN)
