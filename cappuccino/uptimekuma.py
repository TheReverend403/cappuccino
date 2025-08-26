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
from httpx import URL, AsyncClient, HTTPError
from irc3 import rfc

from cappuccino import Plugin


@irc3.plugin
class UptimeKuma(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self._webhook: str | None = self.config.get("webhook", None)
        self._interval: int = self.config.get("interval", 30)

    @irc3.event(rfc.CONNECTED)
    def _on_connect(
        self, srv: str | None = None, me: str | None = None, data: str | None = None
    ):
        if self._webhook:
            self.bot.create_task(self._ping_loop())

    async def ping(self, message: str = "OK", status: str = "up"):
        async with AsyncClient(timeout=5) as client:
            request_params = {"status": status, "msg": message}
            request_url = URL(self._webhook, params=request_params)
            self.logger.debug(f"Pinging {request_url}")
            try:
                response = await client.get(request_url)
                response.raise_for_status()
                self.logger.debug("Ping succeeded.")
            except HTTPError:
                self.logger.exception("Ping failed.")

    async def _ping_loop(self):
        self.logger.info(f"Pinging Uptime Kuma every {self._interval} seconds.")
        while True:
            await self.ping()
            await asyncio.sleep(self._interval)
