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
from datetime import datetime

import bottle
from sqlalchemy import (
    JSON,
    DateTime,
    String,
    desc,
    func,
    inspect,
    nullslast,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column

from cappuccino import BaseModel, Plugin
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


class RiceDB(BaseModel):
    __tablename__ = "ricedb"

    nick: Mapped[str] = mapped_column(String(), nullable=False, primary_key=True)
    dtops: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    homescreens: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    stations: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    pets: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    dotfiles: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    handwritings: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    distros: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    websites: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    selfies: Mapped[JSON | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    lastfm: Mapped[str] = mapped_column(String(), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
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
        user = self.db_session.scalar(
            select(RiceDB).where(func.lower(RiceDB.nick) == username.lower())
        )
        if not user:
            return None

        return getattr(user, key)

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        user_select = select(RiceDB).where(func.lower(RiceDB.nick) == username.lower())
        user = self.db_session.scalar(user_select)
        setattr(user, key, None)
        self.db_session.commit()

    @irc3.extend
    def set_user_value(self, username: str, key: str, value=None):
        existing_user = (
            self.db_session.scalar(
                select(RiceDB).where(func.lower(RiceDB.nick) == username.lower())
            )
            or None
        )

        if existing_user is None:
            user = RiceDB(nick=username, **{key: value})
            self.db_session.add(user)
            self.db_session.commit()
            return

        setattr(existing_user, key, value)
        self.db_session.commit()

    def _json_dump(self):
        bottle.response.content_type = "application/json"

        data = []
        all_users = self.db_session.scalars(
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
