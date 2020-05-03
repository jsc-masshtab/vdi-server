# -*- coding: utf-8 -*-
from functools import wraps
from tornado.escape import json_encode
from graphql.execution.base import ResolveInfo

from settings import AUTH_ENABLED
from database import Role, EntityType

from auth.utils.veil_jwt import extraxt_user_object
from common.veil_errors import Unauthorized
from auth.models import User

from languages import lang_init
from journal.journal import Log as log


_ = lang_init()


def prepare_body(func):
    """Convert dict to HTTPClient request.body"""

    def wrapper(*args, **kwargs):

        if len(args) >= 4 and kwargs.get('body'):
            raise AssertionError(
                _('\'body\' index in args must be 4, but in the same time \'body\' in kwargs'))

        if len(args) >= 4:
            input_body = args[4]
            input_method = args[2]
        else:
            input_body = kwargs.get('body')
            input_method = kwargs.get('method')

        if not input_body:
            body = ''
        elif len(input_body) == 0:
            body = ''
        elif isinstance(input_body, str):
            body = input_body
        elif isinstance(input_body, dict):
            try:
                body = json_encode(input_body)
            except ValueError:
                body = ''
        else:
            body = ''

        if body == '' and input_method == 'GET':
            body = None

        if len(args) >= 4:
            args_list = list(args)
            args_list[4] = body
            args = tuple(args_list)
        else:
            kwargs['body'] = body
        return func(*args, **kwargs)
    return wrapper


def check_params(*a_params, **k_params):
    """Декоратор для проверки соответствия передаваемых аргументов контрольным спискам"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if len(a_params) > 0 and len(k_params) > 0:
                raise NotImplementedError(_('Can check only kwargs or args. Not both at the same time.'))

            if len(a_params) > 1:
                if len(kwargs) > 0:
                    raise AssertionError(
                        _('The parameters to be checked are in an dict. Can\'t explicitly match values with tuple.'))
                if not isinstance(args[0], str) or not isinstance(args[0], int):
                    # First element in args can be self of a method.
                    local_args = args[1:]
                else:
                    local_args = args.copy()
                for idx, parameter_value in enumerate(local_args):
                    valid_values = a_params[idx]
                    if parameter_value not in valid_values:
                        raise AssertionError(
                            _('Value {} is invalid. Valid values are: {}').format(parameter_value, valid_values))
            elif len(k_params) > 0:
                if len(args) > 1:
                    raise AssertionError(
                        _('The parameters to be checked are in an dict. Can\'t explicitly match values with tuple.'))
                for parameter in k_params:
                    if not kwargs.get(parameter):
                        raise AssertionError(_('Parameter {} is necessary.').format(parameter))
                    parameter_value = kwargs.get(parameter)
                    valid_values = k_params.get(parameter)
                    if parameter_value not in valid_values:
                        raise AssertionError(
                            _('Parameter {} value {} is invalid. Valid values are: {}').format(parameter,
                                                                                               parameter_value,
                                                                                               valid_values))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def context(f):
    def decorator(func):
        def wrapper(*args, **kwargs):
            info = next(arg for arg in args if isinstance(arg, ResolveInfo))
            return func(info.context, *args, **kwargs)
        return wrapper
    return decorator


def user_passes_test(test_func, exc=Unauthorized):  # noqa
    """exc в GraphQl вернется с 200тым кодом.
       https://github.com/graphql-python/graphene/issues/946
    """

    def decorator(f):
        @wraps(f)
        @context(f)
        async def wrapper(cntxt, *args, **kwargs):  # noqa
            if AUTH_ENABLED:
                user = await extraxt_user_object(cntxt.headers)
                if user and isinstance(user, User):
                    if test_func(await user.roles):
                        return f(*args, **kwargs)
                # log.debug(_('IP: . username: {}'))
                await log.warning(
                    _('IP: {}. username: {}').format(cntxt.remote_ip, user.username),
                    entity_dict={'entity_type': EntityType.SECURITY, 'entity_uuid': None})
                raise exc(_('Invalid permissions'))
            else:
                return f(*args, **kwargs)
        return wrapper
    return decorator


def is_read_only(roles) -> bool:
    return Role.READ_ONLY in roles


def is_administrator(roles) -> bool:
    return Role.ADMINISTRATOR in roles


def is_security_administrator(roles) -> bool:
    return Role.SECURITY_ADMINISTRATOR in roles


def is_vm_administrator(roles) -> bool:
    return Role.VM_ADMINISTRATOR in roles


def is_network_administrator(roles) -> bool:
    return Role.NETWORK_ADMINISTRATOR in roles


def is_storage_administrator(roles) -> bool:
    return Role.STORAGE_ADMINISTRATOR in roles


def is_vm_operator(roles) -> bool:
    return Role.VM_OPERATOR in roles


readonly_required = user_passes_test(lambda roles: is_read_only(roles))
administrator_required = user_passes_test(lambda roles: is_administrator(roles))
security_administrator_required = user_passes_test(lambda roles: is_security_administrator(roles))
vm_administrator_required = user_passes_test(lambda roles: is_vm_administrator(roles))
network_administrator_required = user_passes_test(lambda roles: is_network_administrator(roles))
storage_administrator_required = user_passes_test(lambda roles: is_storage_administrator(roles))
vm_operator_required = user_passes_test(lambda roles: is_vm_operator(roles))
