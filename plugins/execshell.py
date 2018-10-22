import subprocess
import irc3
from irc3.plugins.command import command


def _exec_wrapper(cmd, input_data=None):
    if input_data:
        input_data = input_data.encode('UTF-8')

    proc = subprocess.run(cmd,
                          input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)

    if proc.returncode == 0:
        return proc.stdout.decode('UTF-8')

    return proc.stderr.decode('UTF-8')


@irc3.plugin
class ExecShell(object):
    requires = [
        'irc3.plugins.command',
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='admin', show_in_help_list=False, options_first=True)
    def exec(self, mask, target, args):
        """Run a system command and upload the output to ix.io.

            %%exec <command>...
        """

        cmd = args['<command>']
        output = _exec_wrapper(cmd)
        paste_url = _exec_wrapper(['curl', '--silent', '-F', 'f:1=@-', 'ix.io'], output)

        return f'{mask.nick}: {paste_url}'
