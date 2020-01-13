#  This file is part of cappuccino.
#
#  cappuccino is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cappuccino is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cappuccino.  If not, see <https://www.gnu.org/licenses/>.

import os
import random
import re

import irc3
import markovify
from irc3.plugins.command import command
from sqlalchemy import Boolean, Column, MetaData, String, Table, create_engine, func, select
from sqlalchemy.exc import IntegrityError

CMD_PATTERN = re.compile(r'^\s*([.!~`$])+')
SED_CHECKER = re.compile(r"^\s*s[/|\\!.,].+")
URL_CHECKER = re.compile(r'.*https?://.*', re.IGNORECASE | re.UNICODE)


def should_ignore_message(line):
    if not line:
        return

    return CMD_PATTERN.match(line) or \
        SED_CHECKER.match(line) or \
        URL_CHECKER.match(line) or \
        line.startswith('[') or \
        line.startswith('\x01ACTION ')


@irc3.plugin
class Ai(object):
    requires = [
        'plugins.botui',
        'plugins.formatting'
    ]

    metadata = MetaData()
    corpus = Table('ai_corpus', metadata, Column('line', String, primary_key=True), Column('channel', String))
    channels = Table('ai_channels', metadata, Column('name', String, primary_key=True), Column('status', Boolean))

    def __init__(self, bot):
        self.bot = bot
        self.ignore_nicks = []
        self.max_loaded_lines = 10000
        self.db = create_engine(self.bot.config[__name__]['database'])

        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
            self.max_loaded_lines = self.bot.config[__name__]['max_loaded_lines']
        except KeyError:
            pass

        self.metadata.create_all(self.db)
        self.migrate()

    def _add_line(self, line: str, channel: str):
        try:
            insert_stmt = self.corpus.insert().values(line=self.bot.strip_formatting(line), channel=channel)
            self.db.execute(insert_stmt)
        except IntegrityError:
            pass

    def _get_lines(self, channel: str = None) -> list:
        select_stmt = select([self.corpus.c.line])
        if channel:
            select_stmt = select_stmt.where(self.corpus.c.channel == channel)\
                .order_by(func.random()).limit(self.max_loaded_lines)
        else:
            select_stmt = select_stmt.order_by(func.random()).limit(self.max_loaded_lines)

        lines = [result.line for result in self.db.execute(select_stmt)]
        return lines if len(lines) > 0 else None

    def _line_count(self, channel: str = None) -> int:
        select_stmt = select([func.count(self.corpus.c.line)])
        if channel:
            select_stmt = select_stmt.where(self.corpus.c.channel == channel)

        return self.db.execute(select_stmt).scalar()

    def is_active(self, channel: str) -> bool:
        if not channel.startswith('#'):
            return False

        select_stmt = select([self.channels.c.status]).where(self.channels.c.name == channel)
        result = self.db.execute(select_stmt).scalar()

        if result is None:
            insert_stmt = self.channels.insert().values(name=channel, status=0)
            self.db.execute(insert_stmt)
            return False

        return result

    def toggle(self, channel: str):
        if self.is_active(channel):
            update_stmt = self.channels.update().where(self.channels.c.name == channel).values(status=0)
        else:
            update_stmt = self.channels.update().where(self.channels.c.name == channel).values(status=1)

        self.db.execute(update_stmt)

    def migrate(self):
        if not str(self.db.url).startswith('sqlite://') and os.path.exists('data/ai.sqlite'):
            self.bot.log.info('Found ai.sqlite, migrating data.')
            sqlite_db = create_engine('sqlite:///data/ai.sqlite')
            formatting_codes_regex = re.compile(r'.*\x1f|\x02|\x1D|\x03.*', re.UNICODE)

            corpus_results = sqlite_db.execute('SELECT * FROM corpus')
            channel_results = sqlite_db.execute('SELECT * FROM channels')
            corpus_insert = self.corpus.insert(). \
                values([
                    {'line': row[0], 'channel': row[1]}
                    for row in corpus_results if not formatting_codes_regex.match(row[0])
                ])

            channels_insert = self.channels.insert(). \
                values([
                    {'name': row[0], 'status': row[1]} for row in channel_results
                ])

            try:
                self.db.execute(channels_insert)
                self.db.execute(corpus_insert)
            except IntegrityError:
                pass

            self.bot.log.info('Migration complete, renaming old sqlite database.')
            os.rename('data/ai.sqlite', 'data/ai.sqlite.bak')

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
            if channel_line_count > 0 and line_count > 0:
                channel_percentage = int(round(100 * float(channel_line_count) / float(line_count), ndigits=0))

            ai_status = 'enabled' if self.is_active(target) else 'disabled'
            return f'Chatbot is currently {ai_status} for {target}. ' \
                   f'Channel/global line count: {channel_line_count}/{line_count} ({channel_percentage}%).'

        if not self.bot.is_chanop(target, mask.nick):
            prefixes = [prefix.value for prefix in self.bot.nickprefix if prefix is not self.bot.nickprefix.VOICE]
            op_prefixes = ', '.join(prefixes)

            return f'You must be a channel operator ({op_prefixes}) to do that.'

        self.toggle(target)
        return 'Chatbot activated.' if self.is_active(target) else 'Shutting up!'

    @irc3.event(irc3.rfc.PRIVMSG)
    def handle_line(self, target, event, mask, data):
        if not target.is_channel:
            return

        channel = target
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
