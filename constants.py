"""
List of constants necessary for the bot's operation
"""

# List of responses in the affirmative
AFFIRMATIVE_RESPONSES = ['yes', 'yup', 'y', 'okay', 'ok', 'go ahead', 'affirmative', 'the affirmative',
                         'in the affirmative', 'roger', 'ja', 'si', 'go', 'do it']

# Command aliases
ALIASES = {
    "anime": ["ani", "Anime", "animu", "aniem", "anilist", "AniList"],
    "aes": ["AES"],
    "bestgirl": ["bestGirls", "bestGirl", "bestgirls", "bestGrils", "bestgril", "bestgrils", "bestGril", "bg", "BG"],
    "code": ["Code", "program", "exe", "swift", "python", "java", "cpp", "brainfuck", "golang", "ide", "IDE", "cobol",
             "pascal", "fortran", "vbn", "scala", "bash", "php", "perl", "cpp14", "c", "csharp", "lua", "rust"],
    "gritty": ["grity", "grittmeister", "grittster", "god", "orange", "philly", "philadelphia", "eattherich", "Gritty"],
    "hello": ["hi", "hey"],
    "join": ["jion", "joni"],
    "leave": ["shut up", "fuckOff", "gtfo", "GTFO"],
    "ls": ["list", "lsit", "l", "lists"],
    "meco": ["MECO", "Meco", "MainEngineCutOff", "podcast"],
    "meow": ["cat", "moew", "mewo", "nyaa", "nyan"],
    "nasa": ["NASA", "APOTD", "APOD", "apod", "apotd"],
    "on": ["offnominal", "OffNominal", "Off-nominal", "Off-Nominal", "ON", "OFFNOMINAL", "OFF_NOMINAL", "OFF-NOMINAL"],
    "picture": ["snek", "Snek", "sneks", "Sneks", "snake", "snakes", "pic", "photo", "unsplash", "Unsplash"],
    "rand": ["random", "ran", "randmo"],
    "say": ["voice", "speak"],
    "tag": ["tags", "Tag", "Tags"],
    "ud": ["urbanDictionary", "urbandict", "urbanDict", "UD", "uD", "Ud"],
    "wm": ["WM", "wemartians", "WeMartians", "We-martians", "Wemartians"],
    "wiki": ["wikipedia", "Wikipedia", "Wiki", "WIKI"],
    "wolf": ["wolfram", "wA", "Wolfram", "WolframAlpha", "wolframAlpha", "woflram", "wofl"],
    "woof": ["dog", "doggo", "wof", "woofer", "wouef"],
    "youtube": ["yt", "YT", "YouTube", "youTube", "Youtube", "ytube", "yuotube", "youube", "youbue"]}

# User IDs authorized to perform dev commands
AUTHORIZED_IDS = [
    '187086824588443648'  # IWant2Die
]

# Bot description
BOT_DESCRIPTION = """SuitsBot v4.4.3
Discord bot deployed to practice webAPI implementation and learn Python.
Supports a variety of different functions including
- Call-and-response user tags
- Searching Wikipedia and AniList.co
- Creating and managing lists
- Playing audio clips in voice chat

More information at: https://github.com/DWCamp/SuitsBot/wiki
"""

# Command brief help text
BRIEF_HELP = {
    "anime": "Provides information about anime",
    "aes": "A command for making text 'A E S T H E T I C'",
    "bestgirl": "Best girl list manager",
    "code": "Arbitrary code execution",
    "gritty": "The bot graces your server with an image of His Royal Orangeness",
    "hello": "The bot says hi to you",
    "join": "Join a user in voice",
    "leave": "leave voice",
    "ls": "Arbitrary list creation",
    "meco": "Posts the URL to the MECO podcast episode with the number provided",
    "meow": "Cat.",
    "nasa": "A stunning astonomy picture",
    "on": "Posts the URL to the Off-Nominal podcast episode with the number provided",
    "picture": "Get a random picture of something",
    "rand": "Generate a random result",
    "say": "Have the bot say dumb things in voice",
    "tag": "Have the bot repeat a message when given a key phrase",
    "ud": "Searches Urban Dictionary for a term",
    "wiki": "Ask Wikipedia about a subject",
    "wm": "Posts the URL to the We Martians podcast episode with the number provided",
    "wolf": "Ask WolframAlpha a question",
    "woof": "Woof.",
    "youtube": "Searches YouTube"}

# URL for command help embed thumbnails
COMMAND_THUMBNAILS = {
    "anime": "https://anilist.co/img/icons/logo_full.png",
    "code": "https://cdn.discordapp.com/attachments/341428321109671939/460671554653650964/codeIcon.png",
    "bestgirl": "https://media1.tenor.com/images/19461e616447d8b63251f41f7abc461a/tenor.gif?itemid=6112845",
    "ls": ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/WikiProject_Council_project_list_icon.svg/" +
           "2000px-WikiProject_Council_project_list_icon.svg.png"),
    "rand": "https://aruzegaming.com/wp-content/uploads/2016/04/Red-Dice-Wild_CHARACTER.png",
    "tag": "https://cdn2.iconfinder.com/data/icons/marketing-strategy/512/Loud_Speaker-512.png",
    "say": "https://cdn.discordapp.com/attachments/341428321109671939/487265313071824926/sayIcon.png",
    "wiki": "https://www.wikipedia.org/portal/wikipedia.org/assets/img/Wikipedia-logo-v2@2x.png"}

# Embed color hexcodes
EMBED_COLORS = {"default": 0x4E2368,
                "amazon": 0xF49706,
                "anime": 0x1A9AFC,
                "bestgirl": 0x76BB01,
                "code": 0x00EE36,
                "error": 0xAA0000,
                "flag": 0xFCEF15,
                "gritty": 0xF74902,
                "list": 0x00C8C8,
                "meow": 0xFCBE41,
                "nasa": 0xEE293D,
                "newegg": 0x012D6B,
                "picture": 0x95AF4D,
                "reddit": 0xFF5700,
                "twitter": 0x1D9DED,
                "ud": 0x1D2439,
                "wiki": 0xFFFFFF,
                "woof": 0x9E7132,
                "yiff": 0xD4EFFF,
                "youtube": 0xFF0000}

# Headers for web requests
HEADERS = {'User-Agent': 'suitsBot Discord Bot - https://github.com/DWCamp',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Language': 'en-us'}

# Full help text for commands
LONG_HELP = {
    "anime": "Things I guess",
    "aes": ("A command for spiting out vaporwave text. Just type the command and then a string of characters and it " +
            "will print them out in the A E S T H E T I C way. Because this command involves printing one string " +
            "across multiple lines, it won't accept any input longer than 20 characters (including the command). " +
            "This also means that custom emotes and user mentions are off-limits, since the string representation of " +
            "those features is much longer than Discord will have you believe."),
    "bestgirl": ("A command for each user to manage their own best girl list. Type `!bestGirl help` for a list of " +
                 "the commands you can use. An example is `!bestGirl add [<index>] <girl>`, which when used would " +
                 "look like `!bestGirl add [1] Ryuko Matoi`"),
    "code": ("Executes code typed in code formatted blocks (code enclosed in triple backticks ```like this```). " +
             "Supports 67 different languages. Type `!code -help` for more information"),
    "gritty": "Prepare yourself for his mighty orangeness. The one Wikipedia describes as a 'Large, furry, orange " +
              "creature in Flyers regalia', he who's own team marketing director said 'doesn't know his right from " +
              "his left'. Eater of the rich. Wrecker of stadium back rooms. Menace to refs and rink staff. He " +
              "takes no quarter. He shows no mercy. He will smile at your funeral. Gritizens, put your hands " +
              "together for the one, the only...\n\n**GRITTY**",
    "hello": "A simple greeting! Say hi to the bot and she will say hi back!",
    "join": "Make the bot join a user in voice",
    "leave": "Makes the bot leave voice chat",
    "ls": ("A command for each user to create arbitrary lists of different things. Functions like MySQL, where the " +
           "user possesses multiple tables of data which the user can edit by going into and performing edit " +
           "commands similar to those found in the `!bestGirl` command. Type `!list help` for a full list of the " +
           "commands you can use and how they work."),
    "meco": "Give it a positive integer and it will give you the link to that MECO episode",
    "meow": "Cat.",
    "nasa": ("Provides an HD image of an astronomical nature. This image is provided by NASA's Astronomy Picture Of " + 
             "the Day API and changes every midnight EST. As it is provided by a third party API, this bot assumes " + 
             "no liability for the contents of the image or text. But it's NASA, so you're probably fine."),
    "on": "Give it a positive integer and it will give you the link to that Off-Nominal episode",
    "picture": ("Returns a random image of the subject requested. If no subject is provided, the search defaults to " +
                "a cute snek. Be aware that the search is *very* lose, so the image you receive may have seemingly " +
                "nothing to do with your search term.\n\nWARNING\nThis command is rate limited, so try not to spam " +
                "it too much"),
    "rand": ("Uses a random number generator to answer questions of dice rolls, coin flips, or what to do for " +
             "dinner. An example is `!rand item A, B, C...`, where it will return a randomly selected member of a " +
             "comma separated list. Type `!random help` for the complete user guide."),
    "say": ("Says one of the prerecorded voice clips in chat. For a list of the available clips, type `!say -ls`. " + 
            "The bot must be a member of your current voice channel for this command to work. To bring the bot to " + 
            "your voice channel, use the command `!join`"),
    "tag": ("Simple call and response. After you save a tag with the command `!tag [<key>] <value>`, you can then " + 
            "use the command `!tag <key>` to make the bot respond with `<value>`. Useful for common links, large " + 
            "meme texts, or images. Since each key can only have one value, users also have a personal group of " + 
            "key-value pairs that can be set or accessed with the command `!tag -u`. For the complete user guide, " + 
            "type `!tag -help`"),
    "ud": "Searches Urban Dictionary for a search term",
    "wiki": ("Queries Wikipedia for information about the requested subject. Returns a simple description as well as " + 
             "a longer form excerpt from the article."),
    "wm": "Give it a positive integer and it will give you the link to that We Martians episode",
    "wolf": ("Use this command to ask the bot simple WolframAlpha questions. Type `!wolf` and followed by your " + 
             "question and the bot will return the WolframAlpha response"),
    "woof": "Woof.",
    "youtube": "Searches YouTube for the video title provided and provides a link to the first search result"}

# Server Command Prefixes
PREFIXES = {
    "352255498697048082": "%",
    "630095143088816147": "?"
}

# List of reserved list ids
RESERVED_LIST_IDS = ["BestGirl"]

# Redis Settings
REDIS_PREFIX = "suitsBot-"                              # Prefix for all keys
RECENTLY_UNFURLED_TIMEOUT_SECONDS = 300                 # How long to wait before unfurling the same thing again
UNFURLED_CLEANUP_TRACKING_IN_SECONDS = 60 * 60 * 24     # How long to track messages to cleanup unfurls

# Emoji so users can let us know if an embed needs to be deleted
DELETE_EMOJI = "❌"
DELETE_EMOJI_COUNT_TO_DELETE = 5
