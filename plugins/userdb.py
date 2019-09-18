from datetime import datetime

try:
    import ujson as json
except ImportError:
    import json

import irc3
from pathlib import Path


@irc3.plugin
class UserDB(dict):

    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)

        self.__bot = bot
        self.__root = Path('data')
        self.__file = self.__root / 'userdb.json'
        self.__last_write = None

        try:
            with self.__file.open('r') as fd:
                self.update(json.load(fd))
        except FileNotFoundError:
            # Database file itself doesn't need to exist on first run, it will be created on first write.
            if not self.__file.exists():
                # Copy ricedb.json from old installations if it exists.
                old_db_file = Path(self.__root) / 'ricedb.json'
                if old_db_file.exists():
                    old_db_file.replace(self.__file)
                    with self.__file.open('r') as fd:
                        self.update(json.load(fd))
                else:
                    self.__root.mkdir(exist_ok=True)
                    self.__file.touch(exist_ok=True)
                    self.__bot.log.debug(f'Created {self.__root} directory')

        # If any user has an uppercase in their nick, convert the whole DB to lowercase.
        db_copy = self.copy()
        for user, data in db_copy.items():
            if any(c.isupper() for c in user):
                self.set_user_value(user, self.pop(user))

    @irc3.extend
    def get_user_value(self, username: str, key: str):
        try:
            return self.get(username.lower())[key]
        except (KeyError, TypeError):
            return None

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        try:
            del self[username.lower()][key]
        except KeyError:
            pass

        self.sync()

    @irc3.extend
    def set_user_value(self, username: str, key, value=None):
        data = {key: value} if value else key
        username = username.lower()

        try:
            self[username].update(data)
        except KeyError:
            self[username] = data

        self.sync()

    def sync(self):
        # Only write to disk once every 5 minutes so seen.py doesn't kill performance with constant writes.
        if not self.__last_write or abs((datetime.now() - self.__last_write).seconds) >= 60 * 5:
            with self.__file.open('w') as fd:
                json.dump(self, fd)
            self.__last_write = datetime.now()
