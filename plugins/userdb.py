import signal
import sys
import threading
from datetime import datetime

import bottle
from irc3.plugins.command import command

try:
    import ujson as json
except ImportError:
    import json

import irc3
from pathlib import Path


def strip_path():
    bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')


def http_json_dump(data: dict):
    bottle.response.content_type = 'application/json'

    return json.dumps(dict(sorted(data.items())))


@irc3.plugin
class UserDB(object):

    def __init__(self, bot):
        self.bot = bot
        self.root = Path('data')
        self.file = self.root / 'userdb.json'
        self.data = {}
        self.last_write = datetime.now()

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._shutdown_hook)

        try:
            self.config = self.bot.config[__name__]
            if not self.config.get('enable_http_server'):
                return
            host, port = self.config['http_host'], int(self.config['http_port'])
        except KeyError:
            host, port = '127.0.0.1', 8080

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

        bottle.hook('before_request')(strip_path)
        bottle.route('/')(lambda: http_json_dump(self.data))
        bottle_thread = threading.Thread(
            target=bottle.run,
            kwargs={'quiet': True, 'host': host, 'port': port},
            name='{0} HTTP server'.format(__name__),
            daemon=True
        )
        bottle_thread.start()

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

    @command()
    def sync(self, force=False):
        # Only write to disk once every 5 minutes so seen.py doesn't kill performance with constant writes.
        if force or abs((datetime.now() - self.last_write).seconds) >= 60 * 5:
            with self.file.open('w') as fd:
                json.dump(self.data, fd)
            self.last_write = datetime.now()
            self.bot.log.debug('Synced database to disk.')

    def _shutdown_hook(self, signo, frame):
        self.sync(force=True)
        sys.exit(0)
