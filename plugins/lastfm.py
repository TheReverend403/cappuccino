import irc3
import pylast
from irc3.plugins.command import command

DB_KEY = 'lastfm'
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
            self.bot.log.error('Missing last.fm API key')
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
                    self.bot.set_user_value(mask.nick, DB_KEY, lastfm_username)
                    return 'last.fm username set.'

            base_command = self.bot.config.cmd + 'np'
            irc_username = args['<username>'] or mask.nick
            lastfm_username = self.bot.get_user_value(irc_username, DB_KEY)

            if not lastfm_username:
                if irc_username == mask.nick:
                    return f'You have no last.fm username set. ' \
                           f'Please set one with {base_command} --set <username>'

                return f'{irc_username} has no last.fm username set. ' \
                       f'Ask them to set one with {base_command} --set <username>'

            try:
                lastfm_user = self.lastfm.get_user(lastfm_username)
            except pylast.WSError:
                return f'No such last.fm user ({lastfm_username}). ' \
                       f'Please set a valid user with {base_command} --set <username>'

            formatted_name = irc_username
            if irc_username.lower() != lastfm_username.lower():
                formatted_name += f' ({lastfm_username})'

            current_track = lastfm_user.get_now_playing()
            if not current_track:
                return f'{formatted_name} is not listening to anything right now.'

            artist = current_track.get_artist().get_name().strip()
            title = current_track.get_title().strip()

            if len(artist) > MAX_TRACK_ARTIST_LEN:
                artist = ''.join(artist[:MAX_TRACK_ARTIST_LEN]) + '...'
            if len(title) > MAX_TRACK_TITLE_LEN:
                title = ''.join(title[:MAX_TRACK_TITLE_LEN]) + '...'

            artist = self.bot.format(artist, bold=True)
            title = self.bot.format(title, bold=True)
            track_info = f'{title} by {artist}'

        except (pylast.NetworkError, pylast.MalformedResponseError, pylast.WSError) as err:
            error = self.bot.format(err, bold=True)
            return f'{mask.nick}: A last.fm error occurred: {error}'

        return f'{formatted_name} is now playing {track_info}'
