import irc3


@irc3.plugin
class Plugin(object):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config[__name__]

    @irc3.event(r':(?P<ns>\w+)!.+@.+ NOTICE (?P<nick>.*) :This nickname is registered.*')
    def login_attempt(self, ns, nick):
        try:
            password = self.config['password']
        except KeyError:
            self.bot.log.warn('This nick is registered but no NickServ password is set in config.ini')
        else:
            self.bot.privmsg(ns, 'identify {0}'.format(password))

    @irc3.event(r':\w+!.+@.+ NOTICE .* :Password accepted.*')
    def login_succeeded(self):
        self.bot.log.info('Authenticated with NickServ')

    @irc3.event(r':\w+!.+@.+ NOTICE .* :Password incorrect.*')
    def login_failed(self):
        self.bot.log.error('Failed to authenticate with NickServ due to an incorrect password')
