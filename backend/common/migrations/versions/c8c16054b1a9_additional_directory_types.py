"""additional directory types

Revision ID: c8c16054b1a9
Revises: cff542bb5131
Create Date: 2021-05-27 18:54:35.573049

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c8c16054b1a9'
down_revision = 'cff542bb5131'
branch_labels = None
depends_on = None


def upgrade():
    # drop old column
    op.drop_column('authentication_directory', 'directory_type')
    op.execute("DROP TYPE IF EXISTS directorytypes;")
    # create new type
    directory_type = postgresql.ENUM("ActiveDirectory",
                                     "FreeIPA",
                                     "OpenLDAP",
                                     "ALD",
                                     name="directorytypes",
                                     )
    directory_type.create(op.get_bind())
    # add column to table
    op.add_column('authentication_directory',
                  sa.Column(
                      "directory_type",
                      sa.Enum(
                          "ActiveDirectory",
                          "FreeIPA",
                          "OpenLDAP",
                          "ALD",
                          name="directorytypes",
                      ),
                      server_default="ActiveDirectory",
                  ))
    # set ActiveDirectory to existing records
    op.execute("UPDATE authentication_directory SET directory_type = 'ActiveDirectory'")
    # remove nullable for new column
    op.alter_column(table_name='authentication_directory',
                    column_name='directory_type',
                    nullable=False)


def downgrade():
    # drop old column
    op.execute(
        "DELETE FROM authentication_directory WHERE directory_type  != 'ActiveDirectory';")
    op.drop_column('authentication_directory', 'directory_type')
    op.execute("DROP TYPE IF EXISTS directorytypes;")
    # create new type
    directory_type = postgresql.ENUM("ActiveDirectory",
                                     name="directorytypes")
    directory_type.create(op.get_bind())
    # add column to table
    op.add_column('authentication_directory',
                  sa.Column(
                      "directory_type",
                      sa.Enum(
                          "ActiveDirectory",
                          name="directorytypes",
                      ),
                      server_default="ActiveDirectory",
                  ))
    # set ActiveDirectory to existing records
    op.execute("UPDATE authentication_directory SET directory_type = 'ActiveDirectory'")
    # remove nullable for new column
    op.alter_column(table_name='authentication_directory',
                    column_name='directory_type',
                    nullable=False)
