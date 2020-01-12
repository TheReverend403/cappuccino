Cappuccino
======

An IRC bot providing various utilities primarily for [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice). 

Requires Python 3.6 or above.

# Installation

First, install [Poetry](https://poetry.eustace.io/)

```sh
poetry install # Optionally install plugin dependencies with: --extras 'sentry ai lastfm'
cp config.ini.dist config.ini
$EDITOR config.ini
poetry run irc3 config.ini
```
