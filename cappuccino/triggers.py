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
from sqlalchemy import String, delete, func, select, update
from sqlalchemy.orm import Mapped, mapped_column

from cappuccino import BaseModel, Plugin
from cappuccino.util.channel import is_chanop
from cappuccino.util.formatting import Color, style


class Trigger(BaseModel):
    __tablename__ = "triggers"

    trigger: Mapped[str] = mapped_column(String(), nullable=False, primary_key=True)
    channel: Mapped[str] = mapped_column(String(), nullable=False, primary_key=True)
    response: Mapped[str] = mapped_column(String(), nullable=False)


@irc3.plugin
class Triggers(Plugin):
    requires = ["irc3.plugins.command", "irc3.plugins.userlist"]

    def __init__(self, bot):
        super().__init__(bot)

    def _get_trigger(self, channel: str, trigger: str):
        return self.db_session.scalar(
            select(Trigger.response)
            .where(func.lower(Trigger.trigger) == trigger.lower())
            .where(func.lower(Trigger.channel) == channel.lower())
        )

    def _set_trigger(self, channel: str, trigger: str, text: str):
        trigger_model = self.db_session.scalar(
            update(Trigger)
            .returning(Trigger)
            .where(func.lower(Trigger.trigger) == trigger.lower())
            .where(func.lower(Trigger.channel) == channel.lower())
            .values(response=text)
        )

        if trigger_model is None:
            trigger_model = Trigger(trigger=trigger, channel=channel, response=text)
            self.db_session.add(trigger_model)

        self.db_session.commit()

    def _delete_trigger(self, channel: str, trigger: str) -> bool:
        return (
            self.db_session.scalar(
                delete(Trigger)
                .where(func.lower(Trigger.trigger) == trigger.lower())
                .where(func.lower(Trigger.channel) == channel.lower())
                .returning(Triggers.trigger)
            )
            is not None
        )

    def _get_triggers_list(self, channel: str) -> list:
        return self.db_session.scalars(
            select(Trigger.trigger).where(
                func.lower(Trigger.channel) == channel.lower()
            )
        ).all()

    @command(permission="view")
    def trigger(self, mask, target, args):
        """Manages predefined responses to message triggers.

        %%trigger (set <trigger> <response>... | del <trigger> | list)
        """

        if not target.is_channel:
            return "This command can only be used in channels."

        if (args["set"] or args["del"]) and not is_chanop(self.bot, target, mask.nick):
            return "Only channel operators may modify channel triggers."

        response = None
        trigger = args["<trigger>"]

        if args["set"]:
            self._set_trigger(target, trigger, " ".join(args["<response>"]))
            response = f"Trigger '{trigger}' set."
        elif args["del"]:
            response = (
                f"Deleted trigger '{trigger}'."
                if self._delete_trigger(target, trigger)
                else "No such trigger."
            )
        elif args["list"]:
            trigger_list = self._get_triggers_list(target)
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
