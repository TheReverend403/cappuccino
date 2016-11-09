from subprocess import Popen, PIPE

import irc3


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
        arguments = ['sed', '--posix', command or self.command]
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
    def __init__(self, bot):
        self.bot = bot
        self.history_buffer = {}

    @irc3.event(irc3.rfc.PRIVMSG)
    def chat_history(self, target, event, mask, data):
        if event != 'PRIVMSG' or not target.is_channel or data.startswith('s/'):
            return
        if target in self.history_buffer:
            self.history_buffer.pop(target)
        self.history_buffer.update({target: {mask.nick: data}})

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :\s*(?P<sed>s/.+)')
    def sed(self, mask, target, sed):
        if target in self.history_buffer:
            last_message = self.history_buffer.get(target)
            if not last_message:
                return

            (user, message), = last_message.items()
            editor = Editor(sed)
            try:
                new_message = editor.edit(message)
            except EditorException as error:
                self.bot.log.error(error)
                self.bot.privmsg(target, '{0}: {1}'.format(mask.nick, error))
            else:
                if new_message == message:
                    self.bot.privmsg(target, '{0}: No modifications were made.'.format(mask.nick))
                    return
                # Prevent spam.
                max_len = 256
                if len(new_message) > max_len:
                    self.bot.privmsg(target, '{0}: Output would be too large. ({1}/{2} characters)'.format(
                        self.bot.antiping(mask.nick), len(new_message), max_len))
                    return
                emphasised_meant = self.bot.bold('meant')
                if mask.nick == user:
                    self.bot.privmsg(target, '{0} {1} to say: {2}'.format(
                        self.bot.antiping(mask.nick), emphasised_meant, new_message))
                else:
                    self.bot.privmsg(target, '{0} thinks {1} {2} to say: {3}'.format(
                        self.bot.antiping(mask.nick), user, emphasised_meant, new_message))
