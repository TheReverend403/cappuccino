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
import threading

import bottle
from sqlalchemy import Column, JSON, MetaData, String, Table, desc, func, select
from sqlalchemy.exc import IntegrityError

try:
    import ujson as json
except ImportError:
    import json

import irc3


def _strip_path():
    bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')


@irc3.plugin
class UserDB(object):

    requires = [
        'plugins.database'
    ]

    metadata = MetaData()
    ricedb = Table('ricedb', metadata,
                   Column('nick', String, primary_key=True),
                   Column('data', JSON))

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.database
        self.metadata.create_all(self.db)
        self._migrate()

        try:
            self.config = self.bot.config[__name__]
            if not self.config.get('enable_http_server'):
                return
            host, port = self.config['http_host'], int(self.config['http_port'])
        except KeyError:
            host, port = '127.0.0.1', 8080

        bottle.hook('before_request')(_strip_path)
        bottle.route('/')(lambda: self._json_dump())
        bottle_thread = threading.Thread(
            target=bottle.run,
            kwargs={'quiet': True, 'host': host, 'port': port},
            name='{0} HTTP server'.format(__name__),
            daemon=True
        )
        bottle_thread.start()

    @irc3.extend
    def get_user_value(self, username: str, key: str):
        query = select([self.ricedb.c.data]).where(func.lower(self.ricedb.c.nick) == username.lower())
        result = self.db.execute(query).scalar()
        if result is None:
            return None

        try:
            return result[key]
        except (KeyError, TypeError):
            return None

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        query = select([self.ricedb.c.data]).where(func.lower(self.ricedb.c.nick) == username.lower())
        result = self.db.execute(query).scalar()

        try:
            del result[key]
        except KeyError:
            pass

        update = self.ricedb.update().where(func.lower(self.ricedb.c.nick) == username.lower()).values(data=result)
        self.db.execute(update)

    @irc3.extend
    def set_user_value(self, username: str, key, value=None):
        query = select([self.ricedb.c.data]).where(func.lower(self.ricedb.c.nick) == username.lower())
        result = self.db.execute(query).scalar()
        data = {key: value} if value else key

        try:
            result.update(data)
        except KeyError:
            result = data
        except ValueError:
            self.del_user_value(username, key)
            return

        update = self.ricedb.update().where(func.lower(self.ricedb.c.nick) == username.lower()).values(data=result)
        self.db.execute(update)

    def _migrate(self):
        if os.path.exists('data/userdb.json'):
            self.bot.log.info('Found userdb.json, migrating data.')
            with open('data/userdb.json', 'r') as fd:
                data = json.load(fd)

                rice_insert = self.ricedb.insert(). \
                    values([
                        {'nick': user, 'data': data[user]}
                        for user in data.keys()
                    ])

                try:
                    self.db.execute(rice_insert)
                except IntegrityError:
                    pass

                self.bot.log.info('Migration complete, renaming old file.')
                os.rename('data/userdb.json', 'data/userdb.json.bak')

    def _json_dump(self):
        bottle.response.content_type = 'application/json'
        result = self.db.execute(self.ricedb.select().order_by(desc(self.ricedb.c.nick)))
        data = {row[0]: row[1] for row in result}

        return json.dumps(dict(data.items()))
