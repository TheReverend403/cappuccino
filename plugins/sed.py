from subprocess import Popen, PIPE

import collections
import irc3
import re

SED_PRIVMSG = r'\s*s[^A-Za-z0-9\s].+'
SED_CHECKER = re.compile('^' + SED_PRIVMSG)


class Editor(object):
    """
    Wrapper to provide ed-style line editing.
    https://gist.github.com/rduplain/3441687
    Ron DuPlain <ron.duplain@gmail.com>
    """

    def __init__(self, command):
        """A wrapper around UNIX sed, for operating on strings with sed expressions.

        Args:
            command: Any valid sed s/ expression.

        Example:
            >>> editor = Editor('s/Hello/Greetings/')
            >>> print(editor.edit('Hello World!'))
            "Greetings World!"
            >>> print(editor.edit('Hello World!', 's/World!/World\./'))
            "Hello World."
            >>> print(editor.edit('Hello, World'))
            "Greetings, World"
        """

        self.command = command

    def _sed_wrapper(self, text, command=None):
        arguments = ['sed', '--posix', '--regexp-extended', command or self.command]
        sed = Popen(arguments, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        sed.stdin.write(bytes(text.strip(), 'UTF-8'))
        sed.stdin.close()
        returncode = sed.wait()
        if returncode != 0:
            # Unix integer returncode, where 0 is success.
            raise EditorException(sed.stderr.read().decode('UTF-8').strip().replace('sed: -e ', ''))
        return sed.stdout.read().decode('UTF-8').strip()

    def edit(self, text, command=None):
        """Run this Editor's sed command against :text.

        Args:
            text: Text to run sed command against.
            command: An optional command to use for this specific operation.
        Returns:
            Resulting text after sed operation.
        Raises:
            EditorException: Details of sed errors.
        """
        output = self._sed_wrapper(text, command or self.command)
        if not output or output == text:
            return text
        return output


class EditorException(Exception):
    """An error occurred while processing the editor command."""


@irc3.plugin
class Sed(object):
    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.history_buffer = {}

    @irc3.event(irc3.rfc.PRIVMSG)
    def update_chat_history(self, target, event, mask, data):
        if event != 'PRIVMSG' or SED_CHECKER.match(data) or data.startswith(self.bot.config.cmd):
            return

        # Strip ACTION data and just use the message.
        data = data.replace('\x01ACTION ', '').replace('\x01', '')
        line = (mask.nick, data)

        if target in self.history_buffer:
            self.history_buffer[target].append(line)
            return

        queue = collections.deque(maxlen=25)
        queue.append(line)
        self.history_buffer.update({target: queue})

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :(?P<_sed>{0})'.format(SED_PRIVMSG))
    def sed(self, mask, target, _sed):
        if target not in self.history_buffer:
            return

        editor = Editor(_sed)
        for target_user, message in reversed(self.history_buffer[target]):
            message = message.strip()
            try:
                new_message = editor.edit(message)
            except EditorException as error:
                self.bot.log.error(error)
                if 'unterminated' not in str(error):
                    self.bot.privmsg(target, '{0}: {1}'.format(self.bot.format(mask.nick, antiping=True), error))
                # Don't even check the rest if the sed command is invalid.
                return

            if not new_message or new_message == message:
                continue

            # Prevent spam.
            max_extra_chars = 32
            max_len = len(message) + max_extra_chars
            error_msg = 'Replacement would be too long. I won\'t post it to prevent potential spam.'
            if len(new_message) > len(error_msg) and len(new_message) > max_len or len(new_message) > 256:
                self.bot.privmsg(target, '{0}: {1}'.format(
                    self.bot.format(mask.nick, antiping=True), self.bot.format(error_msg, color=self.bot.color.RED)))
                return

            emphasised_meant = self.bot.format('meant', bold=True)
            if mask.nick == target_user:
                if target.is_channel:
                    prefix = '{0} {1} to say:'.format(self.bot.format(mask.nick, antiping=True), emphasised_meant)
                else:
                    self.bot.privmsg(mask.nick, new_message)
                    return
            else:
                prefix = '{0} thinks {1} {2} to say:'.format(
                    self.bot.format(mask.nick, antiping=True), target_user, emphasised_meant)
            self.bot.privmsg(target, '{0} {1}'.format(prefix, new_message))
            return
