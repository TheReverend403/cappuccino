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

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from cappuccino.db.models import BaseModel


class Trigger(BaseModel):
    __tablename__ = "triggers"

    name: Mapped[str] = mapped_column(Text, nullable=False, primary_key=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False, primary_key=True)
    response: Mapped[str] = mapped_column(Text, nullable=False, unique=False)
