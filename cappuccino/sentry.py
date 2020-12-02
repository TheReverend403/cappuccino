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

import logging

import irc3
import sentry_sdk
from irc3.plugins.command import command
from requests import RequestException
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

log = logging.getLogger(__name__)


def _before_send(event, hint):
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, (RequestException, TimeoutError)):
            return None

    return event


@irc3.plugin
class Sentry(object):
    requires = ["irc3.plugins.command", "cappuccino.botui"]

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.get(__name__, {})

        dsn = self.config.get("dsn", None)
        if not dsn:
            log.warning("Missing Sentry DSN")
        else:
            sentry_sdk.init(
                dsn,
                before_send=_before_send,
                release=self.bot.version,
                integrations=[SqlalchemyIntegration()],
            )

    @command(name="testsentry", permission="admin", show_in_help_list=False)
    def testsentry(self, mask, target, args):
        """Force an exception to test Sentry.

        %%testsentry
        """
        raise Exception("Sentry test")
