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
        self.muted = True

        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
        except KeyError:
            self.ignore_nicks = []

        try:
            self.channel = self.bot.config[__name__]['channel']
        except KeyError:
            self.channel = None

        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.file)
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS corpus (line TEXT PRIMARY KEY)')
        self.conn.commit()

    def _add_line(self, line):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO corpus VALUES (?)', (line,))
        self.conn.commit()

    def _get_lines(self, line_count=5000):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM corpus ORDER BY RANDOM() LIMIT ?', (line_count,))
        lines = [line[0] for line in cursor.fetchall()]
        return lines if len(lines) >= line_count else None

    @command(permission='admin', show_in_help_list=False)
    def shutup(self, mask, target, args):
        """Toggles chattiness.

            %%shutup
        """
        self.muted = not self.muted
        return 'Shutting up!' if self.muted else 'Unmuted!'

    @irc3.event(r'.*:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<channel>#\S+) :\s*(?P<data>\S+.*)$')
    def handle_line(self, mask, channel, data):
        if not self.channel or channel.lower() != '#' + self.channel:
            return
        data = data.strip()
        if not data:
            return
        if CMD_PREFIX_PATTERN.match(data) or mask.nick in self.ignore_nicks:
            return
        if not data.lower().startswith(self.bot.nick.lower()):
            self._add_line(data)
        if self.muted:
            return
        if self.bot.nick.lower() in data.lower():
            corpus = self._get_lines()
            if not corpus:
                self.bot.log.warning('Not enough lines in corpus for markovify to generate a decent reply. '
                                     'Consider running import.py to import lines from a text file.')
                return
            text_model = markovify.NewlineText('\n'.join(corpus))
            generated_reply = text_model.make_short_sentence(140)
            if not generated_reply:
                self.bot.privmsg(channel, random.choice(['What?', 'Hmm?', 'Yes?', 'What do you want?']))
                return
            self.bot.privmsg(channel, generated_reply.strip())
