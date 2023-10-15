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

import subprocess

import irc3
import requests
from irc3.plugins.command import command

from cappuccino import Plugin


def _is_multiline_string(text: str):
    # require minimum 2 newlines to account for the newline at the end of output.
    return text.count("\n") > 1


def _exec_wrapper(cmd: dict, input_data: str | None = None) -> str:
    if input_data:
        input_data = input_data.encode("UTF-8")

    proc = subprocess.run(
        cmd,  # noqa: S603
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=5,
    )
    return proc.stdout.decode("UTF-8").strip()


@irc3.plugin
class ExecShell(Plugin):
    requires = ["irc3.plugins.command", "cappuccino.core"]

    @command(
        permission="admin", show_in_help_list=False, options_first=True, use_shlex=True
    )
    def exec(self, mask, target, args):  # noqa: A003
        """Run a system command and upload the output to ix.io.

        %%exec <command>...
        """

        try:
            output = _exec_wrapper(args["<command>"])
            if not output:
                return f"{mask.nick}: Command returned no output."

            # Don't paste single line outputs.
            if not _is_multiline_string(output):
                return f"{mask.nick}: {output}"

            # Upload multiline output to ix.io to avoid flooding channels.
            result = self.bot.requests.post("http://ix.io", data={"f:1": output})

        except (
            FileNotFoundError,
            requests.RequestException,
            subprocess.TimeoutExpired,
        ) as ex:
            return f"{mask.nick}: {ex}"

        return f"{mask.nick}: {result.text}"
