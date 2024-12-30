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

import inspect
import re

import irc3
from irc3.plugins.command import command

from cappuccino import Plugin
from cappuccino.util.formatting import Color, style


def _to_user_index(index: int):
    """Converts a zero-indexed value to a user-friendly value starting from 1"""
    return index + 1


def _from_user_index(index: int):
    """Converts a user-supplied index to a value suitable for zero-indexed arrays"""
    index = int(index)
    return index - 1 if index >= 1 else index


@irc3.plugin
class Rice(Plugin):
    requires = ["irc3.plugins.command", "cappuccino.userdb"]

    def __init__(self, bot):
        super().__init__(bot)
        self._max_user_entries: int = self.config.get("max_user_entries", 6)

    def _generic_db(self, mask, target, args):  # noqa: C901
        # Get name of command _generic_db is being called from.
        category = inspect.stack()[1][3]
        category = category if category.endswith("s") else category + "s"

        if args["<values>"]:
            args["<values>"] = [arg.strip() for arg in args["<values>"] if arg.strip()]

            if len(args["<values>"]) == 0:
                return f"{category} cannot be empty!"

        response = None

        if args["--add"] or args["-a"]:
            values = self.bot.get_user_value(mask.nick, category) or []
            if len(values) + len(args["<values>"]) > self._max_user_entries:
                response = (
                    f"You can only set {self._max_user_entries} {category}!"
                    f" Consider deleting or replacing some."
                )
            else:
                for value in args["<values>"]:
                    values.append(value)
                self.bot.set_user_value(mask.nick, category, values)
                response = f"{category} updated."

        elif args["--set"] or args["-s"]:
            values = args["<values>"]
            if len(values) > self._max_user_entries:
                response = (
                    f"You can only set {self._max_user_entries} {category}!"
                    f" Consider deleting or replacing some."
                )
            else:
                self.bot.set_user_value(mask.nick, category, values)
                response = f"{category} updated."

        elif args["--delete"] or args["-d"]:
            values = self.bot.get_user_value(mask.nick, category)
            if not values:
                response = f"You do not have any {category} to remove."
            else:
                indexes = set(args["<ids>"])
                if "*" in indexes:
                    self.bot.del_user_value(mask.nick, category)
                    response = f"Removed all of your {category}."
                else:
                    deleted_list = []
                    for index in sorted(indexes, reverse=True):
                        try:
                            index = _from_user_index(index)
                            deleted_list.append(values[index])
                            del values[index]
                        except IndexError:
                            pass
                        except ValueError:
                            response = "Invalid ID(s)"
                            break
                    if not response:
                        if not deleted_list:
                            response = f"No {category} were removed. Maybe you supplied the wrong IDs?"
                        else:
                            self.bot.set_user_value(mask.nick, category, values)
                            deleted_list = ", ".join(
                                [style(deleted, reset=True) for deleted in deleted_list]
                            )
                            response = f"Removed {deleted_list}."

        elif args["--replace"] or args["-r"]:
            try:
                index = _from_user_index(args["<id>"])
            except ValueError:
                response = "Invalid ID"
            else:
                replacement = args["<value>"].strip()
                values = self.bot.get_user_value(mask.nick, category)
                if not values:
                    response = f"You do not have any {category} to replace."
                else:
                    try:
                        old_value = values[index]
                        values[index] = replacement
                        self.bot.set_user_value(mask.nick, category, values)
                        old_value = style(old_value, reset=True)
                        replacement = style(replacement, reset=True)
                        response = f"Replaced {old_value} with {replacement}"
                    except IndexError:
                        response = "Invalid ID."

        elif args["<user>"] is not None and re.match(
            "^https?://.*", args["<user>"], re.IGNORECASE | re.DOTALL
        ):
            response = "Did you mean to use --add (-a) or --set (-s) there?"

        elif (
            args["<user>"] is not None
            and args["<user>"].isdigit()
            and args["<id>"] is None
        ):
            args["<user>"], args["<id>"] = None, args["<user>"]

        if response:
            return response

        seperator = style(" | ", fg=Color.LIGHT_GRAY)
        user = args["<user>"] or mask.nick
        user_prefix = style("[", fg=Color.LIGHT_GRAY)
        user_suffix = style("]", fg=Color.LIGHT_GRAY)
        user_tag = style(user, fg=Color.GREEN)
        user_tag = f"{user_prefix}{user_tag}{user_suffix}"

        if args["<id>"] is not None:
            try:
                index = _from_user_index(args["<id>"])
                value = self.bot.get_user_value(user, category)[index]
            except (ValueError, IndexError, TypeError):
                return "Invalid ID."
            value = style(value, reset=True)
            return f"{user_tag} {value}"

        values = self.bot.get_user_value(user, category)
        if values:
            indexed_values = []
            for index, item in enumerate(values):
                item = style(item, reset=True)
                if len(values) < 2:  # noqa: PLR2004
                    indexed_values.append(item)
                    break
                index = _to_user_index(index)
                id_prefix = style(f"#{index}", fg=Color.PURPLE)
                indexed_values.append(f"{id_prefix} {item}")
            formatted_values = seperator.join(indexed_values)
            return f"{user_tag} {formatted_values}"

        return f"{user} has no {category}."

    @command(permission="view")
    def station(self, mask, target, args):
        """
        %%station [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view", aliases=["desktop", "dt"])
    def dtop(self, mask, target, args):
        """
        %%dtop [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view", aliases=["git"])
    def dotfiles(self, mask, target, args):
        """
        %%dotfiles [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view", aliases=["hw"])
    def handwriting(self, mask, target, args):
        """
        %%handwriting [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view")
    def distro(self, mask, target, args):
        """
        %%distro [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view", aliases=["phone", "hscr", "hs"])
    def homescreen(self, mask, target, args):
        """
        %%homescreen [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view")
    def selfie(self, mask, target, args):
        """
        %%selfie [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view")
    def pet(self, mask, target, args):
        """
        %%pet [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)

    @command(permission="view", aliases=["site"])
    def website(self, mask, target, args):
        """
        %%website [((-s | --set) <values>... | (-a | --add) <values>... | (-d | --delete) <ids>... | (-r | --replace) <id> <value>) | [<user>] [<id>]]
        """
        yield self._generic_db(mask, target, args)
