# -*- coding: utf-8 -*-
from functools import wraps

from graphql.execution.base import ResolveInfo

from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import User
from common.settings import AUTH_ENABLED
from common.veil.auth.veil_jwt import extract_user_object
from common.veil.veil_errors import Unauthorized
from common.veil.veil_gino import EntityType, Role


def context(f):
    def decorator(func):
        def wrapper(*args, **kwargs):
            info = next(arg for arg in args if isinstance(arg, ResolveInfo))
            return func(info.context, *args, **kwargs)

        return wrapper

    return decorator


def user_passes_test(test_func, exc=Unauthorized):  # noqa
    """Exc в GraphQl вернется с 200тым кодом.

    https://github.com/graphql-python/graphene/issues/946
    """

    def decorator(f):
        @wraps(f)
        @context(f)
        async def wrapper(cntxt, *args, **kwargs):  # noqa
            if AUTH_ENABLED:
                user = await extract_user_object(cntxt.headers)
                kwargs["creator"] = user.username
                if user and isinstance(user, User):
                    if test_func(await user.roles):
                        return f(*args, **kwargs)
                await system_logger.warning(
                    message=_local_("Invalid permissions."),
                    description=_local_("IP: {}. username: {}.").format(
                        cntxt.remote_ip, user.username
                    ),
                    entity={"entity_type": EntityType.SECURITY, "entity_uuid": None},
                )
                raise exc(_local_("Invalid permissions."))
            else:
                kwargs["creator"] = "system"
                return f(*args, **kwargs)

        return wrapper

    return decorator


def is_operator(roles) -> bool:
    # админам доступны права операторов
    return Role.OPERATOR in roles or Role.SECURITY_ADMINISTRATOR in roles or Role.ADMINISTRATOR in roles


def is_administrator(roles) -> bool:
    # админам безопасности доступны права обычных админов
    return Role.ADMINISTRATOR in roles or Role.SECURITY_ADMINISTRATOR in roles


def is_security_administrator(roles) -> bool:
    return Role.SECURITY_ADMINISTRATOR in roles


administrator_required = user_passes_test(lambda roles: is_administrator(roles))
security_administrator_required = user_passes_test(
    lambda roles: is_security_administrator(roles)
)
operator_required = user_passes_test(lambda roles: is_operator(roles))
