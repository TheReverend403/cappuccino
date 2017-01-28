import irc3
import pylast
from irc3.plugins.command import command

MAX_TRACK_ARTIST_LEN = 32
MAX_TRACK_TITLE_LEN = 75


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

    @command(name='np', permission='view', aliases=['lastfm'])
    def now_playing(self, mask, target, args):
        """View currently playing track info.

            %%np [(-s | --set) <username> | <username>]
        """

        try:
            if args['--set'] or args['-s']:
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
                    return 'You have no last.fm username set. Please set one with {0}np --set <username>'.format(
                        self.bot.config.cmd)
                return '{0} has no last.fm username set. Ask them to set one with {1}np --set <username>'.format(
                    irc_username, self.bot.config.cmd)
            try:
                lastfm_user = self.lastfm.get_user(lastfm_username)
            except pylast.WSError:
                return 'No such last.fm user ({0}). Please set a valid user with {1}np --set <username>'.format(
                        lastfm_username, self.bot.config.cmd)

            current_track = lastfm_user.get_now_playing()
            if not current_track:
                return '{0} is not listening to anything right now.'.format(irc_username)

            artist = current_track.get_artist().get_name().strip()
            title = current_track.get_title().strip()

            if len(artist) > MAX_TRACK_ARTIST_LEN:
                artist = ''.join(artist[:MAX_TRACK_ARTIST_LEN]) + '...'
            if len(title) > MAX_TRACK_TITLE_LEN:
                title = ''.join(title[:MAX_TRACK_TITLE_LEN]) + '...'

            track_info = '{0} - {1}'.format(self.bot.format(artist, bold=True), self.bot.format(title, bold=True))
        except (pylast.NetworkError, pylast.MalformedResponseError) as err:
            return '{0}: A last.fm error occurred: {1}'.format(mask.nick, self.bot.format(err, bold=True))

        return '{0} is now playing {1}'.format(irc_username, track_info)
