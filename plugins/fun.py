from contextlib import closing

import irc3
import requests
from lxml import html
from irc3.plugins.command import command

USER_AGENT = 'ricedb/fun.py (https://github.com/TheReverend403/ricedb)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
}


@irc3.plugin
class Fun(object):

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def insult(self, mask, target, args):
        """Send a randomly generated insult from insultgenerator.org

            %%insult
        """
        try:
            with closing(requests.get('http://www.insultgenerator.org')) as response:
                doc = html.fromstring(response.text)
                insult = ''.join(doc.xpath('//div[@class="wrap"]//text()')).strip()
                yield insult
        except requests.exceptions.RequestException as err:
            self.bot.log.exception(err)
            yield 'Error: {0}'.format(err.strerror)

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :\s*\[(?P<data>[A-Za-z0-9-_ \'"!]+)\]$')
    def intensify(self, target, data):
        self.bot.privmsg(target, self.bot.bold('[{0} INTENSIFIES]'.format(data.strip().upper())))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :\s*wew$')
    def wew(self, target):
        self.bot.privmsg(target, self.bot.bold('w e w l a d'))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :\s*ayy+$')
    def ayy(self, target):
        self.bot.privmsg(target, 'lmao')

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) .*PRIVMSG (?P<target>#\S+) :\S*(wh?(aa*z*|u)t?(\'?| i)s? ?up|\'?sup)\S*')
    def gravity(self, mask, target):
        self.bot.privmsg(target,
                         '{0}: A direction away from the center of gravity of a celestial object.'.format(mask.nick))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :\s*same$')
    def same(self, target):
        self.bot.privmsg(target, self.bot.bold('same'))

