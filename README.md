RiceDB
======

An IRC bot designed to maintain a database of user submitted links to various subjects including desktops, mobile phone homescreens, dotfiles and operating systems  
Primarily designed with [#rice@irc.rizon.net](https://qchat.rizon.net/?channels=rice) in mind.

# Installation

As with all Python programs, I recommend you familiarise yourself with, and run this program inside a Python 3 [virtualenv](https://virtualenv.pypa.io/en/stable).

```sh
pip install -r requirements.txt
cp config.ini.dist config.ini
$EDITOR config.ini
irc3 config.ini
```
