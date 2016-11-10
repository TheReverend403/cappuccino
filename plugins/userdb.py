import irc3


class UserDB(object):

    requires = [
        'irc3.plugins.storage'
    ]

    def __init__(self, bot):
        self.bot = bot

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
