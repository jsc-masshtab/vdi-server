"""automated_pool updates

Revision ID: fd0a9d655a9f
Revises: ae7bbf17ac03
Create Date: 2020-09-10 14:15:34.287706

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fd0a9d655a9f'
down_revision = 'ae7bbf17ac03'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('automated_pool', sa.Column('ad_cn_pattern', sa.Unicode(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('automated_pool', 'ad_cn_pattern')
    # ### end Alembic commands ###