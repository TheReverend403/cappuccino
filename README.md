<p align="center">
  <img align="center" src="logo.png" alt="logo">
</p>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/github/license/TheReverend403/cappuccino?style=flat-square" alt="GitHub"></a>
<a href="https://github.com/TheReverend403/cappuccino/actions"><img src="https://img.shields.io/github/actions/workflow/status/TheReverend403/cappuccino/build-docker-image.yml?branch=main&style=flat-square" alt="GitHub Workflow Status"></a>
<a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat-square" alt="Code style: ruff"></a>
</p>

<p align="center">
A set of <a href="https://github.com/gawel/irc3">irc3</a> plugins providing various utilities primarily for <a href="https://qchat.rizon.net/?channels=rice">#rice@irc.rizon.net</a>.
</p>

# Installation

Requirements:

- PostgreSQL

## Setting up the dev environment

First, install [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
git clone https://github.com/TheReverend403/cappuccino
cd cappuccino

uv sync --group dev
uv run pre-commit install
```

## Running in dev mode

```sh
cp docker/.env.example docker/.env # Open and set any empty variables
docker compose -f docker/docker-compose.dev.yml up --build --pull always
```
