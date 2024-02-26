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

VERSION: str = "[version unknown]"
_META_VERSION: str = os.getenv("META_VERSION")
_META_HASH: str = os.getenv("META_VERSION_HASH")

if _META_VERSION and _META_HASH:
    VERSION = f"{_META_VERSION} ({_META_HASH[:8]})"
