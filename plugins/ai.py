try:
    import ujson as json
except ImportError:
    import json
import os
import random
import re
import sqlite3

import irc3
import markovify
from irc3.plugins.command import command

CMD_PREFIX_PATTERN = re.compile(r'^\s*(\.|!|~|`|\$)+')
SED_CHECKER = re.compile(r'^\s*s[/|\\!.,\\].+')


@irc3.plugin
class Ai(object):
    requires = [
        'irc3.plugins.userlist',
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.datadir = 'data'
        self.file = os.path.join(self.datadir, 'ai.sqlite')
        self.channel_file = os.path.join(self.datadir, 'ai.json')
        self.active_channels = []

        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
        except KeyError:
            self.ignore_nicks = []

        try:
            with open(self.channel_file, 'r') as fd:
                self.active_channels = json.load(fd)
        except FileNotFoundError:
            if not os.path.exists(self.datadir):
                os.mkdir(self.datadir)
                self.bot.log.debug('Created {0}/ directory'.format(self.datadir))

        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.file)
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS corpus (line TEXT PRIMARY KEY, channel TEXT)')
        self.conn.commit()

    def _add_line(self, line, channel):
        if CMD_PREFIX_PATTERN.match(line) or SED_CHECKER.match(line) or line.startswith('['):
            return

        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO corpus VALUES (?,?)', (line, channel))
        self.conn.commit()

    def _get_lines(self, channel, max_line_count=5000):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM corpus ORDER BY RANDOM() LIMIT ?', (max_line_count,))
        lines = [self.bot.strip_formatting(line[0]) for line in cursor.fetchall()]
        return lines if len(lines) > 0 else None

    def _line_count(self, channel=None):
        cursor = self.conn.cursor()
        if channel:
            cursor.execute('SELECT COUNT(*) FROM corpus WHERE channel=?', (channel,))
        else:
            cursor.execute('SELECT COUNT(*) FROM corpus')
        return cursor.fetchone()[0]

    def is_active(self, channel):
        return channel in self.active_channels

    def toggle(self, channel):
        try:
            self.active_channels.remove(channel)
        except ValueError:
            self.active_channels.append(channel)

        with open(self.channel_file, 'w') as fd:
            json.dump(self.active_channels, fd)

    @command()
    def ai(self, mask, target, args):
        """Toggles chattiness.

            %%ai [--status]
        """

        if args['--status']:
            line_count = self._line_count()
            channel_line_count = self._line_count(target)
            channel_percentage = 0

            # Percentage of global lines the current channel accounts for.
            if channel_line_count >= 0 and line_count >= 0:
                channel_percentage = int(round(100 * float(channel_line_count) / float(line_count), ndigits=0))

            return 'Chatbot is currently {0} for {3}. Channel/global line count: {2}/{1} ({4}%).'.format(
                'enabled' if self.is_active(target) else 'disabled',
                line_count, channel_line_count, target, channel_percentage)

        privmodes = ['@', '&', '~', '%']
        is_op = False
        for mode in privmodes:
            try:
                if mask.nick in self.bot.channels[target].modes[mode]:
                    is_op = True
                    break
            except (KeyError, AttributeError):
                continue

        if not is_op:
            return 'You must have one of the following modes to do that: {0}'.format(', '.join(privmodes))

        self.toggle(target)
        return 'Chatbot activated.' if self.is_active(target) else 'Shutting up!'

    @irc3.event(r'.*:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<channel>#\S+) :\s*(?P<data>\S+.*)$')
    def handle_line(self, mask, channel, data):
        data = data.strip()
        if not data:
            return

        if mask.nick in self.ignore_nicks:
            return

        if not data.lower().startswith(self.bot.nick.lower()):
            self._add_line(data, channel)

        if not self.is_active(channel):
            return

        # Only respond to messages mentioning the bot
        if not self.bot.nick.lower() in data.lower():
            return

        corpus = self._get_lines(channel)
        if not corpus:
            self.bot.log.warning('Not enough lines in corpus for markovify to generate a decent reply.')
            return

        text_model = markovify.NewlineText('\n'.join(corpus))
        generated_reply = text_model.make_short_sentence(140)
        if not generated_reply:
            self.bot.privmsg(channel, random.choice(['What?', 'Hmm?', 'Yes?', 'What do you want?']))
            return

        self.bot.privmsg(channel, generated_reply.strip())
