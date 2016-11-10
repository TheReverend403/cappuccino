from pprint import pprint

import re
from subprocess import Popen, PIPE

import irc3
from collections import OrderedDict

SED_START = r's[#/\\.|,].+'


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


class ChatHistoryFifo(OrderedDict):
    """
    Store items in the order the keys were last updated.
    Evicts the oldest entry when len > max_size.
    """
    max_size = 20

    def __init__(self, *args, **kwds):
        if 'max_size' in kwds:
            self.max_size = kwds['max_size']
            del kwds['max_size']
        super().__init__(*args, **kwds)

    def __setitem__(self, key, value, **kwargs):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value, **kwargs)
        if self.__len__() > self.max_size:
            OrderedDict.popitem(self, last=False)


@irc3.plugin
class Sed(object):

    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.history_buffer = {}

    @irc3.event(irc3.rfc.PRIVMSG)
    def chat_history(self, target, event, mask, data):
        # Strip ACTION data and just use the message.
        data = data.replace('\x01ACTION ', '').replace('\x01', '')
        if event != 'PRIVMSG' or not target.is_channel or re.match(r'^\s*' + SED_START, data):
            return
        message = {mask.nick: data}
        if target in self.history_buffer:
            if len(self.history_buffer[target]) > 0:
                self.history_buffer[target].update(message)
        else:
            self.history_buffer.update({target: ChatHistoryFifo(message)})
        self.bot.log.debug(self.history_buffer)

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :\s*(?P<_sed>{0})'.format(SED_START))
    def sed(self, mask, target, _sed):
        if target in self.history_buffer:
            editor = Editor(_sed)
            for user, message in self.history_buffer[target].items():
                try:
                    new_message = editor.edit(message)
                except EditorException as error:
                    self.bot.log.error(error)
                    self.bot.privmsg(target, '{0}: {1}'.format(self.bot.antiping(mask.nick), error))
                else:
                    if new_message == message:
                        continue
                    # Prevent spam.
                    max_extra_chars = 32
                    max_len = len(message) + max_extra_chars
                    if len(new_message) > max_len:
                        error_msg = 'Replacement would be too long. I won\'t post it to prevent potential spam.'
                        self.bot.privmsg(target, '{0}: {1}'.format(
                            self.bot.antiping(mask.nick), self.bot.color(error_msg, 4)))
                        return
                    emphasised_meant = self.bot.bold('meant')
                    if mask.nick == user:
                        self.bot.privmsg(target, '{0} {1} to say: {2}'.format(
                            self.bot.antiping(mask.nick), emphasised_meant, new_message))
                    else:
                        self.bot.privmsg(target, '{0} thinks {1} {2} to say: {3}'.format(
                            self.bot.antiping(mask.nick), user, emphasised_meant, new_message))
                    return
