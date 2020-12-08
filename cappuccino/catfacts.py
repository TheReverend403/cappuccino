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
from logging import getLogger

import irc3
from irc3.plugins.command import command
from requests import RequestException

from cappuccino import Plugin

log = getLogger(__name__)


@irc3.plugin
class CatFacts(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self._cache = []
        self._limit = self.config.get("limit", 1000)
        self._max_length = self.config.get("max_length", 200)
        self._api_url = self.config.get("api_url", "https://catfact.ninja/facts")

    def _get_cat_fact(self):
        if not self._cat_cache:
            log.debug("Fetching cat facts.")
            request_parameters = {"limit": self._limit}
            if self._max_length > 0:
                request_parameters.update({"max_length": self._max_length})

            with self.bot.requests.get(
                self._api_url, params=request_parameters
            ) as response:
                self._cat_cache = [fact["fact"] for fact in response.json()["data"]]
                random.shuffle(self._cat_cache)

        return self._cat_cache.pop()

    @command(permission="view")
    def catfact(self, mask, target, args):
        """Grab a random cat fact.

        %%catfact
        """

        try:
            yield self._get_cat_fact()
        except RequestException:
            yield "Something went horribly wrong while I was researching cat facts. :("
