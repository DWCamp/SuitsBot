import re
import utils


class Regex:
    def __init__(self, bot):
        subdomains = "(?:(?:www|old|np|m|en|dd|us|de)\.)?"
        self.bot = bot
        self.amazon = re.compile('https://www\.amazon\.com/(?:\w+-)+\w+/dp/(?:\w{10})')
        self.newegg = re.compile('https://www\.newegg\.com/Product/Product\.aspx\?Item=(?:\w{15})', re.IGNORECASE)
        self.comment = re.compile('https:\/\/' + subdomains + 'reddit\.com\/r\/\w+\/comments\/\w{6}\/[\w%]+\/\w{7}\/?')
        self.post = re.compile('https?://' + subdomains + 'reddit.com/r/\w{1,20}/comments/\w{5,6}/\w+/?\B')
        self.subreddit = re.compile('((^|\s)\/?r\/\w+(\s|$))')
        self.twitter_handle = re.compile('(\s|^)(@{1})(\w{1,15})($|\s)')
        self.twitter_id = re.compile('\\b(https://twitter\\.com/\\w{1,15}/status/)(\\d{19})\\b')
        self.url = re.compile("https?:\/\/" +  # Protocol
                              "(([\w\$\-+!*'\(\),])+\.){1,}" +  # Domain
                              "([\w\$\-+!*'\(\),])+" +  # Top level domain
                              "(\/[\w\$\-+#!*'\(\),]+)*(\/)?" +  # directory
                              "(\.[a-zA-Z]+)?" +  # File type
                              "(\?(([\w+\-_.]*=([\w+\-_.]|(%[0-9A-F]{2}))*)&)*" +  # URL parameters (1/2)
                              "([\w+\-_.]*=([\w+\-_.]|(%[0-9A-F]{2}))*)?)?")  # URL parameters (2/2)

    def is_url(self, string):
        """
        Validates that a string is a properly formatted url

        Parameters
        -------------
        string : str
            The string to check

        Returns
        -------------
        Returns True if the url matches the format of a url
        """
        return self.url.fullmatch(string) is not None

    # Reddit

    def find_comments(self, message):
        return re.findall(self.comment, message)

    def find_posts(self, message):
        return re.findall(self.post, message)

    def find_subreddits(self, message):
        return re.findall(self.subreddit, message)

    # Stores

    def find_amazon(self, message):
        return re.findall(self.amazon, message)

    def find_newegg(self, message):
        return re.findall(self.newegg, message)

    # Twitter

    def find_twitter_handle(self, message):
        matches = re.findall(self.twitter_handle, message)
        if matches:
            return [match[2] for match in matches]  # Grab only the user name
        return []

    def find_twitter_id(self, message):
        matches = re.findall(self.twitter_id, message)
        if matches:
            return [match[1] for match in matches]  # Grab only the status id
        return []


def args(message):
    """ Parses arguments from a message

    Returns
    -------------
    List
    [0] - A list of the arguments
    [1] - The message without the arguments
     """
    message = stripcommand(message)
    arguments = []
    i = 0
    while i < len(message) and message[i] == "-":  # Looks for arguments
        argument = ""
        i += 1
        # iterates over charcters until it finds the end of the arguments
        while i < len(message) and not message[i].isspace():
            argument = argument + message[i]
            i += 1
        arguments.append(argument.lower())
        i += 1
    return arguments, message[i:].strip()


def apos(string):
    """ Make apostrophes and quotes consistent within a string

    Different keyboards, especially the iPhone keyboard, will use different unicode characters
    for apostrophes and quotes at the beginning, middle and end of strings. These look better
    aesthetically, but they provide a problem for text searching. This function replaces all
    the unicode apostrophes with a single type ('), all unicode quotation marks with a single
    type ("), and returns the edited string
    """
    string = string.replace("’", "'")
    string = string.replace("‘", "'")
    string = string.replace("”", '"')
    string = string.replace("“", '"')
    string = string.replace("„", '"')
    return string


def func_param(string):
    """
    Strips off the command and then parses out the function
    and parameter from the content of a message
    
    Returns
    ------------
    A list
    [0] - The function called
    [1] - The parameter text
    """
    message = stripcommand(string)
    if message == "":
        return ["", ""]
    whitespace = utils.first_whitespace(message)
    # Separates the function from the parameter
    if whitespace > 0:
        func = message[:whitespace].lower()
        parameter = message[whitespace + 1:].strip()
    else:
        func = message.lower()
        parameter = ""
    return [func, parameter]


def key_value(message, attachments=None):
    """ Parses key and value from a message and its attachments

    Parameters
    -------------
    message : str
        The message to parse, formatted as `[key] value`
    attachments : Optional - list
        The attachments to the message. These will have their urls extracted and appended to the value

    Returns
    -------------
    If everything went well, returns a list of the key and value:
    [0] - Key string
    [1] - Value string

    If there was an issue in parsing, returns a list of None and the error message
    [0] - None
    [1] - Error Message

    Error messages:
        "EMPTY KEY" - The brackets contained no key
        "UNCLOSED KEY" - The brackets of the key were unclosed
        "NO VALUE" - There was no value to pair with the key
        "WHITESPACE KEY" - The key was entirely whitespace characters
        "KEY STARTS WITH -" - User entered a key starting with '-', which conflicts with argument parsing
    """

    if attachments is None:
        attachments = []

    end = message.find("]")
    if end == 1:  # no tag key
        return [None, "EMPTY KEY"]
    if end == -1:  # unclosed tag key
        return [None, "UNCLOSED KEY"]
    tagkey = message[1:end]
    if len(message) < (end + 3):
        if len(attachments) == 0:
            return [None, "NO VALUE"]
        tagvalue = ""
        for attachment in attachments:
            tagvalue += "\n" + attachment['url']
        return [tagkey.lower(), tagvalue]
    end_offset = 2
    if message[end + 1] != " ":  # Starts the tagvalue immediately after the closing bracket if there isn't a space
        end_offset = 1
    tagvalue = message[(end + end_offset):]  # Sets the value of the tag
    if tagkey.isspace():
        return [None, "WHITESPACE KEY"]
    elif tagkey[0] == "-":
        return [None, "KEY STARTS WITH -"]
    for attachment in attachments:
        tagvalue += "\n" + attachment['url']
    return [tagkey, tagvalue]


def number_in_brackets(string):
    """
    Takes a string containing a number that may or may not be in brackets and returns it as an integer

    Parameters
    -------------
    string - str
        The string to parse

    Returns
    -------------
    int - The value passed

    Raises
    -------------
    ValueError - If the brackets were not closed or the number could not be parsed
    """
    if string[0] == "[":
        close_bracket_loc = string.find("]")
        if close_bracket_loc == -1:
            raise ValueError("You never closed that bracket")
        try:
            index = int(string[1:close_bracket_loc])
            return index
        except ValueError:
            raise ValueError("Could not parse the number '" + string[1:close_bracket_loc] + "'")
    else:
        try:
            index = int(string)
            return index
        except ValueError:
            raise ValueError("Could not parse the number '" + string + "'")


def stringandoptnum(string):
    """
    Takes a string containing a string and optionally a number before it in brackets and returns them

    Parameters
    -------------
    string - Optional String
        e.g. '[1] test' or 'test again'

    Returns
    -------------
    An array of the numbers parsed to integers if the 

    Raises
    -------------
    ValueError - If there is a parse failure
    """
    if string[0] == "[":
        close_bracket_loc = string.find("]")
        if close_bracket_loc == -1:
            raise ValueError("You never closed your brackets")
        try:
            index = int(string[1:close_bracket_loc])
        except ValueError:
            raise ValueError("Could not parse the number '" + string[1:close_bracket_loc] + "'")
        element = string[close_bracket_loc + 1:].strip()
        return [element, index]
    else:
        return [string, None]


def stripcommand(content):
    """ Removes the command invocation from the front of a message """
    endtag = utils.first_whitespace(content)
    if endtag is -1:
        message = ""
    else:
        message = content[endtag:].strip()
    return message


def twonumbers(string):
    """
    Parse a string into two numbers

    Parameters
    -------------
    string - Optional String
        A string containing two numbers, inside or outside of brackets, separated by a space

    Returns
    -------------
    An array of the numbers parsed to integers
    """
    numbers = string.split(" ")
    if len(numbers) < 2:
        raise ValueError("There were less than two numbers")
    numbers = numbers[:2]
    # Remove brackets, if the function was called with brackets
    if numbers[0][0] == "[":
        close_bracket_loc = numbers[0].find("]")
        if close_bracket_loc == -1:
            raise ValueError("You never closed the brackets on the first number")
        numbers[0] = numbers[0][1:close_bracket_loc]
    if numbers[1][0] == "[":
        close_bracket_loc = numbers[1].find("]")
        if close_bracket_loc == -1:
            raise ValueError("You never closed the brackets on the second number")
        numbers[1] = numbers[1][1:close_bracket_loc]
    try:
        numbers[0] = int(numbers[0])
    except ValueError:
        raise ValueError("'" + numbers[0] + "' is not a number")
    try:
        numbers[1] = int(numbers[1])
    except ValueError:
        raise ValueError("'" + numbers[1] + "' is not a number")
    return numbers
