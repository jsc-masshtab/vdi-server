from enum import Enum

from gino.ext.tornado import Gino
from graphene import Enum as GrapheneEnum
from sqlalchemy.sql import desc
from sqlalchemy.sql.schema import Column

from common.veil_errors import SimpleError

db = Gino()


async def get_list_of_values_from_db(db_model, column):
    """
    Return list of column values from table
    """
    db_data = await db.select([column]).select_from(db_model).gino.all()
    values = [value for (value,) in db_data]
    return values


class Status(Enum):

    CREATING = 'CREATING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'
    DELETING = 'DELETING'
    SERVICE = 'SERVICE'
    PARTIAL = 'PARTIAL'
    BAD_AUTH = 'BAD_AUTH'


class AbstractSortableStatusModel:
    """Методы для сортировки таблицы и построения расширенных запросов в стиле Django."""

    @property
    def has_status_field(self):
        model_field = self._get_table_field('is_active')
        return isinstance(model_field, Column)

    @classmethod
    def _get_table_field(cls, field_name):
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order"""
        if hasattr(cls, field_name):
            field_instance = getattr(cls, field_name)
            return field_instance
        return None

    @classmethod
    def get_order_field(cls, field_name):
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order"""
        field = cls._get_table_field(field_name)
        if field is None:
            # TODO: switch SimpleError to FieldError
            raise SimpleError('Неверный параметр сортировки {}'.format(field_name))
        return field

    @classmethod
    def get_query_field(cls, field_name):
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в where"""
        field = cls._get_table_field(field_name)
        if field is None:
            # TODO: switch SimpleError to FieldError
            raise SimpleError('Неверный параметр запроса {}'.format(field_name))
        return field

    @classmethod
    def build_ordering(cls, query, ordering=None):
        """
        ordering - название поля таблицы или доп. сортировки.
        Если ordering не указан, значит сортировка не нужна.
        Порядок сортировки (ASC|DESC) определяется наличием "-" в начале строки с названием поля.
        Допускаем, что размер названия поля таблицы не может быть меньше 2.
        """
        if not ordering or not isinstance(ordering, str) or len(ordering) < 2:
            return query

        reversed_order = False
        if ordering.find('-', 0, 1) == 0:
            reversed_order = True
            ordering = ordering[1:]

        if reversed_order:
            query = query.order_by(desc(cls.get_order_field(ordering)))
        else:
            query = query.order_by(cls.get_order_field(ordering))
        return query

    @classmethod
    def get_query(cls, ordering=None, include_inactive=False):
        """Содержит только логику запроса без фетча.
           Расширяет стандартный запрос сортировкой и статусами.
           Подразумевается, что у модели есть либо поле Status, либо is_active"""
        query = cls.query

        if not include_inactive:
            if cls().has_status_field:
                query = query.where(cls.is_active == True)
            else:
                query = query.where(cls.status != Status.DELETING)

        if ordering:
            query = cls.build_ordering(query, ordering)
        return query

    @classmethod
    async def get_object(cls, id=None, extra_field_name=None, extra_field_value=None, include_inactive=False):
        query = cls.get_query(include_inactive=include_inactive)
        if id:
            query = query.where(cls.id == id)
        elif extra_field_name and extra_field_value:
            field = cls.get_query_field(extra_field_name)
            query = query.where(field == extra_field_value)
        return await query.gino.first()

    @classmethod
    async def get_objects(cls, ordering=None, first=False):
        query = cls.get_query(ordering=ordering)
        if first:
            return await query.gino.first()
        return await query.gino.all()


StatusGraphene = GrapheneEnum.from_enum(Status)


class AbstractEntity:
    @property
    def uuid(self):
        return str(self.id) if self.id else None

    @property
    def entity_type(self):
        return self.__class__.__name__.lower()

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.uuid}
