from irc3.plugins.command import command
import irc3
from tinydb import TinyDB
from tinydb import where


class Database(object):
    def __init__(self, path):
        self.tinydb = TinyDB(path)

    def get_user_value(self, username, key):
        key = '_' + key
        table = self.tinydb.table()
        value = table.get(where('username') == username)
        if not value:
            return None
        try:
            return value[key]
        except KeyError:
            return None

    def set_user_value(self, username, key, value):
        self.insert_else_update_user(username, {key: value})

    def insert_else_update_user(self, username, extra_params=None):
        table = self.tinydb.table()
        if not table.get(where('username') == username):
            table.insert({
                'username': username,
            })
        else:
            table.update({
                'username': username,
            }, where('username') == username)
        if extra_params is not None:
            for k in extra_params:
                if not k.startswith('_'):
                    extra_params['_' + k] = extra_params.pop(k)
            table.update(extra_params, where('username') == username)


def pluralise(value):
    return value if value.endswith('s') else value + 's'


@irc3.plugin
class Plugin(object):
    commands = ['dtop', 'distro', 'dotfile', 'homescreen']

    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data.json')

    @irc3.event(r':(?P<ns>\w+)!.+@.+ NOTICE (?P<nick>.*) :This nickname is registered.*')
    def login_attempt(self, ns, nick):
        try:
            password = self.bot.config['nickserv_password']
        except KeyError:
            self.bot.log.info('No NickServ password is set in config.ini!')
        else:
            self.bot.log.info('Authenticating with NickServ')
            self.bot.privmsg(ns, 'identify {0}'.format(password))

    @irc3.event(r':\w+!.+@.+ NOTICE .* :Password accepted.*')
    def login_succeeded(self):
        self.bot.log.info('Authenticated with NickServ')

    @irc3.event(r':\w+!.+@.+ NOTICE .* :Password incorrect.*')
    def login_failed(self):
        self.bot.log.info('Failed to authenticate with NickServ due to an incorrect password')

    def _generic_db(self, mask, target, args):
        mode = None
        for _command in self.commands:
            try:
                if args[_command]:
                    mode = pluralise(_command)
            except KeyError:
                pass

        if args['--add']:
            values = self.db.get_user_value(mask.nick, mode) or []
            for value in args['<values>']:
                values.append(value)
            self.db.set_user_value(mask.nick, mode, values)
            return '{0} updated!'.format(mode)

        if args['--set']:
            self.db.set_user_value(mask.nick, mode, args['<values>'])
            return '{0} updated!'.format(mode)

        if args['--remove']:
            values = self.db.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to remove!'.format(mode)
            indexes = args['<indexes>']
            deleted = []
            for index in indexes:
                index = int(index)
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
            index = int(args['<index>'])
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
            if args['index']:
                index = int(args['index'])
                try:
                    return '{0} [{1}]'.format(values[index], user)
                except IndexError:
                    return 'Invalid index!'
            return '{0} [{1}]'.format(' | '.join(values), user)
        else:
            return '{0} has no {1}'.format(user, mode)

    @command(permission='view')
    def dtop(self, mask, target, args):
        """View or add a desktop

            %%dtop [(--set <values>... | --add <values>... | --remove <indexes>... | --replace <index> <value>) | <user> [index]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def dotfile(self, mask, target, args):
        """View or add dotfiles

            %%dotfile [(--set <values>... | --add <values>... | --remove <indexes>... | --replace <index> <value>) | <user> [index]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def distro(self, mask, target, args):
        """View or add a distro

            %%distro [(--set <values>... | --add <values>... | --remove <indexes>... | --replace <index> <value>) | <user> [index]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def homescreen(self, mask, target, args):
        """View or add a homescreen

            %%homescreen [(--set <values>... | --add <values>... | --remove <indexes>... | --replace <index> <value>) | <user> [index]]
        """
        yield self._generic_db(mask, target, args)
