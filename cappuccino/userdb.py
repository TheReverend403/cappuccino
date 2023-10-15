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

import threading

import bottle
from sqlalchemy import desc, func, insert, nullslast, select, update

from cappuccino import Plugin
from cappuccino.util.database import Database
from cappuccino.util.formatting import unstyle

try:
    import ujson as json
except ImportError:
    import json

import contextlib

import irc3


def _strip_path():
    bottle.request.environ["PATH_INFO"] = bottle.request.environ["PATH_INFO"].rstrip(
        "/"
    )


@irc3.plugin
class UserDB(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self._db = Database(self)
        self._ricedb = self._db.meta.tables["ricedb"]

        if self.config.get("enable_http_server", False):
            host = self.config.get("http_host", "127.0.0.1")
            port = int(self.config.get("http_port", 8080))
            bottle.hook("before_request")(_strip_path)
            bottle.route("/")(self._json_dump)
            bottle_thread = threading.Thread(
                target=bottle.run,
                kwargs={"quiet": True, "host": host, "port": port},
                name=f"{__name__} HTTP server",
                daemon=True,
            )
            bottle_thread.start()

    @irc3.extend
    def get_user_value(self, username: str, key: str):
        return self._db.execute(
            select([self._ricedb.c[key]]).where(
                func.lower(self._ricedb.c.nick) == username.lower()
            )
        ).scalar()

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        self._db.execute(
            update(self._ricedb)
            .where(func.lower(self._ricedb.c.nick) == username.lower())
            .values(**{key: None})
        )

    @irc3.extend
    def set_user_value(self, username: str, key: str, value=None):
        user_exists = (
            self._db.execute(
                select([self._ricedb.c.nick]).where(
                    func.lower(self._ricedb.c.nick) == username.lower()
                )
            ).scalar()
            or None
        )

        if user_exists is None:
            self._db.execute(insert(self._ricedb).values(nick=username, **{key: value}))
            return

        self._db.execute(
            update(self._ricedb)
            .where(func.lower(self._ricedb.c.nick) == username.lower())
            .values(nick=username, **{key: value})
        )

    def _json_dump(self) -> str:
        bottle.response.content_type = "application/json"

        data = []
        all_users = self._db.execute(
            select([self._ricedb]).order_by(nullslast(desc(self._ricedb.c.last_seen)))
        )
        for row in all_users:
            user = {}
            for column, value in row.items():
                if value is None:
                    continue

                if column == "last_seen":
                    value = value.timestamp()

                with contextlib.suppress(TypeError, AttributeError):
                    value = (
                        [unstyle(val) for val in value]
                        if isinstance(value, list)
                        else unstyle(value)
                    )

                user[column] = value
            data.append(user)
        return json.dumps(data)
