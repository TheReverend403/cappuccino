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

from datetime import UTC, datetime

import irc3
from humanize import naturaltime
from irc3.plugins.command import command

from cappuccino import Plugin

_DB_KEY = "last_seen"


@irc3.plugin
class Seen(Plugin):
    requires = ["irc3.plugins.command", "cappuccino.userdb"]

    def _get_last_seen(self, nick: str) -> datetime:
        return self.bot.get_user_value(nick, _DB_KEY)

    def _set_last_seen(self, nick: str, timestamp: datetime):
        self.bot.set_user_value(nick, _DB_KEY, timestamp)

    @command(permission="view", aliases=["died"])
    def seen(self, mask, target, args):
        """Check when a user was last seen active in any channel.

        %%seen <nick>
        """

        nick = args["<nick>"]

        if nick.lower() == self.bot.nick.lower():
            return "I'm right here, idiot. -_-"

        if nick.lower() == mask.nick.lower():
            return "Are you seriously asking me that?"

        if not self.bot.get_user_value(nick, _DB_KEY):
            return f"I haven't seen any activity from {nick} yet."

        last_seen = self._get_last_seen(nick)
        time_now = datetime.now(UTC)
        duration = naturaltime(time_now - last_seen)
        full_date = last_seen.strftime("%b %d %Y %H:%M UTC")

        if nick == "kori":
            return f"{nick} was right there {duration}. ({full_date})"

        return f"{nick} was last seen {duration}. ({full_date})"

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, target, event, mask, data):
        if (
            event == "NOTICE"
            or data.startswith("\x01VERSION")
            or not target.is_channel
            or mask.nick == self.bot.nick
        ):
            return

        self._set_last_seen(mask.nick, datetime.now(UTC))
