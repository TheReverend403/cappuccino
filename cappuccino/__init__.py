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
from logging.config import dictConfig
from pathlib import Path
from secrets import randbelow

import requests
import yaml
from requests import Session
from requests.cookies import RequestsCookieJar

from cappuccino.util import meta

DEFAULT_LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
    },
    "root": {
        "handlers": ["default"],
        "level": "INFO",
    },
    "loggers": {
        "irc3": {"handlers": ["default"], "propagate": False},
        "raw": {"handlers": ["default"], "propagate": False},
        "cappuccino": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}


def _setup_logging():
    try:
        with Path("logging.yml").open() as fd:
            dictConfig(yaml.safe_load(fd))
            logging.getLogger(__name__).info("Using logging.yml for logging config.")

    except FileNotFoundError:
        dictConfig(DEFAULT_LOG_CONFIG)
        logging.getLogger(__name__).info(
            "logging.yml not found, using default logging config."
        )
    except yaml.YAMLError as exc:
        dictConfig(DEFAULT_LOG_CONFIG)
        logging.getLogger(__name__).exception(exc)


_setup_logging()


def _create_requests_session(bot) -> Session:
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
        self.logger = logging.getLogger(plugin_module)
        self.requests = _create_requests_session(bot)
        if self.config:
            # I have no idea where these are coming from but whatever.
            weird_keys = ["#", "hash"]
            for key in weird_keys:
                if key in self.config:
                    self.config.pop(key)

            self.logger.debug(f"Configuration for {plugin_module}: {self.config}")
