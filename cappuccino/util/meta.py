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

import os

FULL_VERSION: str = "[version unknown]"
VERSION: str | None = os.getenv("META_VERSION")
COMMIT: str | None = os.getenv("META_COMMIT")
SOURCE: str = os.getenv("META_SOURCE") or "https://github.com/TheReverend403/cappuccino"

if VERSION:
    FULL_VERSION = f"{VERSION}"

if COMMIT:
    FULL_VERSION += f"-{COMMIT[:8]}"
