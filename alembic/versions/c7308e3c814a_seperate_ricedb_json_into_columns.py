"""Seperate ricedb json into columns

Revision ID: c7308e3c814a
Revises: ca58ba59b328
Create Date: 2020-02-02 20:34:18.585110

"""
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c7308e3c814a"
down_revision = "ca58ba59b328"
branch_labels = None
depends_on = None

table = "ricedb"


def upgrade():
    op.add_column(table, sa.Column("dtops", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("homescreens", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("stations", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("pets", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("dotfiles", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("handwritings", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("distros", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("websites", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("selfies", sa.JSON(), nullable=True))
    op.add_column(table, sa.Column("lastfm", sa.String(), nullable=True))
    op.add_column(table, sa.Column("last_seen", sa.DateTime(), nullable=True))

    copy_json_to_columns()


def copy_json_to_columns():
    ricedb_table = sa.Table(table, sa.MetaData(bind=op.get_bind()), autoload=True)
    for result in ricedb_table.select().execute():
        user = result[0]
        json_data = result[1]
        last_seen = json_data.get("last_seen")
        if last_seen:
            last_seen = datetime.fromtimestamp(last_seen, tz=UTC)

        values = dict(
            # or None because empty lists aren't considered SQL NULL
            dtops=json_data.get("dtops") or None,
            homescreens=json_data.get("homescreens") or None,
            stations=json_data.get("stations") or None,
            pets=json_data.get("pets") or None,
            dotfiles=json_data.get("dotfiles") or None,
            handwritings=json_data.get("handwritings") or None,
            distros=json_data.get("distros") or None,
            websites=json_data.get("websites") or None,
            selfies=json_data.get("selfies") or None,
            lastfm=json_data.get("lastfm") or None,
            last_seen=last_seen or None,
        )

        ricedb_table.update().values(values).where(
            ricedb_table.c.nick == user
        ).execute()


def downgrade():
    op.drop_column(table, "dtops")
    op.drop_column(table, "homescreens")
    op.drop_column(table, "stations")
    op.drop_column(table, "pets")
    op.drop_column(table, "dotfiles")
    op.drop_column(table, "handwritings")
    op.drop_column(table, "distros")
    op.drop_column(table, "websites")
    op.drop_column(table, "selfies")
    op.drop_column(table, "lastfm")
    op.drop_column(table, "last_seen")
