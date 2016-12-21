try:
    import ujson as json
except ImportError:
    import json

import os
import threading

import bottle
import irc3


class UserDB(dict):
    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)

        self.bot = bot
        self.file = os.path.join('data', 'ricedb.json')

        datadir = os.path.dirname(self.file)
        try:
            with open(self.file, 'r') as fd:
                self.update(json.load(fd))
        except FileNotFoundError:
            # Database file itself doesn't need to exist on first run, it will be created on first write.
            if not os.path.exists(datadir):
                os.mkdir(datadir)
                self.bot.log.debug('Created {0}/ directory'.format(datadir))

        try:
            self.config = self.bot.config[__name__]
            if not self.config.get('enable_http_server'):
                return
            host, port = self.config['http_host'], int(self.config['http_port'])
        except KeyError:
            host, port = '127.0.0.1', 8080

        bottle.route('/')(self.__http_index)
        bottle.route('/<user>')(self.__http_index)
        bottle.route('/<user>/<key>')(self.__http_index)

        bottle_thread = threading.Thread(
            target=bottle.run,
            kwargs={'quiet': True, 'host': host, 'port': port},
            name='{0} HTTP server'.format(__name__)
        )
        bottle_thread.daemon = True
        bottle_thread.start()
        self.bot.log.info('{0} started on http://{1}:{2}'.format(bottle_thread.name, host, port))

    def __http_index(self, user=None, key=None):
        bottle.response.content_type = 'application/json'
        if user:
            if user not in self:
                return bottle.HTTPResponse(status=404, body=json.dumps(None))
            if key:
                if key not in self.get(user):
                    return bottle.HTTPResponse(status=404, body=json.dumps(None))
                return json.dumps(self.get(user).get(key))
            return json.dumps(self.get(user))
        return json.dumps(self)

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
        with open(self.file, 'w') as fd:
            json.dump(self, fd)
