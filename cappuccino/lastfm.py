#  This file is part of cappuccino.
#
#  cappuccino is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cappuccino is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cappuccino.  If not, see <https://www.gnu.org/licenses/>.

import irc3
import pylast
from irc3.plugins.command import command

from cappuccino import Plugin
from cappuccino.util.formatting import style, truncate_with_ellipsis

_DB_KEY = "lastfm"
_MAX_TRACK_ARTIST_LEN = 32
_MAX_TRACK_TITLE_LEN = 75


def _add_lastfm_suffix(irc_username: str, lastfm_username: str) -> str:
    """
    Adds a last.fm username as a suffix to the IRC user info if the two are not equal.
    """

    if irc_username.lower() != lastfm_username.lower():
        return f"{irc_username} ({lastfm_username})"
    return irc_username


@irc3.plugin
class LastFM(Plugin):
    requires = ["irc3.plugins.command", "cappuccino.userdb"]

    def __init__(self, bot):
        super().__init__(bot)

        api_key = self.config.get("api_key", None)
        if not api_key:
            self.logger.error("Missing last.fm API key")
            return

        self._lastfm = pylast.LastFMNetwork(api_key=api_key)

    def _set_lastfm_username(self, irc_username: str, lastfm_username: str) -> str:
        """Verify and set a user's last.fm username."""
        try:
            lastfm_username = self._lastfm.get_user(lastfm_username).get_name(
                properly_capitalized=True
            )
        except pylast.WSError:
            return "That user doesn't appear to exist. Are you trying to trick me? :^)"
        else:
            self.bot.set_user_value(irc_username, _DB_KEY, lastfm_username)
            return "Last.fm account linked successfully."

    @command(name="np", permission="view", aliases=["lastfm"])
    def now_playing(self, mask, target, args):
        """View currently playing track info.

        %%np [(-s | --set) <username> | <username>]
        """

        if args["--set"] or args["-s"]:
            return self._set_lastfm_username(mask.nick, args["<username>"])

        base_command = f"{self.bot.config.cmd}np"
        irc_target_username = args["<username>"] or mask.nick
        lastfm_username = self.bot.get_user_value(irc_target_username, _DB_KEY)

        try:
            if not lastfm_username:
                if irc_target_username == mask.nick:
                    return (
                        f"You have not linked a Last.fm account."
                        f" Please do so with {base_command} --set <username>"
                    )

                return (
                    f"{irc_target_username} has not linked a Last.fm account."
                    f" Ask them to link one with {base_command} --set <username>"
                )

            try:
                lastfm_user = self._lastfm.get_user(lastfm_username)
                lastfm_username = lastfm_user.get_name(properly_capitalized=True)
            except pylast.WSError:
                if irc_target_username == mask.nick:
                    return (
                        f"Your Last.fm account appears to no longer exist."
                        f" Please link a new one with {base_command} --set <username>"
                    )

                possessive_nick = (
                    f"{irc_target_username}'"
                    if irc_target_username.endswith("s")
                    else f"{irc_target_username}'s"
                )
                return (
                    f"{possessive_nick} last.fm account appears to no longer exist."
                    f" Ask them to link a new one with {base_command} --set <username>"
                )

            name_tag = _add_lastfm_suffix(irc_target_username, lastfm_username)
            current_track = lastfm_user.get_now_playing()
            if not current_track:
                return f"{name_tag} is not listening to anything right now."

            artist = current_track.get_artist().get_name().strip()
            title = current_track.get_title().strip()
            artist = truncate_with_ellipsis(artist, _MAX_TRACK_ARTIST_LEN)
            title = truncate_with_ellipsis(title, _MAX_TRACK_TITLE_LEN)
            artist = style(artist, bold=True)
            title = style(title, bold=True)
            track_info = f"{title} by {artist}"
            return f"{name_tag} is now playing {track_info}"
        except (
            pylast.NetworkError,
            pylast.MalformedResponseError,
            pylast.WSError,
        ) as err:
            return style(err, bold=True)
