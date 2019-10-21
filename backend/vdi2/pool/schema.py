# -*- coding: utf-8 -*-
import graphene


class DesktopPoolType(graphene.Enum):
    AUTOMATED = 0
    STATIC = 1
