import re

from enum import Enum
import irc3

IRC_CODES_REGEX = re.compile('\x1f|\x02|\x1D|\x03(?:\d{1,2}(?:,\d{1,2})?)?', re.UNICODE)


@irc3.plugin
class Formatting(object):

    class Color(Enum):
        RESET = '\x0f'
        WHITE = '00'
        BLACK = '01'
        BLUE = '02'
        GREEN = '03'
        RED = '04'
        BROWN = '05'
        PURPLE = '06'
        ORANGE = '07'
        YELLOW = '08'
        LIGHT_GREEN = '09'
        TEAL = '10'
        LIGHT_CYAN = '11'
        LIGHT_BLUE = '12'
        PINK = '13'
        GRAY = '14'
        LIGHT_GRAY = '15'

    def __init__(self, bot):
        self.bot = bot
        self.bot.color = self.Color

    @irc3.extend
    def format(self, text, color=None, bold=False, reset=True):
        if bold:
            text = f'\x02{text}'
        if color:
            text = f'\x03{color.value}{text}'
        if reset:
            text += self.bot.color.RESET.value
        return text

    @irc3.extend
    def strip_formatting(self, string):
        return IRC_CODES_REGEX.sub('', string)
