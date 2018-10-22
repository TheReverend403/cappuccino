import subprocess
import irc3
from irc3.plugins.command import command


def _exec_wrapper(cmd, input_data=None):
    if input_data:
        input_data = input_data.encode('UTF-8')

    proc = subprocess.run(cmd, input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if proc.returncode == 0:
        return proc.stdout.decode('UTF-8')

    return proc.stderr.decode('UTF-8')


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

        output = None
        try:
            output = _exec_wrapper(args['<command>'])
            if not output:
                return f'{mask.nick}: Command returned no output.'

            # Don't paste single line outputs.
            # Check if the output contains a newline after removing the last one for single-line output ending with \n
            if '\n' not in output[:-1]:
                return f'{mask.nick}: {output}'

            result = _exec_wrapper(['curl', '--silent', '-F', 'f:1=@-', 'ix.io'], output)
        except subprocess.TimeoutExpired:
            if output:
                return f'{mask.nick}: ix.io timed out.'

            return f'{mask.nick}: Command timed out.'
        except FileNotFoundError as ex:
            return f'{mask.nick}: {ex}'

        return f'{mask.nick}: {result}'
