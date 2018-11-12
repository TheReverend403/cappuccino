import subprocess
import irc3
import requests
from irc3.plugins.command import command


def is_multiline_string(text: str):
    return text.count('\n') > 1  # require minimum 2 newlines to account for the newline at the end of command output.


def _exec_wrapper(cmd: dict, input_data: str=None):
    if input_data:
        input_data = input_data.encode('UTF-8')

    proc = subprocess.run(cmd, input=input_data, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
    return proc.stdout.decode('UTF-8').strip()


@irc3.plugin
class ExecShell(object):
    requires = [
        'irc3.plugins.command'
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='admin', show_in_help_list=False, options_first=True, use_shlex=True)
    def exec(self, mask, target, args):
        """Run a system command and upload the output to ix.io.

            %%exec <command>...
        """

        try:
            output = _exec_wrapper(args['<command>'])
            if not output:
                return f'{mask.nick}: Command returned no output.'

            # Don't paste single line outputs.
            if not is_multiline_string(output):
                return f'{mask.nick}: {output}'

            # Upload result of command to ix.io to avoid flooding channels with long output.
            result = requests.post('http://ix.io', data={'f:1': output})

        except (FileNotFoundError, requests.RequestException, subprocess.TimeoutExpired) as ex:
            return f'{mask.nick}: {ex}.'

        return f'{mask.nick}: {result.text}'
