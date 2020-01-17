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
from sqlalchemy import Column, DateTime, MetaData, String, Table, func

from util.database import Database


@irc3.plugin
class Chanlog(object):

    db_meta = MetaData()
    chanlog = Table('chanlog', db_meta,
                    Column('user', String),
                    Column('channel', String),
                    Column('event', String),
                    Column('target', String),
                    Column('data', String),
                    Column('time', DateTime, server_default=func.now()))

    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self)
        print(self.bot)

    def _add_event(self, user, event, data, channel: IrcString = None, target=None):
        if not channel.is_channel:
            channel = None

        self.db.execute(self.chanlog.insert().values(
            user=user, channel=channel, event=event, target=target, data=data
        ))

    @irc3.event(r'PRIVMSG (?P<target>[^#]+) :(?P<data>.*)', iotype='out')
    def on_privmsg_out(self, event, target, data):
        print('privmsg out')
        self._add_event(self.bot.nick, 'PRIVMSG', data, channel=target)

    @irc3.event(rfc.PRIVMSG)
    def on_privmsg(self, mask, event, target, data):
        if event == 'NOTICE' or data.startswith('\x01VERSION') or not target.is_channel:
            return

        self._add_event(mask, event, data, channel=target)

    @irc3.event(rfc.JOIN_PART_QUIT)
    @irc3.event(rfc.JOIN_PART_QUIT, iotype='out')
    def on_join_part_quit(self, mask, event, channel, data):
        self._add_event(mask, event, data, channel=channel)

    @irc3.event(rfc.KICK)
    @irc3.event(rfc.KICK, iotype='out')
    def on_kick(self, mask, event, channel, target, data):
        self._add_event(mask, event, data, channel, target)

    @irc3.event(rfc.NEW_NICK)
    @irc3.event(rfc.NEW_NICK, iotype='out')
    def on_new_nick(self, nick, newnick):
        self._add_event(nick, 'NICK', newnick)

    @irc3.event(rfc.TOPIC)
    @irc3.event(rfc.TOPIC, iotype='out')
    def on_topic(self, mask, channel, data):
        self._add_event(mask, 'TOPIC', data, channel)

    @irc3.event(rfc.MODE)
    @irc3.event(rfc.MODE, iotype='out')
    def on_mode(self, mask, event, target, modes, data):
        if not target.is_channel:
            return
        self._add_event(mask, event, modes, channel=target, target=data)
