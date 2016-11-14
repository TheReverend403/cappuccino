import random
from contextlib import closing

import irc3
import requests
from irc3.plugins.command import command
from lxml import html

USER_AGENT = 'ricedb/fun.py (https://github.com/TheReverend403/ricedb)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
}


@irc3.plugin
class Fun(object):

    requires = [
        'plugins.formatting'
    ]

    random_chance = 0.35

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

    @command(permission='view')
    def roll(self, mask, target, args):
        """Roll some dice.

            %%roll <amount> <die-faces>
        """

        dice_count, dice_size = int(args['<amount>']), int(args['<die-faces>'])
        if not dice_count or not dice_size:
            return 'Please supply numbers only.'
        if dice_count < 1 or dice_count > 64 or dice_size < 4 or dice_size > 128:
            return 'Invalid roll specification. Must be a minimum of {0} and a maximum of {1}'.format(
                self.bot.format('1 4', bold=True), self.bot.format('64 128', bold=True))

        rolls = [random.SystemRandom().randint(1, dice_size) for _ in range(dice_count)]
        return '[{0}] = {1}'.format(', '.join(str(roll) for roll in rolls), self.bot.format(sum(rolls), bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*\[(?P<data>[A-Za-z0-9-_ \'"!]+)\]$')
    def intensify(self, target, data):
        if len(data) <= 32:
            self.bot.privmsg(target, self.bot.format('[{0} INTENSIFIES]'.format(data.strip().upper()), bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*wew$')
    def wew(self, target):
        if random.random() > self.random_chance:
            return
        self.bot.privmsg(target, self.bot.format('w e w l a d', bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*ayy+$')
    def ayy(self, target):
        if random.random() > self.random_chance:
            return
        self.bot.privmsg(target, 'lmao')

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) .*PRIVMSG (?P<target>#\S+) :.*(?i)(wh?(aa*z*|u)t?(\'?| i)s? ?up|\'?sup)\b')
    def gravity(self, mask, target):
        self.bot.privmsg(target,
                         '{0}: A direction away from the center of gravity of a celestial object.'.format(mask.nick))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*same$')
    def same(self, target):
        if random.random() > self.random_chance:
            return
        self.bot.privmsg(target, self.bot.format('same', bold=True))
