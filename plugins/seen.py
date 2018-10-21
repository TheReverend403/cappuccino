import re

import irc3
import time
from datetime import timedelta
from irc3.plugins.command import command

DB_KEY = 'last_seen'


def time_format(seconds):
    delta = str(timedelta(seconds=seconds))

    # Remove microseconds in string representation
    delta = re.sub(r'\.[0-9]+', '', delta)
    return delta


@irc3.plugin
class Seen(object):

    requires = [
        'irc3.plugins.command',
        'plugins.userdb'
    ]

    def __init__(self, bot):
        self.bot = bot

    def get_last_seen(self, nick):
        return self.bot.get_user_value(nick, DB_KEY)

    def set_last_seen(self, nick, time):
        self.bot.set_user_value(nick, DB_KEY, time)

    @command(permission='view', aliases=['died'])
    def seen(self, mask, target, args):
        """Check when a user was last seen active in any channel.

            %%seen <nick>
        """

        nick = args['<nick>']

        if nick == self.bot.nick:
            return 'I\'m right here, idiot. -_-'

        if nick == mask.nick:
            return 'Are you seriously asking me that?'

        if not self.bot.get_user_value(nick, DB_KEY):
            return f'I haven\'t seen any activity from {nick} yet.'

        last_seen = self.get_last_seen(nick)
        time_now = time.time()
        timefmt = time_format(time_now - last_seen)

        return f'{nick} was last seen {timefmt} ago.'

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, target, event, mask, data):
        if mask.nick == self.bot.nick or event == 'NOTICE':
            return

        self.set_last_seen(mask.nick, time.time())

    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel):
        if mask.nick == self.bot.nick:
            return

        self.set_last_seen(mask.nick, time.time())