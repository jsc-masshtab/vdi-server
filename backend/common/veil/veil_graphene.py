# -*- coding: utf-8 -*-
from graphene import ObjectType
from graphene import Enum as GrapheneEnum


class VeilResourceType(ObjectType):
    """Фильтрует переданные аргументы отсутствующие у типа."""

    def __init__(self, **kwargs):
        # TODO: args?
        filtered = {attr: attr_value for attr, attr_value in kwargs.items() if attr in self.__class__.__dict__}
        super().__init__(**filtered)


class VmState(GrapheneEnum):
    """Перечисление статусов ВМ на ECP VeiL."""

    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3
