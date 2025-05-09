#!/usr/bin/env python

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

import argparse
import errno
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

logging.basicConfig(
    format="[%(levelname)-5s] %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger(Path(__file__).name)


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    source_file: Path = args.source
    destination_file: Path = args.destination

    log.info(f"Templating {source_file} out to {destination_file}")

    env = Environment(
        loader=FileSystemLoader(source_file.parent), autoescape=select_autoescape()
    )

    try:
        template = env.get_template(source_file.name)
        rendered = template.render(
            **{key: val for (key, val) in os.environ.items() if key.startswith("CFG_")}
        )
        destination_file.write_text(rendered)
        log.info("Done.")
    except FileNotFoundError as exc:
        log.error(f"{exc.filename} does not exist.")  # noqa: TRY400
        sys.exit(errno.ENOENT)


if __name__ == "__main__":
    main()
