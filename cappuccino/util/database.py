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

import logging

from sqlalchemy import MetaData, create_engine

log = logging.getLogger(__name__)


class Database(object):
    instance = None
    meta = None

    def __init__(self, plugin):
        log.debug(f'Initialising database for {plugin.__module__}')
        if not Database.instance:
            Database.instance = self.__Singleton(create_engine(plugin.bot.config.get('database', {}).get('uri')))
            Database.meta = MetaData(bind=Database.instance.engine, reflect=True)

    def __getattr__(self, name):
        return getattr(self.instance.engine, name) or getattr(self.instance, name)

    class __Singleton:
        def __init__(self, engine):
            self.engine = engine
