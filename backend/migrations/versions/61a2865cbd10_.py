"""empty message

Revision ID: 61a2865cbd10
Revises: 2a37a0ca8641
Create Date: 2020-02-03 19:10:40.171726

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '61a2865cbd10'
down_revision = '2a37a0ca8641'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('verbose_name', sa.Unicode(length=128), nullable=False),
                    sa.Column('description', sa.Unicode(length=255), nullable=True),
                    sa.Column('date_created', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                              nullable=True),
                    sa.Column('date_updated', sa.DateTime(timezone=True), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('verbose_name')
                    )
    op.create_table('user_groups',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('group_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index('user_in_group', 'user_groups', ['user_id', 'group_id'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('user_in_group', table_name='user_groups')
    op.drop_table('user_groups')
    op.drop_table('group')
    # ### end Alembic commands ###