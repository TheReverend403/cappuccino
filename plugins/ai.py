try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
import random
import re
import sqlite3

import irc3
import markovify
from irc3.plugins.command import command

CMD_PATTERN = re.compile(r'^\s*(\.|!|~|`|\$)+')
SED_CHECKER = re.compile(r'^\s*s[/|\\!.,\\].+')


def should_ignore_message(line):
    if not line:
        return

    return CMD_PATTERN.match(line) or SED_CHECKER.match(line) or line.startswith('[') or line.startswith('\x01ACTION ')


@irc3.plugin
class Ai(object):
    requires = [
        'plugins.botui',
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.datadir = Path('data')
        self.database = self.datadir / 'ai.sqlite'
        self.db_conn = None
        self.ignore_nicks = []
        self.max_loaded_lines = 20000

        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
        except KeyError:
            pass

        try:
            self.max_loaded_lines = self.bot.config[__name__]['max_loaded_lines']
        except KeyError:
            pass

        if not self.database.exists():
            self.datadir.mkdir(exist_ok=True)
            self.bot.log.debug(f'Created {self.datadir} directory')

        self._init_db()

    def _init_db(self):
        self.db_conn = sqlite3.connect(self.database)
        cursor = self.db_conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS corpus (line TEXT PRIMARY KEY, channel TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS channels (name TEXT UNIQUE NOT NULL, status INT DEFAULT 0)')
        self.db_conn.commit()

    def _add_line(self, line, channel):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO corpus VALUES (?,?)', (line, channel))
        self.db_conn.commit()

    def _get_lines(self, channel=None):
        cursor = self.db_conn.cursor()
        if channel:
            cursor.execute('SELECT * FROM corpus WHERE channel=? ORDER BY RANDOM() LIMIT ?',
                           (channel, self.max_loaded_lines))
        else:
            cursor.execute('SELECT * FROM corpus ORDER BY RANDOM() LIMIT ?', (self.max_loaded_lines,))

        lines = [self.bot.strip_formatting(line[0]) for line in cursor.fetchall()]
        return lines if len(lines) > 0 else None

    def _line_count(self, channel=None):
        cursor = self.db_conn.cursor()
        if channel:
            cursor.execute('SELECT COUNT(*) FROM corpus WHERE channel=?', (channel,))
        else:
            cursor.execute('SELECT COUNT(*) FROM corpus')
        return cursor.fetchone()[0]

    def is_active(self, channel):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT status FROM channels WHERE name=?', (channel,))
        result = cursor.fetchone()
        if not result:
            cursor.execute('INSERT INTO channels VALUES (?,?)', (channel, False))
            self.db_conn.commit()
            return False
        return result[0]

    def toggle(self, channel):
        cursor = self.db_conn.cursor()
        if self.is_active(channel):
            cursor.execute('UPDATE channels SET status=0 WHERE name=?', (channel,))
        else:
            cursor.execute('UPDATE channels SET status=1 WHERE name=?', (channel,))
        self.db_conn.commit()

    @command
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

            ai_status = 'enabled' if self.is_active(target) else 'disabled'
            return f'Chatbot is currently {ai_status} for {target}.' \
                   f'Channel/global line count: {channel_line_count}/{line_count} ({channel_percentage}%).'

        if not self.bot.is_chanop(target, mask.nick):
            prefixes = [prefix.value for prefix in self.bot.nickprefix if prefix is not self.bot.nickprefix.VOICE]
            op_prefixes = ', '.join(prefixes)

            return f'You must be a channel operator ({op_prefixes}) to do that.'

        self.toggle(target)
        return 'Chatbot activated.' if self.is_active(target) else 'Shutting up!'

    @irc3.event(r'.*:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<channel>#\S+) :\s*(?P<data>\S+.*)$')
    def handle_line(self, mask, channel, data):
        if mask.nick in self.ignore_nicks or mask.nick == self.bot.nick:
            return

        data = data.strip()
        if should_ignore_message(data):
            return

        # Only respond to messages mentioning the bot in an active channel
        if self.bot.nick.lower() not in data.lower():
            # Only add lines that aren't mentioning the bot
            self._add_line(data, channel)
            return

        if not self.is_active(channel):
            return

        corpus = self._get_lines()
        if not corpus:
            self.bot.log.warning('Not enough lines in corpus for markovify to generate a decent reply.')
            return

        text_model = markovify.NewlineText('\n'.join(corpus))
        generated_reply = text_model.make_short_sentence(100)
        if not generated_reply:
            self.bot.privmsg(channel, random.choice(['What?', 'Hmm?', 'Yes?', 'What do you want?']))
            return

        self.bot.privmsg(channel, generated_reply.strip())
