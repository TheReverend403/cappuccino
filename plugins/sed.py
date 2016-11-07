from subprocess import Popen, PIPE
import irc3


class Editor(object):
    """
    Wrapper to provide ed-style line editing.
    https://gist.github.com/rduplain/3441687
    Ron DuPlain <ron.duplain@gmail.com>
    """

    def __init__(self, command):
        self.command = command

    def sed_wrapper(self, text):
        """Wrap sed to provide full ed-style line-editing.

        Being the stream editor, open sed in a subprocess and communicate with it
        using stdio, raising a sensible exception if the command call does not
        succeed.

        Note this wrapper deals with shell injection attempts:
        >>> sed_wrapper('Hello, world!', 's/world/friends/; ls')
        Traceback (most recent call last):
           ...
        EditorException: sed: -e expression #1, char 20: extra characters after command
        >>> sed_wrapper('Hello, world!', '; ls')
        Traceback (most recent call last):
           ...
        EditorException: sed: -e expression #1, char 4: extra characters after command
        >>>
        """
        arguments = ['sed', self.command]
        sed = Popen(arguments, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        sed.stdin.write(bytes(text.strip(), 'UTF-8'))
        sed.stdin.close()
        returncode = sed.wait()
        if returncode != 0:
            # Unix integer returncode, where 0 is success.
            raise EditorException(sed.stderr.read().decode('UTF-8').strip().replace('sed: -e ', ''))
        return sed.stdout.read().decode('UTF-8').strip()

    def edit(self, text):
        r"""Edit given text using ed-style line editing, using system's sed command.

        Examples:
        >>> edit('Hello, world!', 's/world/friends/')
        u'Hello, friends!'
        >>> edit('Hello, world!', 'bad_input')
        Traceback (most recent call last):
           ...
        EditorException: sed: can't find label for jump to `ad_input'
        >>>

        Boring empty cases are handled gracefully:
        >>> edit('Hello, world!', '')
        u'Hello, world!'
        >>> edit('', 's/world/friends/')
        u''
        >>> edit('', '')
        u''
        >>>

        This is a full ed implementation:
        >>> edit('Hello hello, world! HELLO!', 's/hello/greetings/gi')
        u'greetings greetings, world! greetings!'
        >>> edit('Hello, world!', r's/\(.*\)/You said, "\1"/')
        u'You said, "Hello, world!"'
        >>>

        A note on backslash escaping for sed, remember that Python has it's own
        escaping. For example, "backslash one" must either be \\1 or provided in a
        raw string, r'\1'.

        >>> edit('Hello, world!', 's/\\(.*\\)/\\U\\1/')
        u'HELLO, WORLD!'
        >>> edit('Hello, world!', r's/\(.*\)/\U\1/')
        u'HELLO, WORLD!'
        >>>
        """
        output = self.sed_wrapper(text)
        if not output:
            return text
        return output


class EditorException(RuntimeError):
    """An error occured while processing the editor command."""


@irc3.plugin
class Plugin(object):
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

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG '
                r'(?P<target>\S+) :\s*'
                r'(?P<sed>s/.+)')
    def sed(self, mask, target, sed):
        if target in self.history_buffer:
            last_message = self.history_buffer.get(target)
            if not last_message:
                return

            (user, message), = last_message.items()
            editor = Editor(sed)
            try:
                message = editor.edit(message)
            except EditorException as error:
                self.bot.log.error(error)
                self.bot.privmsg(target, '{0}: {1}'.format(mask.nick, error))
            else:
                self.bot.privmsg(target, '<{0}> {1}'.format(user, message))
