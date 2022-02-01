"""Change_lenght_token.

Revision ID: 6g78tf2ee56d
Revises: 17997eb1f91f
Create Date: 2022-02-01 15:49:32.314111

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6g78tf2ee56d'
down_revision = '17997eb1f91f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE controller ALTER COLUMN token TYPE varchar(2048);")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE controller ALTER COLUMN token TYPE varchar(1024);")
    # ### end Alembic commands ###
