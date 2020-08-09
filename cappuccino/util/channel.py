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


class ChannelMode(Enum):
    VOICE = '+'
    HALF_OP = '%'
    OP = '@'
    SUPER_OP = '&'
    OWNER = '~'


def is_chanop(botcontext, channel: str, nick: str) -> bool:
    for mode in ChannelMode:
        # Voiced users aren't channel operators.
        if mode is ChannelMode.VOICE:
            continue

        try:
            if nick in botcontext.channels[channel].modes[mode.value]:
                return True
        except (KeyError, AttributeError):
            continue

    return False
