import irc3
import time
from datetime import timedelta
from irc3.plugins.command import command


"""
    Author: Joaquin Varela <https://github.com/jjvvx>
"""
@irc3.plugin
class ChannelAutopsy(object):

    requires = [
        'plugins.userdb'
    ]

    def __init__(self, bot):
        self.bot = bot

        self.nick_dead   = bot.config[__name__]['nick']
        self.channel     = bot.config[__name__]['chan']
        self.notify_time = bot.config[__name__]['notify_time']

        if self.get_tod is []:
            self.update_tod(time.time())

    def get_tod(self):
        return self.bot.get_user_value(self.nick_dead, "deadsince")

    def update_tod(self, tim):
        self.bot.set_user_value(self.nick_dead, "deadsince", tim)

    def format(self, tim):
        delta = timedelta(seconds=tim)
        
        return str(delta)

    @command(permission='view')
    def died(self, mask, target, args):
        """Remind yourself how long it has been since someone's death.

            %%died
        """

        tod  = self.get_tod()
        tim = int(time.time())
        return '{nick} has been pronounced legally dead {timefmt} ago.'.format(
            nick=self.nick_dead, timefmt=self.format(tim - tod)
        )

    """
        Let's face it, from this point on this is going to be code that will
        never even run in production.
    """
    @irc3.event(r".*:(?P<nick>\S+)!\S+@\S+ PRIVMSG #(?P<channel>\S+)")
    def handle_revival(self, nick, channel):
        if nick != self.nick_dead or channel.lower() != self.channel.lower():
            return

        tim = int(time.time())
        old_tod = self.get_tod()
        self.update_tod(tim)

        if (tim - old_tod) > self.notify_time:
            txt = "{nick} has miraculously returned from the dead {timefmt} later".format(
                nick=self.nick_dead, timefmt=self.format(tim - old_tod)
            )

            self.bot.privmsg('#'+channel, txt)