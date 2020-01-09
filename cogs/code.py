from discord.ext import commands
from discord import Embed
from constants import *
import credentials
import parse
import utils


class Code:
    """
    Arbitrary code execution

    Uses the JDOODLE web service to execute code and print its output. Supports 65 languages.
    Users enter code using Discord's multiline markdown formatting and provide the language tag
    they wish to compile against. That format is three backticks, the language tag, a return,
    then the code, closing it out with three more backticks. The first line should contain zero
    whitespace characters. The language tag is case-insensitive.

    Ex:
    ```swift
    print("I wish I could write this bot in Swift")
    ```
    """

    def __init__(self, bot):
        self.bot = bot
        self.langs = {
            "c": ["C (GCC 8.1.0)", "c", 3],
            "clisp": ["CLISP (GNU CLISP 2.49.93 - GNU 8.1.0)", "clisp", 2],
            "cpp": ["C++ (GCC 8.1.0)", "cpp", 3],
            "cpp14": ["C++ 14 (GCC 8.1.0)", "cpp14", 2],
            "csharp": ["C# (mono 5.10.1)", "csharp", 2],
            "haskell": ["Haskell (ghc 8.2.2)", "haskell", 2],
            "java": ["Java 11.0.4", "java", 3],
            "kotlin": ["Kotlin 1.3.50 (JRE 11.0.4)", "kotlin", 2],
            "lua": ["Lua 5.3.4", "lua", 1],
            "nodejs": ["NodeJS 12.11.1", "nodejs", 3],
            "pascal": ["Pascal (fpc-3.0.4)", "pascal", 2],
            "perl": ["Perl 5.26.2", "perl", 2],
            "php": ["PHP 7.2.5", "php", 2],
            "python2": ["Python 2.7.15", "python2", 1],
            "python": ["Python 3.7.4", "python3", 3],
            "go": ["GO Lang 1.10.2", "go", 2],
            "scala": ["Scala 2.12.5", "scala", 3],
            "scheme": ["Scheme (Gauche 0.9.4)", "scheme", 1],
            "sql": ["SQLite 3.23.1", "sql", 2],
            "swift": ["Swift 5.1", "swift", 3],
            "r": ["R Language 3.5.0", "r", 0],
            "ruby": ["Ruby 2.6.5", "ruby", 3],
            "rust": ["RUST 1.25.0", "rust", 2]
        }

        self.esolangs = {
            "ada": ["Ada (GNATMAKE 8.1.0)", "ada", 2],
            "gccasm": ["Assembler - GCC (GCC 8.1.0)", "gccasm", 1],
            "nasm": ["Assembler - NASM 2.13.03", "nasm", 2],
            "bash": ["Bash shell 4.4.19", "bash", 2],
            "bc": ["BC 1.07.1", "", 1],
            "brainfuck": ["Brainfuck (bfc-0.1)", "brainfuck", 0],
            "c99": ["C-99 (GCC 8.1.0)", "c99", 2],
            "clojure": ["Clojure 1.9.0", "clojure", 1],
            "cobol": ["COBOL (GNU COBOL 2.2.0)", "cobol", 1],
            "coffeescript": ["CoffeeScript 2.3.0", "coffeescript", 2],
            "d": ["D (DMD64 D Compiler v2.071.1)", "d", 0],
            "dart": ["Dart 1.24.3", "dart", 2],
            "elixir": ["Elixir 1.6.4", "elixir", 2],
            "fsharp": ["F# 4.1", "fsharp", 0],
            "factor": ["Factor 8.29", "factor", 2],
            "falcon": ["Falcon 0.9.6.8 (Chimera)", "falcon", 0],
            "fantom": ["Fantom 1.0.69", "fantom", 0],
            "forth": ["Forth (gforth 0.7.3)", "forth", 0],
            "fortran": ["Fortran (GNU 8.1.0)", "fortran", 2],
            "freebasic": ["FREE BASIC 1.05.0", "freebasic", 1],
            "groovy": ["Groovy 2.4.15 (JVM 10.0.1)", "", 2],
            "hack": ["Hack (HipHop VM 3.13.0)", "hack", 0],
            "icon": ["Icon 9.4.3", "icon", 0],
            "intercal": ["Intercal 0.30", "intercal", 0],
            "lolcode": ["LOLCODE 0.10.5", "lolcode", 0],
            "nemerle": ["Nemerle 1.2.0.507", "nemerle", 0],
            "nim": ["Nim 0.18.0", "nim", 2],
            "objc": ["Objective C (GCC 8.1.0)", "", 2],
            "ocaml": ["Ocaml 4.03.0", "ocaml", 0],
            "octave": ["Octave (GNU 4.4.0)", "octave", 2],
            "mozart": ["OZ Mozart 2.0.0 (OZ 3)", "", 0],
            "picolisp": ["Picolisp 18.5.11", "picolisp", 2],
            "pike": ["Pike v8.0", "pike", 0],
            "prolog": ["Prolog (GNU Prolog 1.4.4)", "prolog", 0],
            "smalltalk": ["SmallTalk (GNU SmallTalk 3.2.92)", "smalltalk", 0],
            # "spidermonkey":["SpiderMonkey 45.0.2", "spidermonkey", 1],
            "racket": ["Racket 6.12", "racket", 1],
            "rhino": ["Rhino JS 1.7.7.1", "rhino", 0],
            "tcl": ["TCL 8.6.8", "tcl", 2],
            "unlambda": ["Unlambda 0.1.3", "unlambda", 0],
            "vbn": ["VB.Net (mono 5.10.1)", "vbn", 2],
            "verilog": ["VERILOG 10.2", "verilog", 2],
            "whitespace": ["Whitespace 0.3", "whitespace", 0],
            # "yabasic":["YaBasic 2.769", "yabasic", 0], #TAKEN OUT SO THE LANG LIST DOESN'T EXCEED MESSAGE CHAR LIMIT
        }

        self.credits_check_url = "https://api.jdoodle.com/v1/credit-spent"
        self.execute_url = "https://api.jdoodle.com/v1/execute"
        self.JDOODLE_ID = credentials.tokens["JDOODLE_ID"]
        self.JDOODLE_SECRET = credentials.tokens["JDOODLE_SECRET"]

    # Arbitrary code execution
    @commands.command(pass_context=True, help=LONG_HELP['code'], brief=BRIEF_HELP['code'], aliases=ALIASES['code'])
    async def code(self, ctx):
        """
        code command

        Parameters
        ------------
        ctx : discord.context
            The message context object
        """
        try:
            (arguments, message) = parse.args(ctx.message.content)

            # Explain all the arguments to the user
            if "help" in arguments or (len(message) == 0 and len(arguments) == 0):
                title = "!code - User Guide"
                description = ("Remote code execution. Allows users to write code and submit it to the bot for " +
                               "remote execution, after which the bot prints out the results, any error codes, " +
                               "the execution time, and memory consumption. The command supports 65 different " +
                               "languages, including Java, Python 2/3, PHP, Swift, C++, Rust, and Go.\n\nTo invoke " +
                               "execution, include a block of code using the multi-line Discord code format " +
                               "( https://support.discordapp.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-" +
                               "Formatting-Bold-Italic-Underline- ). To use this formatting, use three backticks " +
                               "(`, the key above the tab key), followed immediately (no spaces!) by the language " +
                               "tag, followed by a linebreak, followed by your code. Close off the code block with " +
                               "three more backticks. It's a little complicated, I apologize. It's Discord's " +
                               "formatting rules, not mine.\n\n**Be advised**\nRemote execution will time out after " +
                               "5 seconds and does not support external libraries or access to the internet.")

                helpdict = {"-help": "Shows this user guide",
                            "-full": "Shows the full list of supported languages",
                            "-lang": "Shows the common languages supported by this command",
                            }
                await self.bot.say(embed=utils.embedfromdict(helpdict,
                                                             title=title,
                                                             description=description,
                                                             thumbnail_url=COMMAND_THUMBNAILS["code"]))
                return

            if "ls" in arguments or "full" in arguments:
                message = "`Name` (`compiler version`) - `tag`\n---------"
                for langname in self.langs.keys():
                    name = self.langs[langname][0]  # Name
                    message += "\n**" + name + "** : " + langname
                if "full" in arguments:
                    message += "\n---------"
                    for langname in self.esolangs.keys():
                        name = self.esolangs[langname][0]  # Name
                        message += "\n**" + name + "** : " + langname
                await self.bot.say(utils.trimtolength(message, 2000))
                return

            if "dev" in arguments:
                [json, resp_code] = await utils.get_json_with_post(url=self.credits_check_url, json={
                    "clientId": self.JDOODLE_ID,
                    "clientSecret": self.JDOODLE_SECRET})
                if resp_code != 200:
                    await utils.report(self.bot, "Failed to check credits\n" + str(json), source="!code dev", ctx=ctx)
                    return
                if "used" not in json.keys():
                    await utils.report(self.bot, json, "Failed to get credit count for JDOODLE account", ctx=ctx)
                    await self.bot.say("Forces external to your request have caused this command to fail.")
                    return
                await self.bot.say(json['used'])
                return

            if "```" in message:
                trimmedmessage = message[message.find("```") + 3:]
                if "```" not in trimmedmessage:
                    await self.bot.say("You didn't close your triple backticks")
                    return
                trimmedmessage = trimmedmessage[:trimmedmessage.find("```")]
                splitmessage = trimmedmessage.split("\n", maxsplit=1)
                if len(trimmedmessage) == 0:
                    await self.bot.say("You need to put code inside the backticks")
                    return
                if trimmedmessage[0] not in [" ", "\n"] and len(splitmessage) > 1:
                    [language, script] = splitmessage
                    language = language.strip()
                    for key in self.esolangs.keys():
                        self.langs[key] = self.esolangs[key]
                    if language.lower() in self.langs.keys():
                        response = await utils.get_json_with_post(url=self.execute_url, json={
                            "clientId": self.JDOODLE_ID,
                            "clientSecret": self.JDOODLE_SECRET,
                            "script": script,
                            "language": self.langs[language.lower()][1],
                            "versionIndex": self.langs[language.lower()][2]
                        })
                        [json, resp_code] = response
                        if resp_code == 429:
                            await utils.report(self.bot,
                                               json,
                                               "Bot has reached its JDOODLE execution limit",
                                               ctx=ctx)
                            await self.bot.say("The bot has reached its code execution limit for the day.")
                            return
                        output_embed = Embed()
                        if "error" in json.keys():
                            output_embed.description = json['error']
                            output_embed.title = "ERROR"
                            output_embed.colour = EMBED_COLORS["error"]
                            await self.bot.say(embed=output_embed)
                            return
                        output_embed.title = "Output"
                        output_embed.colour = EMBED_COLORS["code"]
                        output_embed.add_field(name="Language", value=self.langs[language.lower()][0])
                        output_embed.add_field(name="CPU Time", value=str(json['cpuTime']) + " seconds")
                        output_embed.add_field(name="Memory Usage", value=json['memory'])
                        if len(json['output']) > 2046:
                            output_embed.description = "``` " + utils.trimtolength(json['output'], 2040) + "```"
                        else:
                            output_embed.description = "``` " + json['output'] + "```"
                        await self.bot.say(embed=output_embed)
                    else:
                        await self.bot.say("I don't know the language '" + language + "'. Type `!code -full` " +
                                           "to see the list of languages I support, or type `!code -ls` to see " +
                                           "the most popular ones")
                else:
                    await self.bot.say("There was no language tag. Remember to include the language tag " +
                                       "immediately after the opening backticks. Type `!code -ls` or " +
                                       "`!code -full` to find your language's tag")
            else:
                await self.bot.say("I don't see any code")
        except Exception as e:
            await utils.report(self.bot, str(e), source="!code command", ctx=ctx)


def setup(bot):
    bot.add_cog(Code(bot))
