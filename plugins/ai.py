import random
import re
import sqlite3

import irc3
import markovify
import os
from irc3.plugins.command import command

CMD_PREFIX_PATTERN = re.compile(r'^\s*(\.|!|~|`|\$)+')


@irc3.plugin
class Ai(object):

    def __init__(self, bot):
        self.bot = bot
        self.file = os.path.join('data', 'ai.sqlite')
        self.active_channels = []

        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
        except KeyError:
            self.ignore_nicks = []

        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.file)
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS corpus (line TEXT PRIMARY KEY, channel TEXT)')
        self.conn.commit()

    def _add_line(self, line, channel):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO corpus VALUES (?,?)', (line, channel))
        self.conn.commit()

    def _get_lines(self, channel, line_count=1000):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM corpus WHERE channel=? ORDER BY RANDOM() LIMIT ?', (channel, line_count))
        lines = [line[0] for line in cursor.fetchall()]
        return lines if len(lines) >= line_count else None

    def is_active(self, channel):
        return channel in self.active_channels

    def toggle(self, channel):
        try:
            self.active_channels.remove(channel)
        except ValueError:
            self.active_channels.append(channel)

    @command()
    def ai(self, mask, target, args):
        """Toggles chattiness.

            %%ai [--status]
        """

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
            return '{0}: You must have one of the following modes to use this command: {1}'.format(
                mask.nick, ', '.join(privmodes))

        if args['--status']:
            return '{0}: Chatbot is currently {1}.'.format(
                mask.nick, 'enabled' if self.is_active(target) else 'disabled')

        self.toggle(target)
        return 'Chatbot activated.' if self.is_active(target) else 'Shutting up!'

    @irc3.event(r'.*:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<channel>#\S+) :\s*(?P<data>\S+.*)$')
    def handle_line(self, mask, channel, data):
        data = data.strip()
        if not data:
            return

        if CMD_PREFIX_PATTERN.match(data) or mask.nick in self.ignore_nicks:
            return

        if not data.lower().startswith(self.bot.nick.lower()):
            self._add_line(data, channel)

        if not self.is_active(channel):
            return

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
