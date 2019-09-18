import atexit
import signal
from datetime import datetime

try:
    import ujson as json
except ImportError:
    import json

import irc3
from pathlib import Path


@irc3.plugin
class UserDB(object):

    def __init__(self, bot):
        self.bot = bot
        self.root = Path('data')
        self.file = self.root / 'userdb.json'
        self.data = {}
        self.last_write = None
        atexit.register(self.sync, force=True)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._shutdown_hook)

        try:
            with self.file.open('r') as fd:
                self.data.update(json.load(fd))
        except FileNotFoundError:
            # Database file itself doesn't need to exist on first run, it will be created on first write.
            if not self.file.exists():
                # Copy ricedb.json from old installations if it exists.
                old_db_file = Path(self.root) / 'ricedb.json'
                if old_db_file.exists():
                    old_db_file.replace(self.file)
                    with self.file.open('r') as fd:
                        self.data.update(json.load(fd))
                else:
                    self.root.mkdir(exist_ok=True)
                    self.file.touch(exist_ok=True)
                    self.bot.log.debug(f'Created {self.root} directory')

        # If any user has an uppercase in their nick, convert the whole DB to lowercase.
        db_copy = self.data.copy()
        for user, data in db_copy.items():
            if any(c.isupper() for c in user):
                self.set_user_value(user, self.data.pop(user))

    @irc3.extend
    def get_user_value(self, username: str, key: str):
        try:
            return self.data.get(username.lower())[key]
        except (KeyError, TypeError):
            return None

    @irc3.extend
    def del_user_value(self, username: str, key: str):
        try:
            del self.data[username.lower()][key]
        except KeyError:
            pass

        self.sync()

    @irc3.extend
    def set_user_value(self, username: str, key, value=None):
        data = {key: value} if value else key
        username = username.lower()

        try:
            self.data[username].update(data)
        except KeyError:
            self.data[username] = data

        self.sync()

    def sync(self, force=False):
        # Only write to disk once every 5 minutes so seen.py doesn't kill performance with constant writes.
        if force or not self.last_write or abs((datetime.now() - self.last_write).seconds) >= 60 * 5:
            with self.file.open('w') as fd:
                json.dump(self.data, fd)
            self.last_write = datetime.now()
            self.bot.log.info('Synced database to disk.')

    def _shutdown_hook(self, *args):
        self.sync(force=True)
