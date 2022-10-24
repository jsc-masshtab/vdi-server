"""Gateway settings

Revision ID: e515cfece1bf
Revises: 4877bb8b4f29
Create Date: 2022-08-24 13:37:40.814368

"""
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e515cfece1bf'
down_revision = '4877bb8b4f29'
branch_labels = None
depends_on = None


def upgrade():
    # Add column 'gateway_settings'
    op.add_column('settings', sa.Column('gateway_settings', sa.JSON, nullable=True))

    gateway_dict = {"port_range_start": 48654,
                    "port_range_stop": 48999,
                    "gateway_address": "127.0.0.1",
                    "gateway_port": 8000,
                    "broker_address": "127.0.0.1",
                    "broker_port": 4200,
                    "vc_address": "127.0.0.1",
                    "vc_port": 4210
                    }
    gateway_json = json.dumps(gateway_dict)
    op.execute("""UPDATE public.settings SET gateway_settings = '{}'""".format(gateway_json))


def downgrade():
    op.drop_column('settings', 'gateway_settings')
