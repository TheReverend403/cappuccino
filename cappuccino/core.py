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

from random import randint

import irc3
import requests
from requests import Session
from requests.cookies import RequestsCookieJar

from cappuccino import Plugin
from cappuccino.util import meta


@irc3.plugin
class Core(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        requests.packages.urllib3.disable_warnings()

        # Accept YouTube consent cookies automatically
        cookie_jar = RequestsCookieJar()
        cookie_value = f"YES+srp.gws-20210512-0-RC3.en+FX+{randint(1, 1000)}"  # noqa: S311
        cookie_jar.set("CONSENT", cookie_value)

        self.bot.requests = Session()
        self.bot.requests.cookies = cookie_jar
        self.bot.requests.headers.update(
            {
                "User-Agent": f"cappuccino {meta.VERSION} - {meta.SOURCE}",
                "Accept-Language": "en-GB,en-US,en;q=0.5",
                "timeout": "5",
                "allow_redirects": "true",
            }
        )
