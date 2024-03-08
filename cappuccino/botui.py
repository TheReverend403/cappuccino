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


import irc3
from irc3.plugins.command import command

from cappuccino import Plugin
from cappuccino.util import meta


@irc3.plugin
class BotUI(Plugin):
    requires = ["irc3.plugins.command", "irc3.plugins.userlist"]

    @command(permission="view", aliases=["source", "version"])
    def bots(self, mask, target, args):
        """Report in!

        %%bots
        """
        yield f"Reporting in! [cappuccino {meta.VERSION}] - {meta.SOURCE}"

    @command(permission="admin", show_in_help_list=False)
    def join(self, mask, target, args):
        """Join a channel.

        %%join <channel> [<password>]
        """

        channel = args["<channel>"]
        if args["<password>"]:
            channel += f' {args["<password>"]}'

        self.bot.join(channel)
        self.logger.info(f"Joined {channel}")

    @command(permission="admin", show_in_help_list=False)
    def part(self, mask, target, args):
        """Leave a channel.

        %%part [<channel>]
        """

        if args["<channel>"]:
            target = args["<channel>"]

        self.bot.part(target)
        self.logger.info(f"Parted {target}")

    @command(permission="admin", show_in_help_list=False)
    def quit(self, mask, target, args):
        """Shut the bot down.

        %%quit
        """

        self.logger.info(f"Shutting down as requested by {mask}")
        self.bot.quit()

    @command(permission="admin", show_in_help_list=False)
    def nick(self, mask, target, args):
        """Change nickname of the bot.

        %%nick <nick>
        """

        nick = args["<nick>"]
        self.bot.set_nick(nick)
        self.logger.info(f"Changed nick to {nick}")

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
        self.logger.info(f"Sent PSA requested by {mask}: {message}")

    @command(permission="view")
    def ping(self, mask, target, args):
        """Ping!

        %%ping
        """
        self.bot.privmsg(target, f"{mask.nick}: Pong!")
