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
import os
from secrets import randbelow

import requests
from requests import Session
from requests.cookies import RequestsCookieJar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cappuccino.util import meta


def _create_requests_session() -> Session:
    requests.packages.urllib3.disable_warnings()

    # Accept YouTube consent cookies automatically
    cookie_jar = RequestsCookieJar()
    cookie_value = f"YES+srp.gws-20210512-0-RC3.en+FX+{1 + randbelow(1000)}"
    cookie_jar.set("CONSENT", cookie_value)

    session = Session()
    session.cookies = cookie_jar
    session.headers.update(
        {
            "User-Agent": f"cappuccino {meta.VERSION} - {meta.SOURCE}",
            "Accept-Language": "en-GB,en-US,en;q=0.5",
            "timeout": "5",
            "allow_redirects": "true",
        }
    )
    return session


class Plugin:
    def __init__(self, bot):
        plugin_module = self.__class__.__module__
        self.bot = bot
        self.config: dict = self.bot.config.get(plugin_module, {})
        self.logger = logging.getLogger(f"irc3.{plugin_module}")
        self.requests = _create_requests_session()

        db_config = self.bot.config.get("database", {})
        db = create_engine(
            db_config.get("uri"),
            pool_size=db_config.get("pool_size", os.cpu_count()),
            max_overflow=db_config.get("max_overflow", os.cpu_count()),
        )
        self.db_session = sessionmaker(db)

        if self.config:
            # I have no idea where these are coming from but whatever.
            weird_keys = ["#", "hash"]
            for key in weird_keys:
                if key in self.config:
                    self.config.pop(key)

            self.logger.debug(f"Configuration for {plugin_module}: {self.config}")
