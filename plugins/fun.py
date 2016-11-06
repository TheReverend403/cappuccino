import irc3
import requests
from lxml import html
from irc3.plugins.command import command


@irc3.plugin
class Plugin(object):

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def insult(self, mask, target, args):
        """Send a randomly generated insult from insultgenerator.org

            %%insult
        """
        response = None
        try:
            response = requests.get('http://www.insultgenerator.org')
        except requests.exceptions.RequestException as ex:
            self.bot.log.exception(ex)
            yield 'Error: {0}'.format(ex.strerror)
        else:
            doc = html.fromstring(response.text)
            insult = ''.join(doc.xpath('//div[@class="wrap"]/text()')).strip()
            yield insult
        finally:
            if response is not None:
                response.close()

    @command(name='wtc', permission='view')
    def whatthecommit(self, mask, target, args):
        """Send a random commit message from whatthecommit.com.

            %%wtc
        """
        response = None
        try:
            response = requests.get('http://whatthecommit.com')
        except requests.exceptions.RequestException as ex:
            self.bot.log.exception(ex)
            yield 'Error: {0}'.format(ex.strerror)
        else:
            doc = html.fromstring(response.text)
            commit_message = doc.xpath('//div[@id="content"]/p/text()')[0].strip()
            yield commit_message
        finally:
            if response is not None:
                response.close()
