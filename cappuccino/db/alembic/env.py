import configparser
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from cappuccino.db.models import BaseModel
from cappuccino.db.models.ai import AIChannel, CorpusLine  # noqa: F401
from cappuccino.db.models.triggers import Trigger  # noqa: F401
from cappuccino.db.models.userdb import RiceDB  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = BaseModel.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    bot_config = configparser.ConfigParser()
    bot_config.read(os.getenv("SETTINGS_FILE", "config.ini"))
    alembic_config = config.get_section(config.config_ini_section)
    alembic_config["sqlalchemy.url"] = bot_config["database"]["uri"]
    connectable = engine_from_config(
        alembic_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
