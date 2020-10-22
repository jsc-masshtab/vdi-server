# -*- coding: utf-8 -*-
from enum import Enum
from graphene import Enum as GrapheneEnum
from sqlalchemy.sql import desc, and_
from sqlalchemy.sql.schema import Column
from asyncpg import DataError

from common.database import db
from common.languages import lang_init

_ = lang_init()


async def get_list_of_values_from_db(db_model, column):
    """
    Return list of column values from table
    """
    db_data = await db.select([column]).select_from(db_model).gino.all()
    values = [value for (value,) in db_data]
    return values


class EntityType(Enum):
    """Базовые виды сущностей"""

    CONTROLLER = 'CONTROLLER'
    SECURITY = 'SECURITY'
    POOL = 'POOL'
    SYSTEM = 'SYSTEM'
    VM = 'VM'
    USER = 'USER'
    GROUP = 'GROUP'
    AUTH = 'AUTH'


class Status(Enum):

    CREATING = 'CREATING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'
    DELETING = 'DELETING'
    SERVICE = 'SERVICE'
    PARTIAL = 'PARTIAL'
    BAD_AUTH = 'BAD_AUTH'


class Role(Enum):
    """Перечисление системных и не редактируемых ролей."""

    SECURITY_ADMINISTRATOR = 'SECURITY_ADMINISTRATOR'
    OPERATOR = 'OPERATOR'
    ADMINISTRATOR = 'ADMINISTRATOR'


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
        from common.veil.veil_errors import SimpleError
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order"""
        field = cls._get_table_field(field_name)
        if field is None:
            # TODO: switch SimpleError to FieldError
            raise SimpleError(_('Incorrect sort parameter {}.').format(field_name))
        return field

    @classmethod
    def get_query_field(cls, field_name):
        from common.veil.veil_errors import SimpleError
        """Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в where"""
        field = cls._get_table_field(field_name)
        if field is None:
            # TODO: switch SimpleError to FieldError
            raise SimpleError(_('Incorrect request parameter {}.').format(field_name))
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
    async def get_object(cls, id_=None, extra_field_name=None, extra_field_value=None, include_inactive=False):
        query = cls.get_query(include_inactive=include_inactive)
        if id_:
            query = query.where(cls.id == id_)
        elif extra_field_name and extra_field_value:
            field = cls.get_query_field(extra_field_name)
            query = query.where(field == extra_field_value)
        obj = await query.gino.first()
        return obj

    @classmethod
    async def get_objects(cls, limit=100, offset=0, name=None, filters=None, ordering=None, first=False,
                          include_inactive=False):
        query = cls.get_query(ordering=ordering, include_inactive=include_inactive)
        if name:
            if cls.__name__ == 'User':
                query = query.where(cls.username.ilike('%{}%'.format(name)))
            else:
                query = query.where(cls.verbose_name.ilike('%{}%'.format(name)))
        if filters:
            query = query.where(and_(*filters))
        if first:
            return await query.gino.first()
        return await query.limit(limit).offset(offset).gino.all()


class VeilModel(db.Model):

    @property
    def entity_type(self):
        return EntityType.SECURITY

    @property
    def entity_name(self):
        return self.__class__.__name__

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

    @property
    async def entity_obj(self):
        from common.models.auth import Entity
        return await Entity.query.where(
            (Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id)).gino.first()

    @property
    def active(self):
        return self.status == Status.ACTIVE

    @property
    def failed(self):
        return self.status == Status.FAILED

    async def make_failed(self):
        """Переключает в статус FAILED."""
        from common.log.journal import system_logger
        await self.update(status=Status.FAILED).apply()
        msg = _('{} {} has been disabled.').format(self.entity_name, self.verbose_name)
        description = _('{} {} has`t been found in VeiL. Switched to FAILED.').format(self.entity_name,
                                                                                      self.verbose_name)
        await system_logger.info(message=msg, description=description, entity=self.entity, user='system')

    async def soft_delete(self, creator):
        from common.log.journal import system_logger
        try:
            await self.delete()
        except DataError as db_error:
            await system_logger.debug(_('Soft_delete exception: {}.').format(db_error))
            return False
        else:
            if self.entity:
                msg = _('{} {} has been removed.').format(self.entity_name, self.verbose_name)
                await system_logger.debug(msg, entity=self.entity, user=creator)
            else:
                msg = _('{} has been removed.').format(self.verbose_name)
                await system_logger.debug(msg, user=creator)
        return True

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


StatusGraphene = GrapheneEnum.from_enum(Status)
RoleTypeGraphene = GrapheneEnum.from_enum(Role)
