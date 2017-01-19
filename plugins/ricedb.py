import inspect

import irc3
import random
from irc3.plugins.command import command

MAX_USER_VALUES = 6


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
        self.bot.log.debug('{0} called by {1} with args: {2}'.format(mode, mask, args))
        mode = mode if mode.endswith('s') else mode + 's'

        if args['<values>']:
            args['<values>'] = [arg.strip() for arg in args['<values>'] if arg.strip()]

            if len(args['<values>']) == 0:
                return '{0} cannot be empty!'.format(mode)

        if args['--add'] or args['-a']:
            values = self.bot.get_user_value(mask.nick, mode) or []
            if len(values) + len(args['<values>']) > MAX_USER_VALUES:
                return 'You can only set {0} {1}! Consider deleting or replacing some.'.format(MAX_USER_VALUES, mode)
            for value in args['<values>']:
                values.append(value)
            self.bot.set_user_value(mask.nick, mode, values)
            return '{0} updated.'.format(mode)

        if args['--set'] or args['-s']:
            values = args['<values>']
            if len(values) > MAX_USER_VALUES:
                return 'You can only set {0} {1}! Consider deleting or replacing some.'.format(MAX_USER_VALUES, mode)
            self.bot.set_user_value(mask.nick, mode, values)
            return '{0} updated.'.format(mode)

        if args['--delete'] or args['-d']:
            values = self.bot.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to remove.'.format(mode)
            indexes = set(args['<ids>'])
            if '*' in indexes:
                self.bot.set_user_value(mask.nick, mode, [])
                return 'Removed all of your {0}.'.format(mode)
            deleted = []
            # Delete values in descending order to prevent re-ordering of the list while deleting.
            for index in sorted(indexes, reverse=True):
                index = from_user_index(index)
                try:
                    deleted.append(values[index])
                    del values[index]
                except IndexError:
                    pass
            if not deleted:
                return 'No {0} were removed. Maybe you supplied the wrong IDs?'.format(mode)
            self.bot.set_user_value(mask.nick, mode, values)
            return 'Removed {0}.'.format(', '.join(deleted))

        if args['--replace'] or args['-r']:
            index = from_user_index(args['<id>'])
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
                return 'Invalid ID.'

        user = args['<user>'] or mask.nick
        if user.isdigit():  # Support .command <id> syntax
            index = from_user_index(int(user))
            try:
                value = self.bot.get_user_value(mask.nick, mode)[index]
            except IndexError:
                return 'Invalid ID.'
            else:
                return '{0} [{1}]'.format(value, mask.nick)

        values = self.bot.get_user_value(user, mode)
        if values:
            indexed_values = []
            for index, item in enumerate(values):
                indexed_values.append('({0}) {1}'.format(
                        self.bot.format(to_user_index(index), bold=True), self.bot.format(item, reset=True)))
            return '{0} [{1}]'.format(' | '.join(indexed_values), user)

        return '{0} no {1}.'.format(user + ' has' if user != mask.nick else 'You have',
                                    'reason to live' if random.random() <= 0.05 else mode)

    @command(permission='view')
    def station(self, mask, target, args):
        """
            %%station [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view', aliases=['desktop'])
    def dtop(self, mask, target, args):
        """
            %%dtop [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view', aliases=['git'])
    def dotfiles(self, mask, target, args):
        """
            %%dotfiles [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view', aliases=['hw'])
    def handwriting(self, mask, target, args):
        """
            %%handwriting [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def distro(self, mask, target, args):
        """
            %%distro [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view', aliases=['hscr'])
    def homescreen(self, mask, target, args):
        """
            %%homescreen [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def selfie(self, mask, target, args):
        """
            %%selfie [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)
