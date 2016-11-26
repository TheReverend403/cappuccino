import time
from contextlib import closing

import irc3
import random
import requests
from bs4 import BeautifulSoup
from irc3.plugins.command import command

USER_AGENT = 'ricedb/fun.py (https://github.com/TheReverend403/ricedb)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
}

# Borrowed from https://github.com/GeneralUnRest/8ball-bot/blob/master/8ball.js
EIGHTBALL_RESPONSES = ['Signs point to yes.', 'Yes.', 'Reply hazy, try again.', 'Without a doubt.',
                       'My sources say no.', 'As I see it, yes.', 'You may rely on it.', 'Concentrate and ask again.',
                       'Outlook not so good.', 'It is decidedly so.', 'Better not tell you now.', 'Very doubtful.',
                       'Yes - definitely.', 'It is certain.', 'Cannot predict now.', 'Most likely.', 'Ask again later.',
                       'My reply is no.', 'Outlook good.', 'Don\'t count on it.']


@irc3.plugin
class Fun(object):
    requires = [
        'plugins.formatting'
    ]

    random_chance = 0.05
    last_reply_time = 0

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def insult(self, mask, target, args):
        """Send a randomly generated insult from insultgenerator.org

            %%insult
        """
        try:
            with closing(requests.get('http://www.insultgenerator.org')) as response:
                insult = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'wrap'}).text.strip()
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

    @command(permission='view', name='8ball')
    def eightball(self, mask, target, args):
        """Consult the wise and powerful 8 ball.

            %%8ball <query>...
        """

        nick = self.bot.format(mask.nick, antiping=True)
        return '{0}: {1}'.format(nick, random.choice(EIGHTBALL_RESPONSES))

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
        if time.time() - self.last_reply_time < 30 or random.random() > self.random_chance:
            return
        self.last_reply_time = time.time()
        self.bot.privmsg(target,
                         '{0}: A direction away from the center of gravity of a celestial object.'.format(mask.nick))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*same$')
    def same(self, target):
        if random.random() > self.random_chance:
            return
        self.bot.privmsg(target, self.bot.format('same', bold=True))
