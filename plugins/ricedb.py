import inspect
import shlex

import irc3
import pylast
import random
import requests
from irc3.plugins.command import command


def to_user_index(index):
    """Converts a zero-indexed value to a user-friendly value starting from 1"""
    return index + 1


def from_user_index(index):
    """Converts a user-supplied index to a value suitable for zero-indexed arrays"""
    index = int(index)
    return index - 1 if index >= 1 else index


@irc3.extend
def get_user_value(bot, username, key):
    try:
        return bot.db.get(username)[key]
    except (KeyError, TypeError):
        return None


@irc3.extend
def set_user_value(bot, username, key, value):
    data = {key: value}
    bot.db.set(username, **data)


@irc3.plugin
class RiceDB(object):
    requires = [
        'irc3.plugins.command',
        'irc3.plugins.storage',
    ]

    def __init__(self, bot):
        self.bot = bot
        try:
            self.lastfm = pylast.LastFMNetwork(api_key=self.bot.config[__name__]['lastfm_api_key'])
        except KeyError:
            self.bot.log.warn('Missing last.fm API key')

    def _generic_db(self, mask, target, args):
        # Get name of command _generic_db is being called from.
        mode = inspect.stack()[1][3]
        mode = mode if mode.endswith('s') else mode + 's'

        # Apply some sanity to the way docopt handles args with spaces.
        if args['<values>']:
            try:
                args['<values>'] = shlex.split(' '.join(args['<values>']))
            except ValueError:
                pass

        if args['--add']:
            values = self.bot.get_user_value(mask.nick, mode) or []
            for value in args['<values>']:
                values.append(value)
            self.bot.set_user_value(mask.nick, mode, values)
            return '{0} updated.'.format(mode)

        if args['--set']:
            values = args['<values>']
            self.bot.set_user_value(mask.nick, mode, values)
            return '{0} updated.'.format(mode)

        if args['--delete']:
            values = self.db.get_user_value(mask.nick, mode)
            if not values:
                return 'You do not have any {0} to remove.'.format(mode)
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
            self.bot.set_user_value(mask.nick, mode, values)
            return 'Removed {0}.'.format(', '.join(deleted))

        if args['--replace']:
            index = from_user_index(args['<index>'])
            replacement = args['<value>']
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
                indexed_values.append('[{0}] {1}'.format(to_user_index(index), item))
            return '{0} [{1}]'.format(' | '.join(indexed_values), self.bot.antiping(user))
        else:
            return '{0} no {1}.'.format(
                self.bot.antiping(user) + ' has' if user != mask.nick else 'You have',
                'reason to live' if random.random() <= 0.15 else mode)

    @command(permission='view')
    def dtop(self, mask, target, args):
        """View or add a desktop.

            %%dtop [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def dotfiles(self, mask, target, args):
        """View or add dotfiles.

            %%dotfiles [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def distro(self, mask, target, args):
        """View or add a distro.

            %%distro [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def homescreen(self, mask, target, args):
        """View or add a homescreen.

            %%homescreen [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='view')
    def selfie(self, mask, target, args):
        """View or add a selfie.

            %%selfie [(--set <values>... | --add <values>... | --delete <indexes>... | --replace <index> <value>) | <user>]
        """
        yield self._generic_db(mask, target, args)

    @command(permission='admin', show_in_help_list=False)
    def mirror_aigis(self, mask, target, args):
        """Update local DB from Aigis' latest version.

            %%mirror_aigis
        """
        server = 'Rizon'
        db_map = {
            'dtops': 'desktops',
            'homescreens': 'homescreens',
            'selfies': 'selfies',
            'dotfiles': 'gits'
        }

        self.bot.log.info('Updating user database...')
        for db in db_map:
            r = requests.get('https://api.joaquin-v.xyz/aigis/database.php?server={0}&db={1}'.format(
                server, db_map[db]))
            data = r.json()
            if 'error_msg' in data:
                self.bot.log.error(data['error_msg'])
                continue
            for user in data:
                if data[user]:
                    self.bot.set_user_value(user, db, data[user])
        yield 'Database updated.'

    @command(name='np', permission='view')
    def now_playing(self, mask, target, args):
        """View currently playing track info.

            %%np [--set <username> | <username>]
        """
        if args['--set']:
            lastfm_username = args['<username>']
            try:
                lastfm_username = self.lastfm.get_user(lastfm_username).get_name(properly_capitalized=True)
            except pylast.WSError:
                return 'No such last.fm user. Are you trying to trick me? :^)'
            else:
                self.bot.set_user_value(mask.nick, 'lastfm', lastfm_username)
                return 'last.fm username set.'

        irc_username = args['<username>'] or mask.nick
        lastfm_username = self.bot.get_user_value(irc_username, 'lastfm')
        if not lastfm_username:
            if irc_username == mask.nick:
                return 'You have no last.fm username set. Please set one with .np --set <username>'
            return '{0} has no last.fm username set. Ask them to set one with .np --set <username>'.format(
                self.bot.antiping(irc_username))

        lastfm_user = self.lastfm.get_user(lastfm_username)
        current_track = lastfm_user.get_now_playing()
        if not current_track:
            return '{0} is not listening to anything right now.'.format(self.bot.antiping(irc_username))

        trackinfo = '{0} - {1}'.format(
            self.bot.bold(current_track.get_artist().get_name()), self.bot.bold(current_track.get_title()))
        return '{0} is now playing {1} | {2}'.format(
            self.bot.antiping(irc_username), trackinfo, self.bot.color(current_track.get_url(), 2))
