RiceDB
======

An IRC bot designed to maintain a database of user submitted links to various subjects including desktops, mobile phone homescreens, dotfiles and operating systems  
Primarily designed with [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice) in mind.

ricedb was developed against Python 3.6, but *should* run on Python 3.5.

# Installation

## Docker


```sh
docker build -t ricedb .

# Run in the foreground.
docker run --mount type=bind,source=(pwd)/data,target=/app/data ricedb

# Run automatically in the background when dockerd starts.
docker run -d --name ricedb --restart unless-stopped --mount type=bind,source=$(pwd)/data,target=/app/data ricedb

docker (start|stop|restart|logs) ricedb
```

## Standalone

```sh
pip install -r requirements.txt
cp config.ini.dist config.ini
$EDITOR config.ini
irc3 config.ini
```
