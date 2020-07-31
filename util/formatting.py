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

import ircstyle


class Color:
    WHITE = ircstyle.colors.white
    BLACK = ircstyle.colors.black
    BLUE = ircstyle.colors.blue
    GREEN = ircstyle.colors.green
    RED = ircstyle.colors.red
    BROWN = ircstyle.colors.brown
    PURPLE = ircstyle.colors.purple
    ORANGE = ircstyle.colors.orange
    YELLOW = ircstyle.colors.yellow
    LIGHT_GREEN = ircstyle.colors.light_green
    TEAL = ircstyle.colors.teal
    LIGHT_CYAN = ircstyle.colors.light_cyan
    LIGHT_BLUE = ircstyle.colors.light_blue
    PINK = ircstyle.colors.pink
    GRAY = ircstyle.colors.grey
    LIME = ircstyle.colors.lime
    LIGHT_GRAY = ircstyle.colors.light_grey


def style(text, fg: Color = None, bg: Color = None, bold=False, italics=False, underline=False, reset=True) -> str:
    return ircstyle.style(str(text), fg=fg, bg=bg, italics=italics, underline=underline, bold=bold, reset=reset)


def unstyle(text: str) -> str:
    return ircstyle.unstyle(text)
