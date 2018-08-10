import re

import irc3
import time
from datetime import timedelta
from irc3.plugins.command import command


@irc3.plugin
class ChannelAutopsy(object):

    requires = [
        'plugins.userdb'
    ]

    def __init__(self, bot):
        self.bot = bot

        self.nick_dead = bot.config[__name__]['nick']
        self.channel = bot.config[__name__]['chan']
        self.notify_time = bot.config[__name__]['notify_time']

        if not self.get_time_of_death():
            self.set_time_of_death(time.time())

    def get_time_of_death(self):
        return self.bot.get_user_value(self.nick_dead, "deadsince")

    def set_time_of_death(self, time):
        self.bot.set_user_value(self.nick_dead, "deadsince", time)

    def time_format(self, seconds):
        delta = str(timedelta(seconds=seconds))

        # Remove microseconds in string representation
        delta = re.sub(r'\.[0-9]+', '', delta)
        return delta

    @command(permission='view')
    def died(self, mask, target, args):
        """Remind yourself how long it has been since someone's death.

            %%died
        """

        time_of_death = self.get_time_of_death()
        time_now = time.time()
        timefmt = self.time_format(time_now - time_of_death)

        return f'{self.nick_dead} has been pronounced legally dead {timefmt} ago.'

    @irc3.event(r".*:(?P<nick>\S+)!\S+@\S+ PRIVMSG #(?P<channel>\S+)")
    def handle_revival(self, nick, channel):
        if nick != self.nick_dead or channel.lower() != self.channel.lower():
            return

        current_time = time.time()
        old_time_of_death = self.get_time_of_death()
        self.set_time_of_death(current_time)

        if (current_time - old_time_of_death) > self.notify_time:
            timefmt = self.time_format(current_time - old_time_of_death)

            return f'{self.nick_dead} has miraculously returned from the dead {timefmt} later.'
