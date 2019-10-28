# -*- coding: utf-8 -*-
from tornado.escape import json_encode


def prepare_body(func):
    """Convert dict to HTTPClient request.body"""
    def wrapper(*args, **kwargs):
        if len(args) >= 3 and kwargs.get('body'):
            raise AssertionError(
                'Expect that \'body\' is the 4 parameter in args. But in the same time \'body\' in kwargs. Check it.')
        if len(args) >= 3:
            input_body = args[3]
        else:
            input_body = kwargs.get('body')

        if not input_body:
            body = input_body
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
        if len(args) >= 3:
            args_list = list(args)
            args_list[3] = body
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
                raise NotImplementedError('Can check only kwargs or args. Not both at the same time.')

            if len(a_params) > 0:
                if len(kwargs) > 0:
                    raise AssertionError(
                        'The parameters to be checked are in an dict. Can\'t explicitly match values with tuple.')
                if not isinstance(args[0], str) or not isinstance(args[0], int):
                    # First element in args can be self of a method.
                    local_args = args[1:]
                else:
                    local_args = args.copy()
                for idx, parameter_value in enumerate(local_args):
                    valid_values = a_params[idx]
                    if parameter_value not in valid_values:
                        raise AssertionError(
                            'Value {} is invalid. Valid values are: {}'.format(parameter_value, valid_values))
            elif len(k_params) > 0:
                if len(args) > 0:
                    raise AssertionError(
                        'The parameters to be checked are in an dict. Can\'t explicitly match values with tuple.')
                for parameter in k_params:
                    if not kwargs.get(parameter):
                        raise AssertionError('Parameter {} is necessary.'.format(parameter))
                    parameter_value = kwargs.get(parameter)
                    valid_values = k_params.get(parameter)
                    if parameter_value not in valid_values:
                        raise AssertionError(
                            'Parameter {} value {} is invalid. Valid values are: {}'.format(parameter, parameter_value,
                                                                                            valid_values))
            return func(*args, **kwargs)
        return wrapper
    return decorator
