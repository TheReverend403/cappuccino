import irc3
import sentry_sdk
from irc3.plugins.command import command
from requests import RequestException


def before_send(event, hint):
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, (RequestException, TimeoutError)):
            return None

    return event


@irc3.plugin
class Sentry(object):

    requires = [
        'irc3.plugins.command',
    ]

    def __init__(self, bot):
        self.bot = bot
        try:
            sentry_sdk.init(self.bot.config[__name__]['dsn'], before_send=before_send)
        except KeyError:
            self.bot.log.warn('Missing Sentry DSN')
            return

    @command(name='testsentry', permission='admin', show_in_help_list=False)
    def testsentry(self, mask, target, args):
        """Force an exception to test Sentry.

            %%testsentry
        """
        raise Exception('Sentry test')
