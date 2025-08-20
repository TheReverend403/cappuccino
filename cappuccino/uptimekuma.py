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

import asyncio

import irc3
from httpx import AsyncClient, RequestError

from cappuccino import Plugin


@irc3.plugin
class UptimeKuma(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self._webhook = self.config.get("webhook", None)
        self._interval: int = self.config.get("interval", 30)

        if self._webhook:
            bot.create_task(self._ping_loop())
        else:
            self.logger.warning("No webhook supplied, will not ping Uptime Kuma.")

    async def _ping_loop(self):
        self.logger.info(f"Started Uptime Kuma ping every {self._interval} seconds.")
        async with AsyncClient(timeout=5) as client:
            while True:
                self.logger.debug("Pinging Uptime Kuma...")
                try:
                    request_params = {"status": "up", "msg": "OK"}
                    response = await client.get(self._webhook, params=request_params)
                    response_json = response.json()
                    if response_json.get("ok", False):
                        self.logger.debug("Pinged Uptime Kuma successfully.")
                    else:
                        self.logger.warning(
                            f"Failed to ping Uptime Kuma: {response_json.get('msg')}"
                        )
                except RequestError:
                    self.logger.exception()
                await asyncio.sleep(self._interval)
