# -*- coding: utf-8 -*-
import graphene

from common.veil.veil_gino import StatusGraphene


class VeilResourceType(graphene.ObjectType):
    """Фильтрует переданные аргументы отсутствующие у типа."""

    def __init__(self, **kwargs):
        # TODO: args?
        filtered = {attr: attr_value for attr, attr_value in kwargs.items() if attr in self.__class__.__dict__}
        super().__init__(**filtered)


class VmState(graphene.Enum):
    """Перечисление статусов ВМ на ECP VeiL."""

    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class VeilShortEntityType(VeilResourceType):
    """Сокращенное описание структуры вложенной сущности на ECP Veil."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()


# Tags
class VeilTagsType(VeilResourceType):
    verbose_name = graphene.String()
    colour = graphene.String()
    slug = graphene.String()
