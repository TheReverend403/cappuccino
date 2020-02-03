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

import irc3
from irc3.plugins.command import command
from requests import RequestException


@irc3.plugin
class BotUI(object):
    requires = [
        'irc3.plugins.command',
        'plugins.botui'
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view', aliases=['whatthecommit'])
    def wtc(self, mask, target, args):
        """Grab a random commit message.

            %%wtc
        """

        try:
            with self.bot.requests.get('http://whatthecommit.com/index.txt') as response:
                yield f'git commit -m "{response.text.strip()}"'
        except RequestException as ex:
            yield ex.strerror
