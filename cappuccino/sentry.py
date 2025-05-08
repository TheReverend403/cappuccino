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
import sentry_sdk
from requests import RequestException
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from cappuccino import Plugin
from cappuccino.util import meta


def _before_send(event, hint):
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, RequestException | TimeoutError):
            return None

    return event


@irc3.plugin
class Sentry(Plugin):
    requires = ["irc3.plugins.command"]

    def __init__(self, bot):
        super().__init__(bot)

        dsn = self.config.get("dsn", None)
        if not dsn:
            self.logger.info("Missing Sentry DSN, Sentry is disabled.")
            return

        sentry_sdk.init(
            dsn,
            before_send=_before_send,
            release=meta.FULL_VERSION,
            integrations=[SqlalchemyIntegration()],
        )
