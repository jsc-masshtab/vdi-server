from gino.ext.tornado import Gino

db = Gino()


async def get_list_of_values_from_db(db_model, column):
    """
    Return list of column values from table
    """
    db_data = await db.select([column]).select_from(db_model).gino.all()
    values = [value for (value,) in db_data]
    return values
