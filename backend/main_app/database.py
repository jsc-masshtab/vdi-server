# -*- coding: utf-8 -*-
from enum import Enum

from gino.ext.tornado import Gino
from graphene import Enum as GrapheneEnum
from sqlalchemy.sql import desc, and_
from sqlalchemy.sql.schema import Column

from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST

from languages import lang_init


_ = lang_init()

db = Gino()


async def start_gino():
    await db.set_bind(
        'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'.format(DB_USER=DB_USER, DB_PASS=DB_PASS,
                                                                                DB_HOST=DB_HOST, DB_PORT=DB_PORT,
                                                                                DB_NAME=DB_NAME))


async def stop_gino():
    await db.pop_bind().close()


async def get_list_of_values_from_db(db_model, column):
    """
    Return list of column values from table
    """
    db_data = await db.select([column]).select_from(db_model).gino.all()
    values = [value for (value,) in db_data]
    return values


class EntityType(Enum):
    """Базовые виды сущностей"""
    # TODO: расширить виды сущностей при рефакторинге
    ANGLUAR = 'ANGULAR'  # TODO: есть ощущение, что это не взлетело
    THIN_CLIENT = 'THIN_CLIENT'  # TODO: есть ощущение, что это не взлетело
    CONTROLLER = 'CONTROLLER'
    SECURITY = 'SECURITY'
    POOL = 'POOL'
    SYSTEM = 'SYSTEM'
    VM = 'VM'


class Status(Enum):

    CREATING = 'CREATING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'
    DELETING = 'DELETING'
    SERVICE = 'SERVICE'
    PARTIAL = 'PARTIAL'
    BAD_AUTH = 'BAD_AUTH'


class Role(Enum):

    READ_ONLY = 'READ_ONLY'
    ADMINISTRATOR = 'ADMINISTRATOR'
    SECURITY_ADMINISTRATOR = 'SECURITY_ADMINISTRATOR'
    VM_ADMINISTRATOR = 'VM_ADMINISTRATOR'
    NETWORK_ADMINISTRATOR = 'NETWORK_ADMINISTRATOR'  # использование маловероятно
    STORAGE_ADMINISTRATOR = 'STORAGE_ADMINISTRATOR'  # использование маловероятно
    VM_OPERATOR = 'VM_OPERATOR'


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
        from common.veil_errors import SimpleError
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order"""
        field = cls._get_table_field(field_name)
        if field is None:
            # TODO: switch SimpleError to FieldError
            raise SimpleError(_('Incorrect sort parameter {}').format(field_name))
        return field

    @classmethod
    def get_query_field(cls, field_name):
        from common.veil_errors import SimpleError
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в where"""
        field = cls._get_table_field(field_name)
        if field is None:
            # TODO: switch SimpleError to FieldError
            raise SimpleError(_('Incorrect request parameter {}').format(field_name))
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
                query = query.where(cls.is_active == True)  # noqa
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
    async def get_objects(cls, filters=None, ordering=None, first=False, include_inactive=False):
        query = cls.get_query(ordering=ordering, include_inactive=include_inactive)
        if filters:
            query = query.where(and_(*filters))

        if first:
            return await query.gino.first()
        return await query.gino.all()


StatusGraphene = GrapheneEnum.from_enum(Status)
RoleTypeGraphene = GrapheneEnum.from_enum(Role)


class AbstractClass(db.Model):

    @property
    def entity_type(self):
        return EntityType.SECURITY

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

    @property
    async def entity_obj(self):
        from auth.models import Entity
        return await Entity.query.where(
            (Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id)).gino.first()

    async def soft_delete(self, dest, creator):
        from journal.journal import Log
        try:
            await self.delete()
            msg = _('{} {} had remove.').format(dest, self.verbose_name)
            if self.entity:
                await Log.info(msg, entity_dict=self.entity, user=creator)
            else:
                await Log.info(msg, user=creator)
            return True
        except Exception as ex:
            Log.debug(_('Soft_delete exception: {}').format(ex))
            return False

    @classmethod
    async def soft_update(cls, id=None, **kwargs):
        creator = kwargs.pop('creator')
        dict_kwargs = kwargs
        update_dict = dict()
        for key, value in dict_kwargs.items():
            if value is not None:
                update_dict[key] = value
        if update_dict:
            await cls.update.values(**update_dict).where(cls.id == id).gino.status()
            update_type = await cls.get(id)
            update_dict['creator'] = creator

        return update_type, update_dict

    async def add_users(self, users_list: list, creator):
        async with db.transaction():
            for user_id in users_list:
                await self.add_user(user_id, creator)
            return True

    async def add_roles(self, roles_list, creator):
        async with db.transaction():
            for role in roles_list:
                await self.add_role(role, creator)
