from contextlib import closing

import irc3
import requests
from irc3.plugins.command import command
from requests import RequestException

USER_AGENT = 'cappuccino (https://github.com/FoxDev/cappuccino)'

REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB,en-US,en;q=0.5'
}

REQUEST_OPTIONS = {
    'timeout': 3,
    'allow_redirects': True,
    'headers': REQUEST_HEADERS
}


@irc3.plugin
class BotUI(object):

    requires = [
        'irc3.plugins.command',
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view', aliases=['whatthecommit'])
    def wtc(self, mask, target, args):
        """Grab a random commit message.

            %%wtc
        """

        try:
            with closing(requests.get('https://whatthecommit.com/index.txt', **REQUEST_OPTIONS)) as response:
                yield f'git commit -m "{response.text.strip()}"'
        except RequestException as ex:
            yield ex.strerror

