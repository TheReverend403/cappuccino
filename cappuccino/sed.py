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

import re
import subprocess
from collections import deque

import irc3

from cappuccino import Plugin
from cappuccino.util.formatting import Color, style

_SED_PRIVMSG = r"\s*s[/|\\!\.,\\].+"
_SED_CHECKER = re.compile("^" + _SED_PRIVMSG)


def _sed_wrapper(text: str, command: str) -> str:
    # Must be GNU sed
    arguments = ["sed", "--sandbox", "--regexp-extended", command]
    sed_input = text.strip().encode("UTF-8")
    sed = subprocess.run(  # noqa: S603
        arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        input=sed_input,
        check=False,
    )
    stream = sed.stdout.decode("UTF-8").strip()

    if sed.returncode != 0:
        if not stream:
            return "Unknown sed error."
        raise EditorError(stream.replace("sed: -e ", ""))

    return stream


def _edit(text: str, command: str) -> str:
    output = _sed_wrapper(text, command)
    if not output or output == text:
        return text
    return output


class EditorError(Exception):
    """An error occurred while processing the editor command."""


@irc3.plugin
class Sed(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self._history_buffer: dict[str, deque[tuple[str, str]]] = {}

    @irc3.event(irc3.rfc.PRIVMSG)
    def update_chat_history(self, target, event, mask, data):
        if (
            event != "PRIVMSG"
            or _SED_CHECKER.match(data)
            or data.startswith(self.bot.config.cmd)
        ):
            return

        # Strip ACTION data and just use the message.
        data = data.replace("\x01ACTION ", "").replace("\x01", "")
        line = (mask.nick, data)

        if target in self._history_buffer:
            self._history_buffer[target].append(line)
            return

        queue = deque(maxlen=25)
        queue.append(line)
        self._history_buffer.update({target: queue})

    @irc3.event(
        rf":(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :(?P<command>{_SED_PRIVMSG})"
    )
    def sed(self, mask, target, command):
        if target not in self._history_buffer:
            return

        for target_user, message in reversed(self._history_buffer[target]):
            message = message.strip()
            try:
                new_message = _edit(message, command)
            except EditorError as error:
                self.bot.notice(mask.nick, str(error))
                # Don't even check the rest if the sed command is invalid.
                return

            if not new_message or new_message == message:
                continue

            # Prevent spam.
            max_extra_chars = 32
            max_len = len(message) + max_extra_chars
            max_len_hard = 256
            error_msg = (
                "Replacement would be too long."
                " I won't post it to prevent potential spam."
            )
            if (
                len(new_message) > len(error_msg) and len(new_message) > max_len
            ) or len(new_message) > max_len_hard:
                self.bot.notice(mask.nick, style(error_msg, fg=Color.RED))
                return

            emphasised_meant = style("meant", bold=True)
            if mask.nick == target_user:
                if target.is_channel:
                    prefix = f"{mask.nick} {emphasised_meant} to say:"
                else:
                    self.bot.privmsg(mask.nick, new_message)
                    return
            else:
                prefix = f"{mask.nick} thinks {target_user} {emphasised_meant} to say:"
            self.bot.privmsg(target, f"{prefix} {new_message}")
            return
