import time
from contextlib import closing

import irc3
import random
import re
import requests
from bs4 import BeautifulSoup
from irc3.plugins.command import command

USER_AGENT = 'ricedb/fun.py (https://github.com/TheReverend403/ricedb)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
}

DICE_SIDES_LIMIT = (4, 128)
DICE_COUNT_LIMIT = (1, 64)

DECIDE_DELIMITERS = [' or ', ',', '|']

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
    last_reply_time = None

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
    def decide(self, mask, target, args):
        """Make the difficult decisions in life.

            %%decide <options>...
        """

        options = ' '.join(args['<options>'])
        for delimiter in DECIDE_DELIMITERS:
            options = options.replace(delimiter, '|')
        options = options.split('|')
        options = list(filter(bool, set(option.replace(delimiter, '').strip()
                                        for delimiter in DECIDE_DELIMITERS
                                        for option in options
                                        if option not in DECIDE_DELIMITERS)))

        [options.remove(delimiter.strip()) for delimiter in DECIDE_DELIMITERS if delimiter.strip() in options]
        self.bot.log.debug('Parsed options: %s', options)

        nick = self.bot.format(mask.nick, antiping=True)
        if not options:
            return '{0}: I can\'t make a decision for you if you don\'t give me any choices >:V'.format(nick)

        options_length = len(options)
        if options_length == 1:
            options = ['Yes.', 'Maybe.', 'No.']
        elif options_length == 2:
            options.extend(['Neither.', 'Both.'])
        else:
            options.extend(['None of the above.', 'All of the above.'])

        return '{0}: {1}'.format(nick, random.choice(options))

    @command(permission='view')
    def roll(self, mask, target, args):
        """Roll some dice.

            %%roll <amount> <die-faces>
        """

        dice_count, dice_size = int(args['<amount>']), int(args['<die-faces>'])
        if not dice_count or not dice_size:
            return 'Please supply numbers only.'
        count_limit_lower, count_limit_upper = DICE_COUNT_LIMIT
        size_limit_lower, size_limit_upper = DICE_SIDES_LIMIT
        if target.is_channel:
            count_limit_upper, size_limit_upper = int(count_limit_upper / 2), int(size_limit_upper / 2)
        if dice_count < count_limit_lower or dice_count > count_limit_upper \
                or dice_size < size_limit_lower or dice_size > size_limit_upper:
            return 'Invalid roll specification. Must be a minimum of {0} and a maximum of {1}'.format(
                self.bot.format('{0} {1}'.format(count_limit_lower, size_limit_lower), bold=True),
                self.bot.format('{0} {1}'.format(count_limit_upper, size_limit_upper), bold=True))

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
        data = data.strip()
        if data and len(data) <= 32:
            self.bot.privmsg(target, self.bot.format('[{0} INTENSIFIES]'.format(data.upper()), bold=True))

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

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) .*PRIVMSG (?P<target>#\S+) :.*(?i)(wh?(aa*(z|d)*|u)t?(\'?| i)s? ?up|\'?sup)\b')
    def gravity(self, mask, target):
        if self.last_reply_time and time.time() - self.last_reply_time < 60 * 60:  # 1 hour rate limit
            return
        self.last_reply_time = time.time()

        if random.random() > self.random_chance:
            return

        self.bot.privmsg(target,
                         '{0}: A direction away from the center of gravity of a celestial object.'.format(mask.nick))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*same$')
    def same(self, target):
        if random.random() > self.random_chance:
            return
        self.bot.privmsg(target, self.bot.format('same', bold=True))
