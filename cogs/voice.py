from discord.ext import commands
from constants import *
import parse
import utils


class VoiceCommands:
    """
    A series of voice chat commands for the bot

    join
      Causes the bot to join the user in voice

    say
      Says an audio clip in chat based on a tag system

    leave
      Kicks SuitsBot from its current audio channel
    """

    def __init__(self, bot):
        self.bot = bot
        self.quote_folder = "/home/dwcamp/PythonScripts/Sounds/"

    @commands.command(pass_context=True, help=LONG_HELP['join'], brief=BRIEF_HELP['join'], aliases=ALIASES['join'])
    async def join(self, ctx):
        """ Makes SuitsBot join the voice channel """

        # Gets the voice channel the author is in
        author_voice_channel = ctx.message.author.voice_channel
        # Ignores the command if the author is not in voice
        if author_voice_channel is None:
            await self.bot.say("You are not in a voice channel right now")
            return
        voice = await self.join_audio_channel(author_voice_channel)
        await self.bot.say("Joining voice channel...")
        player = voice.create_ffmpeg_player(self.quote_folder + 'hello_there_obi.mp3')  # Creates an ffmpeg player
        self.bot.player = player
        # Plays joining voice clip
        player.start()

    @commands.command(pass_context=True, help=LONG_HELP['say'], brief=BRIEF_HELP['say'], aliases=ALIASES['say'])
    async def say(self, ctx):
        """
        Makes SuitsBot say a stored audio clip in voice via a tag system. (e.g. `!say anthem`)
        The command also supports several CLI arguments for different tasks

        "-help": Shows the command's help embed
        "-ls": Lists all audio clip tags
        "-stop": Stops the current audio clip

        Parameters
        ------------
        ctx : discord.context
            The message context object
        """

        # List of quote files
        quotes = {"anthem": ["**SOYUZ NERUSHIMY RESPUBLIK SVOBODNYKH SPLOTILA NAVEKI VELIKAYA RUS'!**", "anthem.mp3"],
                  "austin": ["IT'S ME, AUSTIN!", "itsMeAustin.mp3"],
                  "beat my dick": ["Good evening Twitter, it's ya boi EatDatPussy445.", "beatTheFuck.wav"],
                  "bold strategy": ["It's a bold strategy cotton, let's see if it pays off for 'em",
                                    "bold-strategy-cotton.mp3"],
                  "cavalry": ["*britishness intensifies*", "cheersLove.ogg"],
                  "deja vu": ["Ever get that feeling of deja vu?", "dejaVu.ogg"],
                  "disco": ["Reminder: You can stop media using the `!say -stop` command", "platinumDisco.mp3"],
                  "do it": ["*Do it*", "doIt.mp3"],
                  "everybody": ["Se *no*!", "everybody.wav"],
                  "hentai": ["It's called hentai, and it's *art*", "itsCalledHentai.mp3"],
                  "hello there": ["**GENERAL KENOBI**", "hello_there_obi.mp3"],
                  "heroes never die": ["Heroes never die!", "heroesNeverDie.ogg"],
                  "high noon": ["It's hiiiiiigh nooooooon...", "itsHighNoon.ogg"],
                  "how": ["**I MADE MY MISTAKES**", "howCould.mp3"],
                  "i tried so hard": ["Woah there, don't cut yourself on that edge", "inTheEnd.mp3"],
                  "it was me": ["Ko! No! Dio! Da!", "itWasMeDio.mp3"],
                  "laser sights": ["*Fooking laser sights*", "fookin-laser-sights.mp3"],
                  "leroy": ["LEEEEEEROOOOOOOOOOOOOY", "leroy.mp3"],
                  "love": ["AND IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII...", "iWillAlwaysLoveYou.mp3"],
                  "nerf this": ["It's nerf or nothing", "nerfThis.ogg"],
                  "nani": ["NANI SORE!?", "nani-sore.mp3"],
                  "nico": [("Nico Nico-nii~ Anata no Heart ni Nico Nico-nii, Egao todokeru Yazawa " +
                            "Nico Nico~ Nico-nii te oboeteru Love Nico~ XD"),
                           "nico_nico_nii.mp3"],
                  "nyan": [("Naname nanajyuunana-do no narabi de nakunaku inanaku " +
                            "nanahan nanadai nannaku narabete naganagame.\nOwO"),
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
                  "star destroyers": ["**IT BROKE NEW GROUND**", "starDestroyers.mp3"],
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
            (arguments, key) = parse.args(ctx.message.content)

            # ------------------------------ NO AUDIO ARGUMENTS

            # Acting on arguments
            if "help" in arguments:  # provides help using this command
                title = "`!say` User Guide"
                description = ("Plays an audio clip in voice. If not already in the user's voice channel, the bot " +
                               "will automatically join the voice channel of the user issuing the command. The bot " +
                               "holds a list of stored audio files which can be summoned using predefined tags " +
                               "(the list of tags can be viewed using the `!say -ls` command). If an audio clip is " +
                               "currently playing, another tag cannot be started. If all users leave the audio " +
                               "channel the bot is in, the bot will leave as well. If the user is not in a voice " +
                               "channel, the command will be rejected")
                helpdict = {
                    "<tag>": ("Plays the predetermined audio clip for that tag. Tags are case-insensitive, but make " +
                              "sure your spelling is right!"),
                    "-help": "Shows this list",
                    "-ls": "Lists the tags for all the available audio clips",
                    "-stop": "Stops the current voice clip"}
                await self.bot.say(embed=utils.embedfromdict(helpdict,
                                                             title=title,
                                                             description=description,
                                                             thumbnail_url=COMMAND_THUMBNAILS["say"]))
                return
            if "ls" in arguments:
                message = "The audio clips I know are: \n"
                for quoteKey in quotes.keys():
                    message += quoteKey + ", "
                await self.bot.say(message[:-2])
                return
            if "stop" in arguments:
                if not self.bot.player.is_playing():
                    await self.bot.say("I'm not saying anything...")
                else:
                    self.bot.player.stop()
                    await self.bot.say("Shutting up.")
                return

            # ------------------------------ VALIDATING KEY

            if key == "":
                await self.bot.say("You need to type the name of an audio clip for me to say. Type `!say -ls` for " +
                                   "a list of my audio clips or type `!say -help` for a full list of my arguments")
                return

            if key not in quotes.keys():
                await self.bot.say("I don't see an audio clip tagged '" + key + "'. Type `!say -ls` for a list of tags")
                return

            # ------------------------------ AUDIO INITIALIZATION

            # Gets the voice channel the author is in
            author_voice_channel = ctx.message.author.voice_channel
            if author_voice_channel is None:  # Ignores the command if the author is not in voice
                await self.bot.say("You are not in a voice channel right now")
                return

            # If the bot is connected to voice,
            if self.bot.is_voice_connected(ctx.message.server):
                voice_channel = self.bot.voice_client_in(ctx.message.server).channel
                # Does nothing if the bot is already in the author's voice channel
                if voice_channel != author_voice_channel:
                    # Stops any active voice clip
                    self.bot.player.stop()
                    voice = self.bot.voice_client_in(ctx.message.server)
                    # Moves the bot to the new channel
                    await voice.move_to(author_voice_channel)
            else:
                await self.bot.join_voice_channel(author_voice_channel)

            # ------------------------------ PLAYING AUDIO

            # Ignores command if bot is already playing a voice clip
            if self.bot.player is not None and self.bot.player.is_playing():
                await self.bot.say("Currently processing other voice command")
                return

            await self.bot.say(quotes[key][0])  # Responds with the text of the voice clip
            voice = self.bot.voice_client_in(ctx.message.server)  # Gets the active voice client
            player = voice.create_ffmpeg_player(
                self.quote_folder + quotes[key][1])  # Gets the voice clip and creates a ffmpeg player
            self.bot.player = player  # Assigns the player to the bot
            player.start()  # Plays the voice clip
        except Exception as e:
            await utils.report(self.bot, str(e), source="Say command", ctx=ctx)

    @commands.command(pass_context=True, help=LONG_HELP['leave'], brief=BRIEF_HELP['leave'], aliases=ALIASES['leave'])
    async def leave(self, ctx):
        """
        Makes SuitsBot leave its current voice channel on the server

        Parameters
        ------------
        ctx : discord.context
            The message context object
        """

        if self.bot.is_voice_connected(ctx.message.server):
            await self.bot.voice_client_in(ctx.message.server).disconnect()  # Disconnect from voice
            await self.bot.say('I have disconnected from voice channels in this server.')
        else:  # If the bot is not connected to voice, do nothing
            await self.bot.say('I am not connected to any voice channel on this server.')

    async def join_audio_channel(self, targetchannel):
        """
        Makes SuitsBot join a target channel

        Parameters
        ------------
        targetchannel : discord.Channel
            The voice channel the bot will try to connect to

        Returns
        ------------
        VoiceClient
            The voice_client is connected to as a result of the command
            (if no action was taken, this will be the pre-existing voice client)

        The bot will attempt to connect to a channel. If the bot is already in a channel,
        it will stop any audio it was playing first
        """

        targetserver = targetchannel.server
        # If the bot is connected to voice,
        if self.bot.is_voice_connected(targetserver):
            currchannel = self.bot.voice_client_in(targetserver).channel
            # Does nothing if the bot is already in the author's voice channel
            if currchannel != targetchannel:
                # Stops any active voice clip
                self.bot.player.stop()
                voice_client = self.bot.voice_client_in(targetserver)
                # Moves the bot to the new channel
                await voice_client.move_to(targetchannel)
            else:
                voice_client = self.bot.voice_client_in(targetserver)
        # If the bot is not connected to voice, join the author's channel
        else:
            voice_client = await self.bot.join_voice_channel(targetchannel)
        return voice_client


def setup(bot):
    bot.add_cog(VoiceCommands(bot))
