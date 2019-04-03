from contextlib import closing

import irc3
import requests
from bs4 import BeautifulSoup
from irc3.plugins.command import command
from requests import RequestException


@irc3.plugin
class BotUI(object):

    requires = [
        'irc3.plugins.command',
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view', aliases=['whatthecommit'])
    def wtc(self, mask, target, args):
        """Grab a random commit message.

            %%wtc
        """

        try:
            with closing(requests.get('https://whatthecommit.com/')) as response:
                commit_message = BeautifulSoup(response.text, 'html.parser').find('p').text.strip()
                commit_message = self.bot.format(commit_message, bold=True)
        except RequestException as ex:
            yield ex.strerror

        yield f'git commit -m "{commit_message}"'
