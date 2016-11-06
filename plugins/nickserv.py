import irc3


@irc3.plugin
class Plugin(object):

    def __init__(self, bot):
        self.bot = bot

    @irc3.event(r':(?P<ns>\w+)!.+@.+ NOTICE .* :This nickname is registered.*')
    def login_attempt(self, ns):
        try:
            password = self.bot.config[__name__]['password']
        except KeyError:
            self.bot.log.warn('This nick is registered but no nickserv password is set in config.ini')
        else:
            self.bot.privmsg(ns, 'identify {0}'.format(password))

    @irc3.event(r':(?P<mask>\w+!.+@.+) NOTICE .* :Password accepted.*')
    def login_succeeded(self, mask):
        self.bot.log.info('Authenticated with {0}'.format(mask))

    @irc3.event(r':(?P<mask>\w+!.+@.+) NOTICE .* :Password incorrect.*')
    def login_failed(self, mask):
        self.bot.log.error('Failed to authenticate with {0} due to an incorrect password'.format(mask))
