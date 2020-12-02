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

from cappuccino.util.database import Database
from cappuccino.util.formatting import unstyle

try:
    import ujson as json
except ImportError:
    import json

import irc3


def _strip_path():
    bottle.request.environ["PATH_INFO"] = bottle.request.environ["PATH_INFO"].rstrip(
        "/"
    )


@irc3.plugin
class UserDB(object):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.get(__name__, {})
        self.db = Database(self)
        self.ricedb = self.db.meta.tables["ricedb"]

        if self.config.get("enable_http_server", False):
            host = self.config.get("http_host", "127.0.0.1")
            port = int(self.config.get("http_port", 8080))
            bottle.hook("before_request")(_strip_path)
            bottle.route("/")(self._json_dump)
            bottle_thread = threading.Thread(
                target=bottle.run,
                kwargs={"quiet": True, "host": host, "port": port},
                name="{0} HTTP server".format(__name__),
                daemon=True,
            )
            bottle_thread.start()

    @irc3.extend
    def get_user_value(self, username: str, key: str):
        select_query = select([self.ricedb.c[key]]).where(
            func.lower(self.ricedb.c.nick) == username.lower()
        )
        result = self.db.execute(select_query).scalar()
        return result

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        update_query = (
            update(self.ricedb)
            .where(func.lower(self.ricedb.c.nick) == username.lower())
            .values(**{key: None})
        )

        self.db.execute(update_query)

    @irc3.extend
    def set_user_value(self, username: str, key, value=None):
        user_exists = (
            self.db.execute(
                select([self.ricedb.c.nick]).where(
                    func.lower(self.ricedb.c.nick) == username.lower()
                )
            ).scalar()
            or None
        )

        if user_exists is None:
            self.db.execute(insert(self.ricedb).values(nick=username, **{key: value}))
            return

        update_query = (
            update(self.ricedb)
            .where(func.lower(self.ricedb.c.nick) == username.lower())
            .values(nick=username, **{key: value})
        )  # Also update nick to fix the mass lowercasing I did on the old DB.
        self.db.execute(update_query)

    def _json_dump(self):
        bottle.response.content_type = "application/json"

        data = []
        all_users = self.db.execute(
            select([self.ricedb]).order_by(nullslast(desc(self.ricedb.c.last_seen)))
        )
        for row in all_users:
            user = {}
            for column, value in row.items():
                if value is None:
                    continue

                if column == "last_seen":
                    value = value.timestamp()

                try:
                    value = (
                        [unstyle(val) for val in value]
                        if type(value) is list
                        else unstyle(value)
                    )
                except (TypeError, AttributeError):
                    pass

                user[column] = value
            data.append(user)
        return json.dumps(data)
