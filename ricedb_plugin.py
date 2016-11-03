import platform

from irc3.plugins.command import command
import irc3

"""Converts a zero-indexed value to a user-friendly value starting from 1"""
def to_user_index(index):
    return index + 1

"""Converts a user-supplied index to a value suitable for zero-indexed arrays"""
def from_user_index(index):
    index = int(index)
    return index - 1 if index > 0 else 0


class Database(object):
    def __init__(self, storage):
        self.storage = storage

    def get_user_value(self, username, key):
        key = '_' + key
        try:
            return self.storage.get(username)[key]
        except (KeyError, TypeError):
            return None

    def set_user_value(self, username, key, value):
        key = '_' + key
        data = {key: value}
        self.storage.set(username, **data)


@irc3.plugin
class Plugin(object):
    commands = ['dtop', 'distro', 'dotfiles', 'homescreen']

    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot.db)

    @irc3.event(r':(?P<ns>\w+)!.+@.+ NOTICE (?P<nick>.*) :This nickname is registered.*')
    def login_attempt(self, ns, nick):
        try:
            password = self.bot.config['nickserv_password']
        except KeyError:
            self.bot.log.warn('This nick is registered but no NickServ password is set in config.ini')
        else:
            self.bot.log.info('Authenticating with NickServ')
            self.bot.privmsg(ns, 'identify {0}'.format(password))

    @irc3.event(r':\w+!.+@.+ NOTICE .* :Password accepted.*')
    def login_succeeded(self):
        self.bot.log.info('Authenticated with NickServ')

    @irc3.event(r':\w+!.+@.+ NOTICE .* :Password incorrect.*')
    def login_failed(self):
        self.bot.log.error('Failed to authenticate with NickServ due to an incorrect password')

    def _generic_db(self, mask, target, args):
        mode = None
        for _command in self.commands:
            try:
                if args[_command]:
                    mode = _command if _command.endswith('s') else _command + 's'
            except KeyError:
                pass

        if args['--add']:
            values = self.db.get_user_value(mask.nick, mode) or []
            if mode == 'distros':
                values = [' '.join(values)]
            for value in args['<values>']:
                values.append(value)
            self.db.set_user_value(mask.nick, mode, values)
            return '{0} updated!'.format(mode)

        if args['--set']:
            values = args['<values>']
            if mode == 'distros':
                values = [' '.join(values)]
            self.db.set_user_value(mask.nick, mode, values)
            return '{0} updated!'.format(mode)

        if args['--delete']:
            values = self.db.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to remove!'.format(mode)
            indexes = args['<indexes>']
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
            self.db.set_user_value(mask.nick, mode, values)
            return 'Removed {0}!'.format(', '.join(deleted))

        if args['--replace']:
            index = from_user_index(args['<index>'])
            value = args['<value>']
            values = self.db.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to replace!'.format(mode)
            try:
                old_value = values[index]
                values[index] = value
                self.db.set_user_value(mask.nick, mode, values)
                return 'Replaced {0} with {1}'.format(old_value, value)
            except IndexError:
                return 'Invalid index!'

        user = args['<user>'] or mask.nick
        values = self.db.get_user_value(user, mode)
        if values:
            indexed_values = []
            for index, item in enumerate(values):
                indexed_values.append('[{0}] {1}'.format(to_user_index(index), item))
            return '{0} [{1}]'.format(' | '.join(indexed_values), user)
        else:
            return '{0} has no {1}'.format(user, mode)

    @command(permission='view')
    def dtop(self, mask, target, args):
        """View or add a desktop

            %%dtop [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def dotfiles(self, mask, target, args):
        """View or add dotfiles

            %%dotfiles [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def distro(self, mask, target, args):
        """View or add a distro

            %%distro [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def homescreen(self, mask, target, args):
        """View or add a homescreen

            %%homescreen [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='admin')
    def mirror_aigis(self, mask, target, args):
        """Update local DB from Aigis' latest version

            %%mirror_aigis
        """
        server = 'Rizon'
        db_map = {
            'dtops': 'desktops',
            'homescreens': 'homescreens',
            'dotfiles': 'gits'
        }

        import requests
        for db in db_map:
            r = requests.get('https://api.joaquin-v.xyz/aigis/database.php?server={0}&db={1}'.format(
                server, db_map[db]))
            data = r.json()
            self.bot.log.info('Updating user database...')
            for user in data:
                if data[user]:
                    self.db.set_user_value(user, db, data[user])
        yield 'Database updated.'

    @command(permission='view')
    def bots(self, mask, target, args):
        """Report in!

            %%bots
        """
        yield 'Reporting in! [Python {0}]'.format(platform.python_version())
