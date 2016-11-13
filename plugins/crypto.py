import hashlib
import irc3
from irc3.plugins.command import command


@irc3.plugin
class Crypto(object):

    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def hash(self, mask, target, args):
        """Hash text.

            %%hash (--md5 | --sha1 | --sha256 | --sha512) <string>...
        """
        available_algorithms = hashlib.algorithms_guaranteed
        text = ' '.join(args['<string>']).encode('UTF-8')
        for algo in available_algorithms:
            flag = '--{0}'.format(algo)
            if flag in args and args[flag]:
                hash_object = hashlib.new(algo)
                hash_object.update(text)
                return '{0}: {1}'.format(self.bot.format(mask.nick, antiping=True), hash_object.hexdigest())
