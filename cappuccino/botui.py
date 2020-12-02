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

import platform
import subprocess

import irc3
import requests
from irc3.plugins.command import command
from requests import Session


@irc3.plugin
class BotUI(object):
    requires = ["irc3.plugins.command", "irc3.plugins.userlist"]

    def __init__(self, bot):
        self.bot = bot
        self.bot.version = (
            subprocess.check_output(["git", "describe"]).decode("UTF-8").strip()
        )
        requests.packages.urllib3.disable_warnings()
        self.bot.requests = Session()
        self.bot.requests.headers.update(
            {
                "User-Agent": "cappuccino (https://github.com/FoxDev/cappuccino)",
                "Accept-Language": "en-GB,en-US,en;q=0.5",
                "timeout": "5",
                "allow_redirects": "true",
            }
        )

    @command(permission="view", aliases=["source", "version"])
    def bots(self, mask, target, args):
        """Report in!

        %%bots
        """
        pyver = platform.python_version()
        yield (
            f"Reporting in! [cappuccino {self.bot.version}, Python {pyver}] "
            f"https://github.com/FoxDev/cappuccino"
        )

    @command(permission="admin", show_in_help_list=False)
    def join(self, mask, target, args):
        """Join a channel.

        %%join <channel> [<password>]
        """

        channel = args["<channel>"]
        if args["<password>"]:
            channel += f' {args["<password>"]}'

        self.bot.join(channel)

    @command(permission="admin", show_in_help_list=False)
    def part(self, mask, target, args):
        """Leave a channel.

        %%part [<channel>]
        """

        if args["<channel>"]:
            target = args["<channel>"]

        self.bot.part(target)

    @command(permission="admin", show_in_help_list=False)
    def quit(self, mask, target, args):
        """Shut the bot down.

        %%quit
        """

        self.bot.quit()

    @command(permission="admin", show_in_help_list=False)
    def nick(self, mask, target, args):
        """Change nickname of the bot.

        %%nick <nick>
        """

        self.bot.set_nick(args["<nick>"])

    @command(permission="admin", show_in_help_list=False)
    def mode(self, mask, target, args):
        """Set user mode for the bot.

        %%mode <mode-cmd>
        """

        self.bot.mode(self.bot.nick, args["<mode-cmd>"])

    @command(permission="admin", show_in_help_list=False)
    def msg(self, mask, target, args):
        """Send a message.

        %%msg <target> <message>...
        """

        msg = " ".join(args["<message>"] or [])
        self.bot.privmsg(args["<target>"], msg)

    @command(permission="admin", aliases=["bc", "broadcast"], show_in_help_list=False)
    def psa(self, mask, target, args):
        """Broadcast a message to all channels.

        %%psa <message>...
        """
        message = " ".join(args["<message>"])
        for channel in self.bot.channels:
            self.bot.privmsg(channel, f"[PSA] {message}")

    @command(permission="view")
    def ping(self, mask, target, args):
        """Ping!

        %%ping
        """
        self.bot.privmsg(target, f"{mask.nick}: Pong!")
