import irc3
import pylast
from irc3.plugins.command import command
from pyshorteners import Shortener
from pyshorteners.exceptions import UnknownShortenerException, ExpandingErrorException, ShorteningErrorException


@irc3.plugin
class LastFM(object):

    requires = [
        'irc3.plugins.command',
        'plugins.formatting',
        'plugins.userdb'
    ]

    def __init__(self, bot):
        self.bot = bot
        try:
            self.lastfm = pylast.LastFMNetwork(api_key=self.bot.config[__name__]['api_key'])
        except KeyError:
            self.bot.log.warn('Missing last.fm API key')
            return
        self.url_shortener = Shortener('Isgd', timeout=3)

    @command(name='np', permission='view')
    def now_playing(self, mask, target, args):
        """View currently playing track info.

            %%np [(-s | --set) <username> | <username>]
        """
        if args['--set'] or args['-s']:
            lastfm_username = args['<username>']
            try:
                lastfm_username = self.lastfm.get_user(lastfm_username).get_name(properly_capitalized=True)
            except pylast.WSError:
                return 'No such last.fm user. Are you trying to trick me? :^)'
            except pylast.NetworkError as err:
                return err
            else:
                self.bot.set_user_value(mask.nick, 'lastfm', lastfm_username)
                return 'last.fm username set.'

        irc_username = args['<username>'] or mask.nick
        lastfm_username = self.bot.get_user_value(irc_username, 'lastfm')
        if not lastfm_username:
            if irc_username == mask.nick:
                return 'You have no last.fm username set. Please set one with .np --set <username>'
            return '{0} has no last.fm username set. Ask them to set one with .np --set <username>'.format(
                self.bot.format(irc_username, antiping=True))

        try:
            lastfm_user = self.lastfm.get_user(lastfm_username)
            current_track = lastfm_user.get_now_playing()
            if not current_track:
                return '{0} is not listening to anything right now.'.format(self.bot.format(irc_username, antiping=True))

            track_url = current_track.get_url()
            try:
                track_url = self.url_shortener.short(track_url)
            except (UnknownShortenerException, ShorteningErrorException, ExpandingErrorException) as err:
                self.bot.log.exception('Exception occurred while shortening {0}: {1}'.format(track_url, err))

            track_info = '{0} - {1} | {2}'.format(
                self.bot.format(current_track.get_artist().get_name(), bold=True),
                self.bot.format(current_track.get_title(), bold=True),
                self.bot.format(track_url, color=self.bot.color.BLUE))
        except pylast.NetworkError as err:
            return err
        return '{0} is now playing {1}'.format(self.bot.format(irc_username, antiping=True), track_info)
