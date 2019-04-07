Cappuccino
======

An IRC bot providing various utilities primarily for [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice). 

Cappuccino is currently developed against Python 3.7 and not tested on earlier versions.

# Installation

## Docker


```sh
# Run in the foreground.
docker-compose up

# Run and detach (daemonise).
docker-compose up -d
```

## Standalone

```sh
pipenv install
cp config.ini.dist config.ini
$EDITOR config.ini
pipenv run irc3 config.ini
```

Or if you're still living in the past...

```sh
pip install -r requirements.txt
cp config.ini.dist config.ini
$EDITOR config.ini
irc3 config.ini
```
