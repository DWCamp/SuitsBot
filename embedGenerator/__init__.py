from embedGenerator.baseGenerator import *
from embedGenerator.DiscordMessageGenerator import DiscordMessageGenerator
from embedGenerator.RedditSelfPostGenerator import RedditSelfPostGenerator
from embedGenerator.RedditCommentGenerator import RedditCommentGenerator
from embedGenerator.TwitterReplyGenerator import TwitterReplyGenerator
from embedGenerator.FxTwitterGenerator import FxTwitterGenerator
from embedGenerator.SubredditGenerator import SubredditGenerator


async def process_message(message: Message):
    """
    Executes EmbedGeneration on all EmbedGenerator subclasses
    :param message: The message to parse
    """
    for subclass in BaseGenerator.__subclasses__():
        await subclass.run(message)
