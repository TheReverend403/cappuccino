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

import random
import re
from datetime import datetime
from timeit import default_timer as timer

import irc3
import markovify
from humanize import intcomma, precisedelta
from irc3.plugins.command import command
from irc3.utils import IrcString
from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError

from cappuccino import Plugin
from cappuccino.util.channel import is_chanop
from cappuccino.util.database import Database
from cappuccino.util.formatting import unstyle

_CMD_PATTERN = re.compile(r"^\s*([.!~`$])+")
_SED_CHECKER = re.compile(r"^\s*s[/|\\!.,].+")
_URL_CHECKER = re.compile(r".*https?://.*", re.IGNORECASE | re.UNICODE)


def _should_ignore_message(line):
    if not line:
        return

    return (
        _CMD_PATTERN.match(line)
        or _SED_CHECKER.match(line)
        or _URL_CHECKER.match(line)
        or line.startswith("[")
        or line.startswith("\x01ACTION ")
    )


@irc3.plugin
class Ai(Plugin):
    requires = ["irc3.plugins.command", "irc3.plugins.userlist"]

    def __init__(self, bot):
        super().__init__(bot)
        self._ignore_nicks: list[str] = self.config.get("ignore_nicks", [])
        self._max_loaded_lines: int = self.config.get("max_loaded_lines", 25000)
        self._max_reply_length: int = self.config.get("max_reply_length", 100)

        self._db = Database(self)
        self._corpus = self._db.meta.tables["ai_corpus"]
        self._channels = self._db.meta.tables["ai_channels"]
        self._text_model = self._create_text_model()

    def _create_text_model(self):
        self.logger.info("Creating text model...")
        start = datetime.now()
        corpus = self._get_lines()
        end = datetime.now()

        if not corpus:
            self.logger.warning(
                "Not enough lines in corpus for markovify to generate a decent reply."
            )
            return

        self.logger.debug(f"Queried {len(corpus)} rows in {precisedelta(end - start)}.")

        start = datetime.now()
        model = markovify.NewlineText(
            "\n".join(corpus), retain_original=False
        ).compile()
        end = datetime.now()
        self.logger.info(f"Created text model in {precisedelta(start - end)}.")

        return model

    def _add_line(self, line: str, channel: str):
        try:
            insert_stmt = insert(self._corpus).values(
                line=unstyle(line), channel=channel
            )
            self._db.execute(insert_stmt)
        except IntegrityError:
            pass

    def _get_lines(self, channel: str = None) -> list:
        select_stmt = select([self._corpus.c.line])
        if channel:
            select_stmt = (
                select_stmt.where(func.lower(self._corpus.c.channel) == channel.lower())
                .order_by(func.random())
                .limit(self._max_loaded_lines)
            )
        else:
            select_stmt = select_stmt.order_by(func.random()).limit(
                self._max_loaded_lines
            )

        lines = [result.line for result in self._db.execute(select_stmt)]
        return lines if len(lines) > 0 else None

    def _line_count(self, channel: str = None) -> int:
        select_stmt = select([func.count(self._corpus.c.line)])
        if channel:
            select_stmt = select_stmt.where(
                func.lower(self._corpus.c.channel) == channel.lower()
            )

        return self._db.execute(select_stmt).scalar()

    def _is_active(self, channel: str) -> bool:
        if not IrcString(channel).is_channel:
            return False

        select_stmt = (
            select([self._channels.c.status])
            .join(self._corpus)
            .where(func.lower(self._corpus.c.channel) == channel.lower())
        )
        result = self._db.execute(select_stmt).scalar()

        if result is None:
            insert_stmt = insert(self._channels).values(name=channel, status=0)
            self._db.execute(insert_stmt)
            return False

        return result

    def _toggle(self, channel: str):
        new_status = int(not self._is_active(channel))
        update_stmt = (
            update(self._channels)
            .where(func.lower(self._corpus.c.channel) == channel.lower())
            .values(status=new_status)
        )

        self._db.execute(update_stmt)

    @command()
    def ai(self, mask, target, args):
        """Toggles chattiness.

        %%ai [--status]
        """

        if not target.is_channel:
            return "This command cannot be used in PM."

        if args["--status"]:
            line_count = self._line_count()
            channel_line_count = self._line_count(target)
            channel_percentage = 0

            # Percentage of global lines the current channel accounts for.
            if channel_line_count > 0 and line_count > 0:
                channel_percentage = int(
                    round(
                        100 * float(channel_line_count) / float(line_count), ndigits=0
                    )
                )

            ai_status = "enabled" if self._is_active(target) else "disabled"
            line_counts = f"{intcomma(channel_line_count)}/{intcomma(line_count)}"
            return (
                f"Chatbot is currently {ai_status} for {target}."
                f" Channel/global line count: {line_counts} ({channel_percentage}%)."
            )

        if not is_chanop(self.bot, target, mask.nick):
            prefixes = [
                prefix.value
                for prefix in self.bot.nickprefix
                if prefix is not self.bot.nickprefix.VOICE
            ]
            op_prefixes = ", ".join(prefixes)

            return f"You must be a channel operator ({op_prefixes}) to do that."

        self._toggle(target)
        return "Chatbot activated." if self._is_active(target) else "Shutting up!"

    @irc3.event(irc3.rfc.PRIVMSG)
    def handle_line(self, target, event, mask, data):
        if not target.is_channel or not mask.is_user:
            return

        if mask.nick in self._ignore_nicks or mask.nick == self.bot.nick:
            return

        data = data.strip()
        if _should_ignore_message(data):
            return

        # Only respond to messages mentioning the bot in an active channel
        if self.bot.nick.lower() not in data.lower():
            # Only add lines that aren't mentioning the bot
            self._add_line(data, target)
            return

        if not self._is_active(target):
            return

        start = timer()
        generated_reply = self._text_model.make_short_sentence(self._max_reply_length)
        end = timer()
        self.logger.debug(
            f"Generating sentence took {(end - start) * 1000} milliseconds."
        )

        if not generated_reply:
            self.bot.privmsg(
                target, random.choice(["What?", "Hmm?", "Yes?", "What do you want?"])
            )
            return

        self.bot.privmsg(target, generated_reply.strip())
