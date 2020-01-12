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


@irc3.plugin
class NickServ(object):

    def __init__(self, bot):
        self.bot = bot

    @irc3.event(r':(?P<nickserv>NickServ)!\S+@\S+ NOTICE .* :This nickname is registered.*')
    def login_attempt(self, nickserv):
        try:
            password = self.bot.config[__name__]['password']
        except KeyError:
            self.bot.log.warn('This nick is registered but no nickserv password is set in config.ini')
        else:
            self.bot.privmsg(nickserv, f'IDENTIFY {password}')

    @irc3.event(r':(?P<mask>NickServ!\S+@\S+) NOTICE .* :Password accepted.*')
    def login_succeeded(self, mask):
        self.bot.log.info(f'Authenticated with {mask}')

    @irc3.event(r':(?P<mask>NickServ!\S+@\S+) NOTICE .* :Password incorrect.*')
    def login_failed(self, mask):
        self.bot.log.warn(f'Failed to authenticate with {mask} due to an incorrect password')
