from gino.ext.tornado import Gino
from enum import Enum

db = Gino()


async def get_list_of_values_from_db(db_model, column):
    """
    Return list of column values from table
    """
    db_data = await db.select([column]).select_from(db_model).gino.all()
    values = [value for (value,) in db_data]
    return values


class Status(Enum):
    """
    При создании миграции Alembic не может корректно отработать создание типа в Pg.
    Чтобы решить проблему:
    op.execute("CREATE TYPE status AS ENUM ('CREATING', 'ACTIVE', 'FAILED', 'DELETING', 'SERVICE', 'PARTIAL');")
    """

    CREATING = 'CREATING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'
    DELETING = 'DELETING'
    SERVICE = 'SERVICE'
    PARTIAL = 'PARTIAL'
