<p align="center">
  <img align="center" src="logo.png">
</p>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/github/license/TheReverend403/cappuccino?style=flat-square" alt="GitHub"></a>
<a href="https://github.com/TheReverend403/cappuccino-discord/actions"><img src="https://img.shields.io/github/workflow/status/TheReverend403/cappuccino/ci?style=flat-square" alt="GitHub Workflow Status"></a>
<a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="Code style: black"></a>
</p>

<p align="center">
A set of <a href="https://github.com/gawel/irc3">irc3</a> plugins providing various utilities primarily for <a href="https://qchat.rizon.net/?channels=rice">#rice@irc.rizon.net</a>.
</p>

## Installation

Requirements:
* PostgreSQL
* Python 3.9+
* [Poetry](https://python-poetry.org)

```sh
poetry install
cp config.ini.dist config.ini
$EDITOR config.ini
poetry run alembic upgrade head
poetry run irc3 config.ini
```

## Developers
[pre-commit](https://pre-commit.com/) is used for formatting and PEP 8 compliance checks.

These checks must pass in order to make a commit to `main`. To install and use the hooks, run the following commands:

```shell script
poetry shell # If you're not already in the poetry env.
pre-commit install
pre-commit run --all-files # or just make a commit to run checks automatically.
```
