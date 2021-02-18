"""superuser

Revision ID: 96d866b36fa2
Revises: a81d0adece0e
Create Date: 2020-04-01 08:48:16.977289

"""
from alembic import op
import sqlalchemy as sa  # noqa


# revision identifiers, used by Alembic.
revision = '96d866b36fa2'
down_revision = 'a81d0adece0e'
branch_labels = None
depends_on = None


def upgrade():
    """Миграция нужна исключительно для заведения пользователя, пока мы не можем это сделать из скрипта установки"""
    # admin - veil
    # sql = """insert
    #          into
    #          public."user" (id, username, "password", email, is_active, is_superuser)
    #          values (
    #             'f9599771-cc95-45e4-9ae5-c8177b796aff',
    #             'admin',
    #             'pbkdf2_sha256$180000$WEBRRFY2i6fIh0IqMVFkfvDcnrEAMBJT7lSJnlBzxwo8RO5CCn$6kR5yASdhj/n6VwXKOaYLfdr2cAXoTedgqrkpngvJhw=',
    #             'admin@admin.admin',
    #             true,
    #             true);"""
    # op.execute(sql)
    pass


def downgrade():
    op.execute("delete from public.user where id = 'f9599771-cc95-45e4-9ae5-c8177b796aff';")
