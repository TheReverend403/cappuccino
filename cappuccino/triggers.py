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

import re

import irc3
from irc3.plugins.command import command
from sqlalchemy import delete, func, select, update

from cappuccino import Plugin
from cappuccino.db.models.triggers import Trigger
from cappuccino.util.channel import is_chanop
from cappuccino.util.formatting import Color, style


@irc3.plugin
class Triggers(Plugin):
    requires = ["irc3.plugins.command", "irc3.plugins.userlist"]

    def __init__(self, bot):
        super().__init__(bot)

    def _get_trigger(self, channel: str, name: str):
        with self.db_session() as session:
            return session.scalar(
                select(Trigger.response)
                .where(func.lower(Trigger.name) == name.lower())
                .where(func.lower(Trigger.channel) == channel.lower())
            )

    def _set_trigger(self, channel: str, name: str, response: str):
        with self.db_session() as session:
            trigger_model = session.scalar(
                update(Trigger)
                .returning(Trigger)
                .where(func.lower(Trigger.name) == name.lower())
                .where(func.lower(Trigger.channel) == channel.lower())
                .values(response=response)
            )

            if trigger_model is None:
                trigger_model = Trigger(name=name, channel=channel, response=response)
                session.add(trigger_model)

    def _delete_trigger(self, channel: str, name: str) -> bool:
        with self.db_session() as session:
            trigger_object = session.scalar(
                delete(Trigger)
                .where(func.lower(Trigger.name) == name.lower())
                .where(func.lower(Trigger.channel) == channel.lower())
                .returning(Trigger)
            )
            return trigger_object is not None

    def _get_triggers_list(self, channel: str) -> list:
        with self.db_session() as session:
            return session.scalars(
                select(Trigger.name).where(
                    func.lower(Trigger.channel) == channel.lower()
                )
            ).all()

    @command(permission="view")
    def trigger(self, mask, target, args):
        """Manages predefined responses to message triggers.

        %%trigger (set <name> <response>... | del <name> | list)
        """

        if not target.is_channel:
            return "This command can only be used in channels."

        if (args["set"] or args["del"]) and not is_chanop(self.bot, target, mask.nick):
            return "Only channel operators may modify channel triggers."

        response = None
        name = args["<name>"]

        if args["set"]:
            self._set_trigger(target, name, " ".join(args["<response>"]))
            response = f"Trigger '{name}' set."
        elif args["del"]:
            response = (
                f"Deleted trigger '{name}'."
                if self._delete_trigger(target, name)
                else "No such trigger."
            )
        elif args["list"]:
            trigger_list = self._get_triggers_list(target)
            self.logger.debug(trigger_list)
            if trigger_list:
                trigger_list = ", ".join(trigger_list)
                response = f"Available triggers for {target}: {trigger_list}"
            else:
                response = f"No triggers available for {target}"

        return response

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, target, event, mask, data):
        if mask.nick == self.bot.nick or event == "NOTICE":
            return

        captured_triggers = re.findall(r"\?([A-Za-z0-9]+)", data)
        if not captured_triggers:
            return

        triggers = set(captured_triggers[:3])
        responses = []
        for trigger in triggers:
            response = self._get_trigger(target, trigger)
            trigger = style(trigger.lower(), fg=Color.ORANGE)
            if response is not None:
                responses.append(f"[{trigger}] {response}")

        for response in responses:
            self.bot.privmsg(target, response)
