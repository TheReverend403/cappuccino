import inspect
import re

import irc3
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
class Rice(object):

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

        if args['<values>']:
            args['<values>'] = [arg.strip() for arg in args['<values>'] if arg.strip()]

            if len(args['<values>']) == 0:
                return f'{mode} cannot be empty!'

        if args['--add'] or args['-a']:
            values = self.bot.get_user_value(mask.nick, mode) or []
            if len(values) + len(args['<values>']) > MAX_USER_VALUES:
                return f'You can only set {MAX_USER_VALUES} {mode}! Consider deleting or replacing some.'

            for value in args['<values>']:
                values.append(value)

            self.bot.set_user_value(mask.nick, mode, values)
            return f'{mode} updated.'

        if args['--set'] or args['-s']:
            values = args['<values>']

            if len(values) > MAX_USER_VALUES:
                return f'You can only set {MAX_USER_VALUES} {mode}! Consider deleting or replacing some.'

            self.bot.set_user_value(mask.nick, mode, values)
            return f'{mode} updated.'

        if args['--delete'] or args['-d']:
            values = self.bot.get_user_value(mask.nick, mode)
            if not values:
                return f'You do not have any {mode} to remove.'

            indexes = set(args['<ids>'])
            if '*' in indexes:
                self.bot.del_user_value(mask.nick, mode)
                return f'Removed all of your {mode}.'

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
                return f'No {mode} were removed. Maybe you supplied the wrong IDs?'

            self.bot.set_user_value(mask.nick, mode, values)
            deleted_list = ', '.join(deleted)
            return f'Removed {deleted_list}.'

        if args['--replace'] or args['-r']:
            index = from_user_index(args['<id>'])
            replacement = args['<value>'].strip()

            if not replacement:
                return 'Replacement cannot be empty!'

            values = self.bot.get_user_value(mask.nick, mode)
            if not values:
                return f'You do not have any {mode} to replace.'

            try:
                old_value = values[index]
                values[index] = replacement
                self.bot.set_user_value(mask.nick, mode, values)

                return f'Replaced {old_value} with {replacement}'
            except IndexError:
                return 'Invalid ID.'

        user = args['<user>'] or mask.nick

        if re.match('^https?://.*', user, re.IGNORECASE | re.DOTALL):
            return 'Did you mean to use --add (-a) or --set (-s) there?'

        if user.isdigit():  # Support .command <id> syntax
            index = from_user_index(int(user))
            try:
                value = self.bot.get_user_value(mask.nick, mode)[index]
            except IndexError:
                return 'Invalid ID.'

            return f'{value} [{mask.nick}]'

        values = self.bot.get_user_value(user, mode)
        if values:
            indexed_values = []
            for index, item in enumerate(values):
                index = self.bot.format(to_user_index(index), bold=True)
                item = self.bot.format(item, reset=True)
                indexed_values.append(f'({index}) {item}')

            formatted_values = ' | '.join(indexed_values)
            formatted_user = self.bot.format(user, color=self.bot.color.GREEN)

            return f'{formatted_values} [{formatted_user}]'

        return f'{user} has no {mode}.'

    @command(permission='view')
    def station(self, mask, target, args):
        """
            %%station [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view', aliases=['desktop', 'dt'])
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

    @command(permission='view')
    def pet(self, mask, target, args):
        """
            %%pet [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view', aliases=['site'])
    def website(self, mask, target, args):
        """
            %%website [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)
