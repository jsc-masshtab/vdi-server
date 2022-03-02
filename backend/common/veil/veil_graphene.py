# -*- coding: utf-8 -*-
from enum import Enum

import graphene

from common.graphene_utils import ShortString
from common.veil.veil_gino import StatusGraphene


class VeilResourceType(graphene.ObjectType):
    """Фильтрует переданные аргументы отсутствующие у типа."""

    def __init__(self, **kwargs):
        filtered = {
            attr: attr_value
            for attr, attr_value in kwargs.items()
            if attr in self.__class__.__dict__
        }
        super().__init__(**filtered)


class VmState(graphene.Enum):
    """Перечисление статусов ВМ на ECP VeiL."""

    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class VeilEventTypeEnum(int, Enum):
    """Типы сообщений на ECP VeiL."""

    info = 0
    warning = 1
    error = 2


class VeilShortEntityType(VeilResourceType):
    """Сокращенное описание структуры вложенной сущности на ECP Veil."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()


# Tags
class VeilTagsType(VeilResourceType):
    verbose_name = graphene.Field(ShortString)
    colour = graphene.Field(ShortString)
