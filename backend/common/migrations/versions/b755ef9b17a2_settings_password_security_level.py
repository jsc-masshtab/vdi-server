"""Settings password security level

Revision ID: b755ef9b17a2
Revises: a73bdb4c3e7a
Create Date: 2022-08-08 15:16:43.311546

"""
import json

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b755ef9b17a2'
down_revision = 'a73bdb4c3e7a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    res = conn.execute("SELECT settings FROM public.settings")
    results = res.fetchall()
    result = results[0]
    (settings_dict,) = result
    settings_dict["PASSWORD_SECURITY_LEVEL"] = "LOW"

    settings_json = json.dumps(settings_dict)
    op.execute("""UPDATE public.settings SET settings = '{}'""".format(settings_json))


def downgrade():
    conn = op.get_bind()
    res = conn.execute("SELECT settings FROM public.settings")
    results = res.fetchall()
    result = results[0]
    (settings_dict,) = result
    del settings_dict["PASSWORD_SECURITY_LEVEL"]

    settings_json = json.dumps(settings_dict)
    op.execute("""UPDATE public.settings SET settings = '{}'""".format(settings_json))
