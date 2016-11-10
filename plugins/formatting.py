import irc3


@irc3.extend
def antiping(bot, text):
    """Adds zero-width spaces after each character in a string to avoid pinging users"""
    return '\u200B'.join(text)


@irc3.extend
def color(bot, text, colorvalue):
    # TODO: Add constants for IRC colours.
    return '\x030{0}{1}\x0f'.format(colorvalue, text)


@irc3.extend
def bold(bot, text):
    return '\x02{0}\x0f'.format(text)
