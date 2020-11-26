from typing import Optional

from discord import FFmpegPCMAudio, VoiceChannel, VoiceClient
from discord.errors import ClientException
from discord.ext import commands
from discord.ext.commands import Cog

from config.local_config import SOUNDS_DIR
from constants import *
import parse
import utils


def in_voice_channel(target_channel: VoiceChannel) -> bool:
    """
    Returns whether SuitsBot is currently connected to a given VoiceChannel

    Parameters
    ------------
    target_channel : discord.VoiceChannel
        The voice channel the bot will connect to

    Returns
    ------------
    Bool: `True` if SuitsBot is currently connected to target_channel, otherwise `False`
    """
    guild_client = target_channel.guild.voice_client
    # Verify that the bot is connected to the guild's VoiceClient on the correct channel
    if guild_client and guild_client.is_connected() and guild_client.channel is target_channel:
        return True
    return False


async def join_audio_channel(target_channel: VoiceChannel) -> Optional[VoiceClient]:
    """
    Makes SuitsBot join a target voice channel and returns the VoiceClient

    If the bot is already in a different channel
    on that server, it will stop any audio it was playing first and then move into
    the new channel. If it was already in that channel, nothing will happen.

    Parameters
    ------------
    target_channel : discord.VoiceChannel
        The voice channel the bot will connect to

    Returns
    ------------
    Optional[VoiceClient] - The VoiceClient for that channel. If `None`, bot was unable to join
    """
    guild_vc = target_channel.guild.voice_client  # Check on the Voice Client for the channel's guild

    # Wrap in `try-except` to catch Timeout Error. `None` will be returned implicitly on failure
    try:
        if guild_vc is None:  # Bot is not connected to voice
            guild_vc = await target_channel.connect(timeout=10)
        elif guild_vc.channel is not target_channel:  # Bot is connected to different channel
            # Stop any playing media and move bot
            guild_vc.stop()
            await guild_vc.move_to(target_channel)

        if guild_vc.is_connected():  # Only return guild_vc on a successful connection
            return guild_vc
    except (TimeoutError, AttributeError):  # TimeoutError sometimes causes AttributeError within discord.py
        print(f"Failed to connect to {target_channel}")


class VoiceCommands(Cog):
    """
    A series of voice chat commands for the bot

    join  - Causes the bot to join the user in voice
    say   - Says an audio clip in chat based on a tag system
    leave - Kicks SuitsBot from its current audio channel
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=LONG_HELP['join'], brief=BRIEF_HELP['join'], aliases=ALIASES['join'])
    async def join(self, ctx):
        """ Makes SuitsBot join the voice channel """

        try:
            # Gets the voice channel the author is in
            author_voice_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
            if author_voice_channel is None:  # Ignore command if author is not in voice
                await ctx.send("You are not in a voice channel right now")
                return
            if in_voice_channel(author_voice_channel):  # Ignore request if bot already in voice channel
                await ctx.send("The bot is already in voice with you")
                return
            # Connect to author's channel
            await ctx.send("Joining voice channel...")
            voice_client = await join_audio_channel(author_voice_channel)
            if voice_client:
                # Plays joining voice clip
                voice_client.play(FFmpegPCMAudio(SOUNDS_DIR + 'hello_there_obi.mp3'))
            else:
                await ctx.send(f"I'm sorry {ctx.author.mention}, but I was not able to join {author_voice_channel}")
        except Exception as e:
            await utils.report(self.bot, str(e), source="join command", ctx=ctx)

    @commands.command(help=LONG_HELP['say'], brief=BRIEF_HELP['say'], aliases=ALIASES['say'])
    async def say(self, ctx):
        """
        Makes SuitsBot say a stored audio clip in voice via a tag system. (e.g. `!say anthem`)
        The command also supports several CLI arguments for different tasks

        "-help": Shows the command's help embed
        "-ls": Lists all audio clip tags
        "-stop": Stops the current audio clip
        """

        # List of quote files
        quotes = {"ah fuck": ["Ah fuck. I can't believe you've done this", "ah-fuck.mp3"],
                  "anthem": ["**SOYUZ NERUSHIMY RESPUBLIK SVOBODNYKH SPLOTILA NAVEKI VELIKAYA RUS'!**", "anthem.mp3"],
                  "austin": ["IT'S ME, AUSTIN!", "itsMeAustin.mp3"],
                  "beat my dick": ["Good evening Twitter, it's ya boi EatDatPussy445.", "beatTheFuck.wav"],
                  "boi": ["B O I", "boi.mp3"],
                  "bold strategy": ["It's a bold strategy cotton, let's see if it pays off for 'em",
                                    "bold-strategy-cotton.mp3"],
                  "careless whisper": ["*sexy sax solo intensifies*", "careless_whispers.mp3"],
                  "cavalry": ["*britishness intensifies*", "cheersLove.ogg"],
                  "deja vu": ["Ever get that feeling of deja vu?", "dejaVu.ogg"],
                  "disco": ["Reminder: You can stop media using the `!say -stop` command", "platinumDisco.mp3"],
                  "do it": ["*Do it*", "doIt.mp3"],
                  "everybody": ["Se *no*!", "everybody.wav"],
                  "ftsio": ["Fuck this shit I'm out", "fuck-this-shit-im-out.mp3"],
                  "fuck you": ["**Fuck yoooooou!**", "fuckYou.mp3"],
                  "gfd": ["God *fucking* dammit!", "gfd.mp3"],
                  "hentai": ["It's called hentai, and it's *art*", "itsCalledHentai.mp3"],
                  "hello darkness": ["*Hello darkness my old friend...*", "helloDarkness.mp3"],
                  "hello there": ["**GENERAL KENOBI**", "hello_there_obi.mp3"],
                  "heroes never die": ["Heroes never die!", "heroesNeverDie.ogg"],
                  "high noon": ["It's hiiiiiigh nooooooon...", "itsHighNoon.ogg"],
                  "how": ["**I MADE MY MISTAKES**", "howCould.mp3"],
                  "i tried so hard": ["Woah there, don't cut yourself on that edge", "inTheEnd.mp3"],
                  "it was me": ["Ko! No! Dio! Da!", "itWasMeDio.mp3"],
                  "laser sights": ["*Fooking laser sights*", "fookin-laser-sights.mp3"],
                  "leroy": ["LEEEEEEROOOOOOOOOOOOOY", "leroy.mp3"],
                  "love": ["AND IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII...", "iWillAlwaysLoveYou.mp3"],
                  "my power": ["*You underestimate my power!*", "you-underestimate-my-power.mp3"],
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
                  "over 9000": ["It's over **9000!!!**", "over9000.mp3"],
                  "pingas": ["Pingas.", "pingas.mp3"],
                  "rimshot": ["Badum, tiss", "rimshot.mp3"],
                  "roundabout": ["To be continued...", "roundabout.mp3"],
                  "sanic": ["goTtA gO faSt!", "sanic.mp3"],
                  "satania": ["BWAHAHAHA!", "sataniaLaugh.mp3"],
                  "sob": ["SON OF A BITCH!", "sob.mp3"],
                  "somebody": ["What are you doing in my swamp?!", "somebodyClipping.wav"],
                  "star destroyers": ["**IT BROKE NEW GROUND**", "starDestroyers.mp3"],
                  "stop": ["It's time to stop!", "stop.mp3"],
                  "take a sip": ["Take a fuckin' sip, babes...", "takeASip.mp3"],
                  "tea": ["I've got fucking tea, ya dickhead!", "gotTea.wav"],
                  "trash": ["**Endless trash**", "Endless Trash.mp3"],
                  "tuturu": ["TUTURUUUUUUUU", "tuturu.mp3"],
                  "violin": ["*sadness intensifies*", "sadViolin.mp3"],
                  "wake me up": ["**I CAN'T WAKE UP**", "wakeMeUp.mp3"],
                  "winky face": [":wink:", "winkyFace.ogg"],
                  "woomy": ["Woomy!", "woomy.mp3"],
                  "wow": ["Wow", "wow.mp3"],
                  "wtf": ["**Hey Todd?!**", "whatTheFuck.mp3"],
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
                await ctx.send(embed=utils.embed_from_dict(helpdict,
                                                           title=title,
                                                           description=description,
                                                           thumbnail_url=COMMAND_THUMBNAILS["say"]))
                return
            if "ls" in arguments:
                message = "The audio clips I know are: \n"
                for quoteKey in quotes.keys():
                    message += quoteKey + ", "
                await ctx.send(message[:-2])
                return
            if "stop" in arguments:
                if not self.bot.voice.is_playing():
                    await ctx.send("I'm not saying anything...")
                else:
                    self.bot.voice.stop()
                    await ctx.send("Shutting up.")
                return

            # ------------------------------ VALIDATING KEY

            if key == "":
                await ctx.send("You need to type the name of an audio clip for me to say. Type `!say -ls` for " +
                               "a list of my audio clips or type `!say -help` for a full list of my arguments")
                return

            if key not in quotes.keys():
                await ctx.send("I don't see an audio clip tagged '" + key + "'. Type `!say -ls` for a list of tags")
                return

            # ------------------------------ AUDIO INITIALIZATION

            # Gets the voice channel the author is in. If the author is not in voice, author_voice_channel is `None`
            author_voice_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
            # Ignores the command if the author is not in voice
            if author_voice_channel is None:
                await ctx.send("You are not in a voice channel right now")
                return

            # Get voice client for author's channel
            voice_client = await join_audio_channel(author_voice_channel)
            if voice_client is None:  # If VoiceClient is None, reject command
                await ctx.send(f"I'm sorry {ctx.author.mention}, but I was not able to join {author_voice_channel}")
                return

            # ------------------------------ PLAYING AUDIO

            # Ignores command if bot is already playing a voice clip
            if voice_client.is_playing():
                await ctx.send("Currently processing other voice command")
                return

            # Play audio clip
            voice_client.play(FFmpegPCMAudio(SOUNDS_DIR + quotes[key][1]))
            await ctx.send(quotes[key][0])  # Responds with the text of the voice clip

        except Exception as e:
            await utils.report(self.bot, str(e), source="say command", ctx=ctx)

    @commands.command(help=LONG_HELP['leave'], brief=BRIEF_HELP['leave'], aliases=ALIASES['leave'])
    async def leave(self, ctx):
        """
        Makes SuitsBot disconnect from the author's current voice channel

        Parameters
        ------------
        ctx : discord.context
            The message context object
        """
        try:
            # Gets the voice channel the author is in
            author_voice_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
            if author_voice_channel is None:  # Ignore command if author is not in voice
                await ctx.send("You must be connected to a voice channel to kick me from it.")
                return

            # If bot is in the author's voice channel, stops playing audio and leaves
            if in_voice_channel(author_voice_channel):
                vc = ctx.guild.voice_client
                vc.stop()
                await vc.disconnect()
                await ctx.send('I have disconnected from voice channels in this guild.')
            else:  # If the bot is not connected to voice, do nothing
                await ctx.send('I am not connected to your voice channel.')
        except Exception as e:
            await utils.report(self.bot, str(e), source="leave command", ctx=ctx)


def setup(bot):
    bot.add_cog(VoiceCommands(bot))
