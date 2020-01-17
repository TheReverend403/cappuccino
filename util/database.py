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

from sqlalchemy import create_engine


class _Singleton:
    def __init__(self, engine):
        self.engine = engine


class Database(object):
    instance = None

    def __init__(self, plugin):
        plugin.bot.log.info(f'Initialising database for {plugin.__module__}')
        if not Database.instance:
            Database.instance = _Singleton(create_engine(plugin.bot.config.get('database', {}).get('uri')))

        if hasattr(plugin, 'db_meta'):
            plugin.db_meta.create_all(self.instance.engine)

    def __getattr__(self, name):
        return getattr(self.instance.engine, name)

