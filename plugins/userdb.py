import irc3
import os


class UserDB(object):

    requires = [
        'irc3.plugins.storage'
    ]

    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists('data'):
            os.mkdir('data')
            self.bot.log.info('Created data/ directory')

    @irc3.extend
    def get_user_value(self, username, key):
        try:
            return self.bot.db.get(username)[key]
        except (KeyError, TypeError):
            return None

    @irc3.extend
    def set_user_value(self, username, key, value):
        data = {key: value}
        self.bot.db.set(username, **data)
