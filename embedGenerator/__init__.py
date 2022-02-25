from embedGenerator.baseGenerator import *
from embedGenerator.SubredditGenerator import SubredditGenerator


async def process_message(message: Message):
    """
    Executes EmbedGeneration on all EmbedGenerator subclasses
    :param message: The message to parse
    """
    for subclass in BaseGenerator.__subclasses__():
        print(f"Calling {subclass.__name__}")
        await subclass.run(message)
    print("Processed")
