import irc3
import sentry_sdk
from irc3.plugins.command import command


@irc3.plugin
class Sentry(object):

    requires = [
        'irc3.plugins.command',
    ]

    def __init__(self, bot):
        self.bot = bot
        try:
            sentry_sdk.init(self.bot.config[__name__]['dsn'])
        except KeyError:
            self.bot.log.warn('Missing Sentry DSN')
            return

    @command(name='testsentry', permission='admin', show_in_help_list=False)
    def testsentry(self, mask, target, args):
        """Force an exception to test Sentry.

            %%testsentry
        """
        raise Exception('Sentry test')
