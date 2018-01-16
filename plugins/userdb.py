try:
    import ujson as json
except ImportError:
    import json

import os
import irc3


class UserDB(dict):
    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)

        self.__bot = bot
        self.__file = os.path.join('data', 'ricedb.json')

        datadir = os.path.dirname(self.__file)
        try:
            with open(self.__file, 'r') as fd:
                self.update(json.load(fd))
        except FileNotFoundError:
            # Database file itself doesn't need to exist on first run, it will be created on first write.
            if not os.path.exists(datadir):
                os.mkdir(datadir)
                self.__bot.log.debug('Created {0}/ directory'.format(datadir))

    @irc3.extend
    def get_user_value(self, username, key):
        try:
            return self.get(username)[key]
        except (KeyError, TypeError):
            return []

    @irc3.extend
    def set_user_value(self, username, key, value):
        data = {key: value}
        try:
            self[username].update(data)
        except KeyError:
            self[username] = data
        with open(self.__file, 'w') as fd:
            json.dump(self, fd)
