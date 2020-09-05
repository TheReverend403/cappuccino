<p align="center">
  <img align="center" src="logo.png">
</p>

<h1 align="center">cappuccino</h1>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/github/license/FoxDev/cappuccino?style=flat-square" alt="GitHub"></a>
<a href="https://requires.io/github/FoxDev/cappuccino/requirements"><img src="https://img.shields.io/requires/github/FoxDev/cappuccino?style=flat-square" alt="Requires.io"></a>
</p>

<p align="center">
Nothing fancy, just an experimental Discord port of <a href="https://github.com/FoxDev/cappuccino">cappuccino</a> for fun.
</p>

A set of <a href="https://github.com/gawel/irc3">irc3</a> plugins providing various utilities primarily for <a href="https://qchat.rizon.net/?channels=rice">#rice@irc.rizon.net</a>. 

Requires Python 3.6 or above.


# Installation

First, install [Poetry](https://poetry.eustace.io/)

```sh
poetry install # Optionally install plugin dependencies with: --extras 'sentry ai lastfm web'
cp config.ini.dist config.ini
$EDITOR config.ini
poetry run irc3 config.ini
```
