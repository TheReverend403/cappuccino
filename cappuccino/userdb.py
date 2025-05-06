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
from sqlalchemy import (
    desc,
    func,
    inspect,
    nullslast,
    select,
    update,
)

from cappuccino import Plugin
from cappuccino.db.models.userdb import RiceDB
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
        with self.db_session() as session:
            return session.scalar(
                select(RiceDB.__table__.columns[key]).where(
                    func.lower(RiceDB.nick) == username.lower()
                )
            )

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        self.set_user_value(username, key, None)

    @irc3.extend
    def set_user_value(self, username: str, key: str, value=None):
        with self.db_session() as session, session.begin():
            user = session.scalar(
                update(RiceDB)
                .returning(RiceDB)
                .where(func.lower(RiceDB.nick) == username.lower())
                .values({key: value})
            )

            if user is None:
                user = RiceDB(nick=username, **{key: value})
                session.add(user)

    def _json_dump(self):
        bottle.response.content_type = "application/json"

        data = []
        with self.db_session() as session:
            all_users = session.scalars(
                select(RiceDB).order_by(nullslast(desc(RiceDB.last_seen)))
            ).all()

        for user in all_users:
            user_dict = {}
            for column, value in inspect(user).attrs.items():
                value = value.value
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

                user_dict[column] = value
            data.append(user_dict)
        return json.dumps(data)
