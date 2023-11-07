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

import irc3
from irc3.plugins.command import command
from requests import RequestException

from cappuccino import Plugin
from cappuccino.util.formatting import Color, style

_RANDOM_CHANCE = 0.33
_DECIDE_DELIMITERS = [" or ", ",", "|"]
# Borrowed from https://github.com/GeneralUnRest/8ball-bot/blob/master/8ball.js
_EIGHTBALL_RESPONSES = [
    "Signs point to yes.",
    "Yes.",
    "Reply hazy, try again.",
    "Without a doubt.",
    "My sources say no.",
    "As I see it, yes.",
    "You may rely on it.",
    "Concentrate and ask again.",
    "Outlook not so good.",
    "It is decidedly so.",
    "Better not tell you now.",
    "Very doubtful.",
    "Yes - definitely.",
    "It is certain.",
    "Cannot predict now.",
    "Most likely.",
    "Ask again later.",
    "My reply is no.",
    "Outlook good.",
    "Don't count on it.",
]


@irc3.plugin
class Fun(Plugin):
    requires = ["irc3.plugins.command", "cappuccino.core"]

    def _reply(self, target: str, message: str):
        # Only reply a certain percentage of the time. AKA rate-limiting. Sort of.
        if random.random() <= _RANDOM_CHANCE:  # noqa: S311
            self.bot.privmsg(target, message)

    @command(permission="view", use_shlex=False)
    def decide(self, mask, target, args):
        """Make the difficult decisions in life.

        %%decide <options>...
        """

        options = " ".join(args["<options>"])
        for delimiter in _DECIDE_DELIMITERS:
            options = options.replace(delimiter, "|")
        options = options.split("|")
        options = list(
            filter(
                None,
                {
                    option.replace(delimiter, "").strip()
                    for delimiter in _DECIDE_DELIMITERS
                    for option in options
                    if option not in _DECIDE_DELIMITERS
                },
            )
        )

        [
            options.remove(delimiter.strip())
            for delimiter in _DECIDE_DELIMITERS
            if delimiter.strip() in options
        ]

        if not options:
            return (
                f"{mask.nick}:"
                f" I can't make a decision for you if you don't give me any choices >:V"
            )

        options_length = len(options)
        if options_length == 1:
            options = ["Yes.", "Maybe.", "No."]

        return f"{mask.nick}: {random.choice(options)}"  # noqa: S311

    @command(permission="view", name="8ball")
    def eightball(self, mask, target, args):
        """Consult the wise and powerful 8 ball.

        %%8ball <query>...
        """

        return f"{mask.nick}: {random.choice(_EIGHTBALL_RESPONSES)}"  # noqa: S311

    @irc3.event(
        r'(?i).*PRIVMSG (?P<target>#\S+) :\s*\[+(?P<data>[A-Za-z0-9-_ \'"!]+)\]+$'
    )
    def intensify(self, target, data):
        max_length = 32
        data = data.strip().upper()
        if not data.endswith("INTENSIFIES"):
            data += " INTENSIFIES"

        if data and len(data) <= max_length:
            self.bot.privmsg(target, style(f"[{data}]", bold=True))

    @irc3.event(r"(?i).*PRIVMSG (?P<target>#\S+) :\s*wew$")
    def wew(self, target):
        self._reply(target, style("w e w l a d", bold=True))

    @irc3.event(r"(?i).*PRIVMSG (?P<target>#\S+) :\s*ayy+$")
    def ayy(self, target):
        self._reply(target, "lmao")

    @irc3.event(r"(?i).*PRIVMSG (?P<target>#\S+) :\s*same$")
    def same(self, target):
        self._reply(target, style("same", bold=True))

    @irc3.event(r"(?i).*PRIVMSG (?P<target>\S+) :\s*benis$")
    def benis(self, target):
        self._reply(target, style("3===D", bold=True))

    @irc3.event(
        r"(?i)^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :.*homo.*"
    )
    def homo(self, target, mask):
        self._reply(target, f"hahahaha {mask.nick} said homo xDDD")

    @irc3.event(
        r"(?i)^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :.*loli.*"
    )
    def loli(self, target, mask):
        link = style("https://pedo.help", fg=Color.BLUE)
        reply = style("[NONCE DETECTED] ", fg=Color.RED)
        reply += f"{mask.nick}, please click for your own good: {link}"
        self._reply(target, reply)

    @irc3.event(irc3.rfc.PRIVMSG)
    def not_the_only_one(self, target, event, mask, data):
        if event != "PRIVMSG" or not target.is_channel:
            return

        if re.match(r"(?i)does any\s?(body|one) else.*", data):
            self.bot.privmsg(
                target, f"{mask.nick}: No, you are literally the only one in the world."
            )
            return

        if re.match(r"(?i)am i the only one.*", data):
            self.bot.privmsg(target, f"{mask.nick}: Statistically, probably not.")
            return

    @irc3.event(
        r"(?i):TrapBot!\S+@\S+ .*PRIVMSG (?P<target>#DontJoinItsATrap) :.*PART THE CHANNEL.*"
    )
    def antitrap(self, target):
        self.bot.part(target)
        self.logger.info(f"Parted {target} (antitrap)")

    @irc3.event(
        r"(?i):(?P<mask>\S+!\S+@\S+) .*PRIVMSG (?P<target>#\S+) :.*(wh?(aa*(z|d)*|u)t?(\'?| i)s? ?up|\'?sup)\b"
    )
    def gravity(self, mask, target):
        self._reply(
            target,
            f'{mask.nick}: "Up" is a direction away from the center of gravity of a celestial object.',
        )

    @command(permission="view", aliases=["whatthecommit"])
    def wtc(self, mask, target, args):
        """Grab a random commit message.

        %%wtc
        """

        try:
            with self.bot.requests.get(
                "https://whatthecommit.com/index.txt"
            ) as response:
                yield f'git commit -m "{response.text.strip()}"'
        except RequestException:
            yield (
                "Failed to fetch a random git commit."
                " Sorry, you'll have to figure one out yourself."
            )
