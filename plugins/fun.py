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
        try:
            response = requests.get('http://www.insultgenerator.org', headers={'Connection': 'close'})
        except requests.exceptions.RequestException as ex:
            self.bot.log.exception(ex)
            yield 'Error: {0}'.format(ex.strerror)
        else:
            doc = html.fromstring(response.text)
            insult = ''.join(doc.xpath('//div[@class="wrap"]/text()')).strip()
            yield insult

    @command(name='wtc', permission='view')
    def whatthecommit(self, mask, target, args):
        """Send a random commit message from whatthecommit.com.

            %%wtc
        """
        try:
            response = requests.get('http://whatthecommit.com', headers={'Connection': 'close'})
        except requests.exceptions.RequestException as ex:
            self.bot.log.exception(ex)
            yield 'Error: {0}'.format(ex.strerror)
        else:
            doc = html.fromstring(response.text)
            commit_message = doc.xpath('//div[@id="content"]/p/text()')[0].strip()
            yield commit_message

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG '
                r'(?P<target>\S+) :\s*\[(?P<data>[A-Za-z0-9-_ \'"!]+)\]$')
    def intensify(self, mask, target, data):
        self.bot.privmsg(target, self.bot.bold('[{0} INTENSIFIES]'.format(data.strip().upper())))

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG '
                r'(?P<target>\S+) :\s*wew$')
    def wew(self, mask, target):
        self.bot.privmsg(target, self.bot.bold('w e w l a d'))

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG '
                r'(?P<target>\S+) :\s*ayy+$')
    def ayy(self, mask, target):
        self.bot.privmsg(target, 'lmao')

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG '
                r'(?P<target>\S+) :\s*(wh?(aa*z*|u)t?(\'?| i)s? ?up|\'?sup)$')
    def gravity(self, mask, target):
        self.bot.privmsg(target,
                         '{0}: A direction away from the center of gravity of a celestial object.'.format(mask.nick))

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG '
                r'(?P<target>\S+) :\s*same$')
    def same(self, mask, target):
        self.bot.privmsg(target, self.bot.bold('same'))

