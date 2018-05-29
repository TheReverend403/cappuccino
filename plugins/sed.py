import collections
import irc3
import re

# Source: https://github.com/CloudBotIRC/CloudBot/blob/master/plugins/correction.py
SED_PRIVMSG = r's/(.*/.*(?:/[igx]{{,4}})?)\S*$'
SED_RE = re.compile(SED_PRIVMSG, re.I | re.UNICODE)


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
        if event != 'PRIVMSG' or SED_RE.match(data) or data.startswith(self.bot.config.cmd):
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

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :{re_cmd}(?P<_sed>{0})'.format(SED_PRIVMSG))
    def sed(self, mask, target, _sed):
        if target not in self.history_buffer:
            return

        match = SED_RE.match(_sed)
        groups = [b.replace('\/', '/') for b in re.split(r"(?<!\\)/", match.groups()[0])]
        sed_find = groups[0]
        sed_replacement = groups[1].replace('\n', '\\n').replace('\r', '\\r')

        for target_user, message in reversed(self.history_buffer[target]):
            message = message.strip()
            new_message = re.sub(sed_find, sed_replacement, message)

            if not new_message or new_message == message:
                continue

            # Prevent spam.
            max_extra_chars = 32
            max_len = len(message) + max_extra_chars
            error_msg = 'Replacement would be too long. I won\'t post it to prevent potential spam.'
            if len(new_message) > len(error_msg) and len(new_message) > max_len or len(new_message) > 256:
                self.bot.notice(mask.nick, self.bot.format(error_msg, color=self.bot.color.RED))
                return

            emphasised_meant = self.bot.format('meant', bold=True)
            if mask.nick == target_user:
                if target.is_channel:
                    prefix = '{0} {1} to say:'.format(mask.nick, emphasised_meant)
                else:
                    self.bot.privmsg(mask.nick, new_message)
                    return
            else:
                prefix = '{0} thinks {1} {2} to say:'.format(mask.nick, target_user, emphasised_meant)
            self.bot.privmsg(target, '{0} {1}'.format(prefix, new_message))
            return
