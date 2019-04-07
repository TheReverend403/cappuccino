import irc3


@irc3.plugin
class NickServ(object):

    def __init__(self, bot):
        self.bot = bot

    @irc3.event(r':(?P<nickserv>NickServ)!\S+@\S+ NOTICE .* :This nickname is registered.*')
    def login_attempt(self, nickserv):
        try:
            password = self.bot.config[__name__]['password']
        except KeyError:
            self.bot.log.warn('This nick is registered but no nickserv password is set in config.ini')
        else:
            self.bot.privmsg(nickserv, f'IDENTIFY {password}')

    @irc3.event(r':(?P<mask>NickServ!\S+@\S+) NOTICE .* :Password accepted.*')
    def login_succeeded(self, mask):
        self.bot.log.info(f'Authenticated with {mask}')

    @irc3.event(r':(?P<mask>NickServ!\S+@\S+) NOTICE .* :Password incorrect.*')
    def login_failed(self, mask):
        self.bot.log.warn(f'Failed to authenticate with {mask} due to an incorrect password')
