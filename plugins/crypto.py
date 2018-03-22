import hashlib
import irc3
from irc3.plugins.command import command


@irc3.plugin
class Crypto(object):

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def hash(self, mask, target, args):
        """Hash text.

            %%hash <ALGORITHM> <string>...
        """
        algo = args['<ALGORITHM>'].lower()
        available_algorithms = set(item.lower() for item in hashlib.algorithms_guaranteed)
        text = ' '.join(args['<string>']).encode('UTF-8')
        if algo not in available_algorithms:
            return 'Please choose an algorithm from {0}'.format(', '.join(set(available_algorithms)))
        hash_object = hashlib.new(algo)
        hash_object.update(text)
        return '{0}: {1}'.format(mask.nick, hash_object.hexdigest())
