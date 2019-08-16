"""
Upon startup, this dictionary will contain:
    - "CLIENT_ID"
    - "CLIENT_SECRET"
    - "BOT_TOKEN"
    - "MYSQL_USER"
    - "MYSQL_PASSWORD"
    - "WOLFRAMALPHA_APPID"
    - "JDOODLE_ID"
    - "JDOODLE_SECRET"
    - "REDDIT_ID"
    - "REDDIT_SECRET"
    - "TWITTER_BEARER"
    - "UNSPLASH_CLIENT_ID"
    - "YOUTUBE_KEY"
"""
tokens = {}


def set_tokens(token_dict):
    global tokens
    tokens = token_dict
