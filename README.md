Cappuccino
======

[![License](https://img.shields.io/github/license/FoxDev/cappuccino.svg)](https://www.gnu.org/licenses/gpl.txt)
[![Requirements Status](https://requires.io/github/FoxDev/cappuccino/requirements.svg?branch=master)](https://requires.io/github/FoxDev/cappuccino/requirements/?branch=master)
[![Keybase PGP](https://img.shields.io/keybase/pgp/TheReverend403.svg)](https://keybase.io/thereverend403)

A set of [irc3](https://github.com/gawel/irc3) plugins providing various utilities primarily for [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice). 

Requires Python 3.6 or above.


# Installation

First, install [Poetry](https://poetry.eustace.io/)

```sh
poetry install # Optionally install plugin dependencies with: --extras 'sentry ai lastfm'
cp config.ini.dist config.ini
$EDITOR config.ini
poetry run irc3 config.ini
```
