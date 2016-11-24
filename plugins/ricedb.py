import inspect
import shlex

import irc3
import random
from irc3.plugins.command import command


def to_user_index(index):
    """Converts a zero-indexed value to a user-friendly value starting from 1"""
    return index + 1


def from_user_index(index):
    """Converts a user-supplied index to a value suitable for zero-indexed arrays"""
    index = int(index)
    return index - 1 if index >= 1 else index


@irc3.plugin
class RiceDB(object):
    requires = [
        'irc3.plugins.command',
        'plugins.formatting',
        'plugins.userdb'
    ]

    def __init__(self, bot):
        self.bot = bot

    def _generic_db(self, mask, target, args):
        # Get name of command _generic_db is being called from.
        mode = inspect.stack()[1][3]
        mode = mode if mode.endswith('s') else mode + 's'

        # Apply some sanity to the way docopt handles args with spaces.
        if args['<values>']:
            try:
                args['<values>'] = [arg.strip() for arg in shlex.split(' '.join(args['<values>'])) if arg.strip()]
            except ValueError:
                pass

            if len(args['<values>']) == 0:
                return 'Values cannot be empty!'

        if args['--add'] or args['-a']:
            values = self.bot.get_user_value(mask.nick, mode) or []
            for value in args['<values>']:
                values.append(value)
            self.bot.set_user_value(mask.nick, mode, values)
            return '{0} updated.'.format(mode)

        if args['--set'] or args['-s']:
            values = args['<values>']
            self.bot.set_user_value(mask.nick, mode, values)
            return '{0} updated.'.format(mode)

        if args['--delete'] or args['-d']:
            values = self.bot.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to remove.'.format(mode)
            indexes = args['<indexes>']
            if '*' in indexes:
                self.bot.set_user_value(mask.nick, mode, [])
                return 'Removed all of your {0}.'.format(mode)
            deleted = []
            for index in indexes:
                index = from_user_index(index)
                try:
                    deleted.append(values[index])
                    del values[index]
                except IndexError:
                    pass
            if not deleted:
                return 'No {0} were removed. Maybe you supplied the wrong indexes?'.format(mode)
            self.bot.set_user_value(mask.nick, mode, values)
            return 'Removed {0}.'.format(', '.join(deleted))

        if args['--replace'] or args['-r']:
            index = from_user_index(args['<index>'])
            replacement = args['<value>'].strip()
            if not replacement:
                return 'Replacement cannot be empty!'
            values = self.bot.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to replace.'.format(mode)
            try:
                old_value = values[index]
                values[index] = replacement
                self.bot.set_user_value(mask.nick, mode, values)
                return 'Replaced {0} with {1}'.format(old_value, replacement)
            except IndexError:
                return 'Invalid index.'

        user = args['<user>'] or mask.nick
        values = self.bot.get_user_value(user, mode)
        if values:
            indexed_values = []
            for index, item in enumerate(values):
                indexed_values.append(
                    '({0}) {1}{2}'.format(self.bot.format(to_user_index(index), bold=True), item, self.bot.color.RESET))
            return '{0} [{1}]'.format(' | '.join(indexed_values), self.bot.format(user, antiping=True))

        return '{0} no {1}.'.format(self.bot.format(user, antiping=True) + ' has' if user != mask.nick else 'You have',
                                    'reason to live' if random.random() <= 0.05 else mode)

    @command(permission='view')
    def station(self, mask, target, args):
        """View or add a battlestation.

            %%station [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def dtop(self, mask, target, args):
        """View or add a desktop.

            %%dtop [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def dotfiles(self, mask, target, args):
        """View or add dotfiles.

            %%dotfiles [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def handwriting(self, mask, target, args):
        """View or add handwriting.

            %%handwriting [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def distro(self, mask, target, args):
        """View or add a distro.

            %%distro [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def homescreen(self, mask, target, args):
        """View or add a homescreen.

            %%homescreen [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def selfie(self, mask, target, args):
        """View or add a selfie.

            %%selfie [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <indexes>... | (-r | --replace) <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)
