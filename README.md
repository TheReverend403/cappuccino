RiceDB
======

An IRC bot designed to maintain a database of user submitted links to various subjects including desktops, mobile phone homescreens, dotfiles and operating systems  
Primarily designed with [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice) in mind.

ricedb was developed against Python 3.6, but *should* run on Python 3.5.

# Installation

As with all Python programs, I recommend you familiarise yourself with, and run this program inside of, a [virtualenv](https://virtualenv.pypa.io/en/stable) or [conda environment](https://github.com/conda/conda) running the latest supported Python release.

```sh
pip install -r requirements.txt
cp config.ini.dist config.ini
$EDITOR config.ini
irc3 config.ini
```
