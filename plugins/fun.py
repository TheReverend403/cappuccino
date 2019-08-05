import re

import irc3
import random

from irc3.plugins.command import command

USER_AGENT = 'cappuccino (https://github.com/FoxDev/cappuccino)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
}

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

    random_chance = 0.2

    def __init__(self, bot):
        self.bot = bot

    def reply(self, target: str, message: str):
        # Only reply a certain percentage of the time. AKA rate-limiting. Sort of.
        if random.random() <= self.random_chance:
            self.bot.privmsg(target, message)

    @command(permission='view', use_shlex=False)
    def decide(self, mask, target, args):
        """Make the difficult decisions in life.

            %%decide <options>...
        """

        options = ' '.join(args['<options>'])
        for delimiter in DECIDE_DELIMITERS:
            options = options.replace(delimiter, '|')
        options = options.split('|')
        options = list(filter(None, set(option.replace(delimiter, '').strip()
                                        for delimiter in DECIDE_DELIMITERS
                                        for option in options
                                        if option not in DECIDE_DELIMITERS)))

        [options.remove(delimiter.strip()) for delimiter in DECIDE_DELIMITERS if delimiter.strip() in options]
        self.bot.log.debug(f'Parsed options: {options}')

        if not options:
            return f'{mask.nick}: I can\'t make a decision for you if you don\'t give me any choices >:V'

        options_length = len(options)
        if options_length == 1:
            options = ['Yes.', 'Maybe.', 'No.']

        return f'{mask.nick}: {random.choice(options)}'

    @command(permission='view', name='8ball')
    def eightball(self, mask, target, args):
        """Consult the wise and powerful 8 ball.

            %%8ball <query>...
        """

        return f'{mask.nick}: {random.choice(EIGHTBALL_RESPONSES)}'

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*\[(?P<data>[A-Za-z0-9-_ \'"!]+)\]$')
    def intensify(self, target, data):
        data = data.strip()
        if data and len(data) <= 32:
            self.bot.privmsg(target, self.bot.format(f'[{data.upper()} INTENSIFIES]', bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*wew$')
    def wew(self, target):
        self.reply(target, self.bot.format('w e w l a d', bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*ayy+$')
    def ayy(self, target):
        self.reply(target, 'lmao')

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)\s*same$')
    def same(self, target):
        self.reply(target, self.bot.format('same', bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>\S+) :(?i)\s*benis$')
    def benis(self, target):
        self.reply(target, self.bot.format('3===D', bold=True))

    @irc3.event(r'.*PRIVMSG (?P<target>\S+) :(?i).*loli.*')
    def loli(self, target):
        self.reply(target, self.bot.format('https://pedo.help'))

    @irc3.event(irc3.rfc.PRIVMSG)
    def not_the_only_one(self, target, event, mask, data):
        if event != 'PRIVMSG' or not target.is_channel:
            return

        if re.match(r'(?i)does any\s?(body|one) else.*', data):
            self.bot.privmsg(target, f'{mask.nick}: No, you are literally the only one in the world.')
            return

        if re.match(r'(?i)am i the only one.*', data):
            self.bot.privmsg(target, f'{mask.nick}: Statistically, probably not.')
            return

    @irc3.event(r':TrapBot!\S+@\S+ .*PRIVMSG (?P<target>#(?i)DontJoinItsATrap) :.*PART THE CHANNEL.*')
    def antitrap(self, target):
        self.bot.log.info('Parting {0}'.format(target))
        self.bot.part(target)
