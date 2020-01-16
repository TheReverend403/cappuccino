#  This file is part of cappuccino.
#
#  cappuccino is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cappuccino is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cappuccino.  If not, see <https://www.gnu.org/licenses/>.

from enum import Enum

import ircmessage


class Color(Enum):
    WHITE = ircmessage.colors.white
    BLACK = ircmessage.colors.black
    BLUE = ircmessage.colors.blue
    GREEN = ircmessage.colors.green
    RED = ircmessage.colors.red
    BROWN = ircmessage.colors.brown
    PURPLE = ircmessage.colors.purple
    ORANGE = ircmessage.colors.orange
    YELLOW = ircmessage.colors.yellow
    LIGHT_GREEN = ircmessage.colors.light_green
    TEAL = ircmessage.colors.teal
    LIGHT_CYAN = ircmessage.colors.light_cyan
    LIGHT_BLUE = ircmessage.colors.light_blue
    PINK = ircmessage.colors.pink
    GRAY = ircmessage.colors.grey
    LIME = ircmessage.colors.lime
    LIGHT_GRAY = ircmessage.colors.light_grey


def style(text, color: Color = None, bold: bool = False, reset: bool = True) -> str:
    if color:
        color = ircmessage.colors.idToName.get(color.value, None)
    return ircmessage.style(str(text), fg=color, bold=bold, reset=reset)


def unstyle(text: str) -> str:
    return ircmessage.unstyle(text)
