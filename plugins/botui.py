import platform

from irc3.plugins.command import command
import irc3


@irc3.extend
def antiping(bot, text):
    """Adds zero-width spaces after each character in a string to avoid pinging users"""
    return '\u200B'.join(text)


@irc3.extend
def color(bot, text, colorvalue):
    # TODO: Add constants for IRC colours.
    return '\x030{0}{1}\x0f'.format(colorvalue, text)


@irc3.extend
def bold(bot, text):
    return '\x02{0}\x0f'.format(text)


@irc3.plugin
class Plugin(object):

    requires = [
        'irc3.plugins.command',
        'irc3.plugins.userlist'
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def bots(self, mask, target, args):
        """Report in!

            %%bots
        """
        yield 'Reporting in! [Python {0}]'.format(platform.python_version())

    @command(permission='admin', show_in_help_list=False)
    def join(self, mask, target, args):
        """Join a channel.

            %%join <channel> [<password>]
        """

        channel = args['<channel>']
        if args['<password>'] is not None:
            channel += ' %s' % args['<password>']

        self.bot.join(channel)

    @command(permission='admin', show_in_help_list=False)
    def part(self, mask, target, args):
        """Leave a channel.

            %%part [<channel>]
        """

        if args['<channel>'] is not None:
            target = args['<channel>']

        self.bot.part(target)

    @command(permission='admin', show_in_help_list=False)
    def nick(self, mask, target, args):
        """Change nickname of the bot.

            %%nick <nick>
        """

        self.bot.set_nick(args['<nick>'])

    @command(permission='admin', show_in_help_list=False)
    def mode(self, mask, target, args):
        """Set user mode for the bot.

            %%mode <mode-cmd>
        """

        self.bot.mode(self.bot.nick, args['<mode-cmd>'])

    @command(permission='admin', show_in_help_list=False)
    def msg(self, mask, target, args):
        """Send a message.

            %%msg <target> <message>...
        """

        msg = ' '.join(args['<message>'] or [])
        self.bot.privmsg(args['<target>'], msg)

    @command(permission='admin', show_in_help_list=False)
    def quote(self, mask, target, args):
        """Send a raw string to the IRCd.

           %%quote <string>...
        """
        cmd = ' '.join(args['<string>'] or [])
        yield 'Sending {}'.format(cmd)
        self.bot.send(cmd)

    @command(permission='admin', show_in_help_list=False)
    def psa(self, mask, target, args):
        """Broadcast a public service announcement to all channels.

            %%psa <message>...
        """
        for channel in self.bot.channels:
            self.bot.privmsg(channel, '[PSA] {0}'.format(' '.join(args['<message>'])))
