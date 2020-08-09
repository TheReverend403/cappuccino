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
from irc3 import rfc
from irc3.utils import IrcString
from sqlalchemy import insert

from cappuccino.util.database import Database


@irc3.plugin
class Chanlog(object):

    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self)
        self.chanlog = self.db.meta.tables['chanlog']
        self.default_nick = self.bot.nick

    def _add_event(self, event: str, data: str = None,
                   user: IrcString = None, channel: IrcString = None, target: str = None):

        if channel and not channel.is_channel:
            channel = None

        # Don't store server actions
        if user and user.is_nick:
            user = user.nick
        else:
            return

        if data:
            data = data.replace('\x00', '')
        self.db.execute(insert(self.chanlog).values(user=user, channel=channel, event=event, target=target, data=data))

    @irc3.event(rfc.PRIVMSG)
    @irc3.event(rfc.PRIVMSG, iotype='out')
    def on_privmsg(self, mask=None, event=None, target=None, data=None):
        if event == 'NOTICE' or data.startswith('\x01VERSION') or not target.is_channel:
            return

        if not mask:
            mask = self.bot.nick

        self._add_event(event, user=mask, data=data, channel=target)

    @irc3.event(rfc.JOIN_PART_QUIT)
    def on_join_part_quit(self, mask=None, event=None, channel=None, data=None):
        # Keep it clean.
        if data and event == 'QUIT':
            data = data.replace('Quit: ', '')

        if not mask:
            mask = self.bot.nick

        self._add_event(event, user=mask, data=data, channel=channel)

    @irc3.event(rfc.JOIN_PART_QUIT, iotype='out')
    def on_join_part_quit_out(self, *args, **kwargs):
        yield self.on_join_part_quit(*args, **kwargs)

    @irc3.event(rfc.KICK)
    def on_kick(self, mask=None, event=None, channel=None, target=None, data=None):
        if not mask:
            mask = IrcString(self.bot.nick)

        if data == mask.nick:
            data = None

        self._add_event(event, data=data, user=mask, channel=channel, target=target)

    @irc3.event(rfc.KICK, iotype='out')
    def on_kick_out(self, *args, **kwargs):
        yield self.on_kick(*args, **kwargs)

    @irc3.event(rfc.NEW_NICK)
    def on_new_nick(self, nick=None, new_nick=None):
        if not nick:
            nick = self.bot.nick

        self._add_event('NICK', user=nick, data=new_nick)

    @irc3.event(rfc.NEW_NICK, iotype='out')
    def on_new_nick_out(self, *args, **kwargs):
        yield self.on_new_nick(*args, **kwargs)

    @irc3.event(rfc.TOPIC)
    @irc3.event(rfc.TOPIC, iotype='out')
    def on_topic(self, mask=None, channel=None, data=None):
        if not mask:
            mask = self.bot.nick

        self._add_event('TOPIC', user=mask, data=data, channel=channel)

    @irc3.event(rfc.TOPIC, iotype='out')
    def on_topic_out(self, *args, **kwargs):
        yield self.on_topic(*args, **kwargs)

    @irc3.event(rfc.MODE)
    def on_mode(self, mask=None, event=None, target=None, modes=None, data=None):
        if not target.is_channel:
            return

        if not mask:
            mask = self.bot.nick

        self._add_event(event, data=modes, user=mask, channel=target, target=data)

    @irc3.event(rfc.MODE, iotype='out')
    def on_mode_out(self, *args, **kwargs):
        yield self.on_mode(*args, **kwargs)
