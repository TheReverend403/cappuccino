RiceDB
======

An IRC bot designed to maintain a database of user submitted links to various subjects including desktops, mobile phone homescreens, dotfiles and operating systems  
Primarily designed with [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice) in mind.

ricedb was developed against Python 3.6, but *should* run on Python 3.5.

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
pip install -r requirements.txt
cp config.ini.dist config.ini
$EDITOR config.ini
irc3 config.ini
```
