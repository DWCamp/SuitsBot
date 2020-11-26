import random
from discord.ext import commands
from discord.ext.commands import Cog
from constants import *
import utils
import parse


class Random(Cog):

    """
    Performs serveral functions employing a random number generator such as dice rolling and coin flipping
    """

    def __init__(self, bot):
        self.bot = bot

    # Randomizer
    @commands.command(help=LONG_HELP['rand'], brief=BRIEF_HELP['rand'], aliases=ALIASES['rand'])
    async def rand(self, ctx):
        try:
            # Extracts the function and parameter from the message
            [func, parameter] = parse.func_param(ctx.message.content)

            # !rand help
            if func in ["help", ""]:
                title = "!rand - User Guide"
                description = "Randomizer. This command is used for randomization in several circumstances. From " \
                              "coin flips and dice rolls to random numbers and picking from lists, let the bot " \
                              "generate random numbers for you.\n\n**WARNING**\nThis command is only pseudorandom " \
                              "and not cryptographically secure"
                helpdict = {"!rand": "No function. Will present this help list",
                            "!rand help": "This command. Shows user guide",
                            "!rand coin": "Flips a coin",
                            "!rand item <A>, <B>, <C>...": "Returns a random item from a comma delineated list",
                            "!rand num": "Returns a random decimal",
                            "!rand num <A>": "Returns a random integer from 0 to A",
                            "!rand num <A> <B>": "Returns a random integer between A and B",
                            "!rand roll <num>d<sides>,...": "Rolls the number of n-sided dice presented. "
                                                            "Multiple dice types can be rolled with a comma separated "
                                                            "list"
                            }
                await ctx.send(embed=utils.embed_from_dict(helpdict,
                                                           title=title,
                                                           description=description,
                                                           thumbnail_url=COMMAND_THUMBNAILS["rand"]))
                return

            # !rand coin
            if func == "coin":
                await ctx.send(utils.random_element(["Heads!", "Tails!"]))
                return

            # !rand item <item>, <item>, <item>
            if func == "item":
                if len(parameter) == 0:
                    await ctx.send("I need a comma delineated list (e.g. '!random item A, B, C, D, E' etc.) "
                                       "to pick from")
                    return
                itemlist = list(filter(None, parameter.split(",")))
                if len(itemlist) == 0:
                    await ctx.send("There aren't any items here for me to choose from!")
                    return
                elif len(itemlist) == 1:
                    await ctx.send("There's only one item. That's an easy choice: " + itemlist[0])
                    return
                await ctx.send("I choose... " + utils.random_element(itemlist).strip())
                return

            # rand num
            # rand num <num>
            # rand num <num> <num>
            if func == "num" or func == "number":
                if len(parameter) == 0:
                    await ctx.send(str(random.random()))
                    return
                numbers = parameter.split(" ")
                if len(numbers) == 1:
                    try:
                        bound = int(numbers[0])
                    except ValueError:
                        await ctx.send("I can't seem to parse '" + numbers[0] + "'")
                        return
                    await ctx.send(str(random.randint(0, bound)))
                else:
                    try:
                        lowerbound = int(numbers[0])
                    except ValueError:
                        await ctx.send("I can't seem to parse '" + numbers[0] + "'")
                        return
                    try:
                        upperbound = int(numbers[1])
                    except ValueError:
                        await ctx.send("I can't seem to parse '" + numbers[1] + "'")
                        return
                    if upperbound < lowerbound:
                        temp = upperbound
                        upperbound = lowerbound
                        lowerbound = temp
                    message = str(random.randint(lowerbound, upperbound))
                    if len(numbers) > 2:
                        message += "\n\nFYI, this function takes a maximum of two only arguments"
                    await ctx.send(message)
                return

            # !rand roll <num>d<sides>, <num>d<sides>
            if func == "roll":
                dice = list(filter(None, parameter.split(",")))
                total = 0
                message = ""
                for die in dice:
                    die = die.strip()
                    dloc = die.find("d")
                    # if there is no "d"
                    if dloc == -1:
                        await ctx.send("I don't see a 'd' in the argument '" + die + "'.")
                        return

                    # if there is no number in front of the "d", it is assumed to be one
                    if dloc == 0:
                        count = "1"
                        sides = die[1:]
                    # if there is no number after the "d", the bot rejects it
                    elif (dloc + 1) == len(die):
                        await ctx.send("I don't see a number after 'd' in the argument '" + die +
                                           "'. I need to know a number of sides")
                        return
                    else:
                        count = die[0:dloc]
                        sides = die[dloc + 1:]

                    try:
                        sides = int(sides)
                    except ValueError:
                        await ctx.send("I'm sorry, but '" + sides + "' isn't a parsable integer...")
                        return
                    try:
                        count = int(count)
                    except ValueError:
                        await ctx.send("I'm sorry, but '" + count + "' isn't a parsable integer...")
                        return

                    if count > 100000:
                        await ctx.send(str(count) + " dice is a *lot*. I think rolling that many would hurt "
                                           "my head :confounded:\nPlease don't make me do it.")
                        return
                    dicesum = 0
                    for i in range(0, count):
                        dicesum += random.randint(1, sides)
                    total += dicesum
                    message += str(count) + " d" + str(sides) + ": I rolled " + str(dicesum) + "\n"
                if len(dice) > 1:
                    await ctx.send(message + "Total: " + str(total))
                else:
                    await ctx.send(message)
                return

            await ctx.send(
                "I don't recognize the function `" + func + "`. Type `!rand help` for information on this command")

        except Exception as e:
            await utils.report(self.bot, str(e), source="Rand command", ctx=ctx)


def setup(bot):
    bot.add_cog(Random(bot))
