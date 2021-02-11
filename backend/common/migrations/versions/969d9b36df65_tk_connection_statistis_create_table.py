"""tk_connection_statistis_create_table

Revision ID: 969d9b36df65
Revises: 3087e24383ee
Create Date: 2020-12-11 11:27:59.055809

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '969d9b36df65'
down_revision = '3087e24383ee'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tk_connection_statistis',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('conn_id', postgresql.UUID(), nullable=False),
                    sa.Column('message', sa.Unicode(length=128), nullable=True),
                    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
                    sa.ForeignKeyConstraint(['conn_id'], ['active_tk_connection.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_tk_connection_statistis_conn_id'), 'tk_connection_statistis', ['conn_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tk_connection_statistis_conn_id'), table_name='tk_connection_statistis')
    op.drop_table('tk_connection_statistis')
    # ### end Alembic commands ###