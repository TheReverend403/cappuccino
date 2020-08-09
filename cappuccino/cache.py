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

import irc3
import redis
from redis_cache import RedisCache


@irc3.plugin
class Cache(object):

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.get(__name__, {})
        self.client = redis.from_url(self.config.get('redis_url'))
        self.bot.cache = RedisCache(redis_client=self.client).cache
