# -*- coding: utf-8 -*-
import graphene

from common.veil_errors import SimpleError

from settings import MIX_POOL_SIZE, MAX_POOL_SIZE, MAX_VM_AMOUNT_IN_POOL, DEFAULT_NAME


# todo: remove raw sql
async def check_and_return_pool_data(pool_id, pool_type=None):
    # check if pool exists
    async with db.connect() as conn:
        qu = 'SELECT * FROM pool WHERE id = $1', pool_id
        pool_data = await conn.fetch(*qu)
        if not pool_data:
            raise SimpleError('Не найден пул с указанным id')
        [pool_data] = pool_data
        pool_data_dict = dict(pool_data.items())

    # if pool_type provided then check if pool has required type
    if pool_type and pool_data_dict['desktop_pool_type'] != pool_type:
        raise SimpleError('Не найден пул с указанным id и типом {}'.format(pool_type))

    return pool_data_dict


def check_pool_initial_size(initial_size):
    if initial_size < MIX_POOL_SIZE or initial_size > MAX_POOL_SIZE:
        raise SimpleError('Начальное количество ВМ должно быть в интервале [{} {}]'.
                          format(MIX_POOL_SIZE, MAX_POOL_SIZE))


def check_reserve_size(reserve_size):
    if reserve_size < MIX_POOL_SIZE or reserve_size > MAX_POOL_SIZE:
        raise SimpleError('Количество создаваемых ВМ должно быть в интервале [{} {}]'.
                          format(MIX_POOL_SIZE, MAX_POOL_SIZE))


def check_total_size(total_size, initial_size):
    if total_size < initial_size:
        raise SimpleError('Максимальное количество создаваемых ВМ не может быть меньше '
                          'начального количества ВМ')
    if total_size < MIX_POOL_SIZE or total_size > MAX_VM_AMOUNT_IN_POOL:
        raise SimpleError('Максимальное количество создаваемых ВМ должно быть в интервале [{} {}]'.
                          format(MIX_POOL_SIZE, MAX_VM_AMOUNT_IN_POOL))


class DesktopPoolType(graphene.Enum):
    AUTOMATED = 0
    MANUAL = 1
