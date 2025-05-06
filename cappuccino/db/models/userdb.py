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

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from cappuccino.db.models import BaseModel


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
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )
