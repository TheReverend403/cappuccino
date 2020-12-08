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

from cappuccino import Plugin


@irc3.plugin
class NickServ(Plugin):
    @irc3.event(
        r":(?P<nickserv>NickServ)!\S+@\S+ NOTICE .* :This nickname is registered.*"
    )
    def login_attempt(self, nickserv):
        password = self.config.get("password", None)
        if not password:
            self.logger.warning(
                "This nick is registered but no nickserv password is set in config.ini"
            )
            return

        self.bot.privmsg(nickserv, f"IDENTIFY {password}")

    @irc3.event(r":(?P<mask>NickServ!\S+@\S+) NOTICE .* :Password accepted.*")
    def login_succeeded(self, mask):
        self.logger.info(f"Authenticated with {mask}")

    @irc3.event(r":(?P<mask>NickServ!\S+@\S+) NOTICE .* :Password incorrect.*")
    def login_failed(self, mask):
        self.logger.warning(
            f"Failed to authenticate with {mask} due to an incorrect password"
        )
