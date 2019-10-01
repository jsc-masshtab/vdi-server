from db.db import db
from vdi.errors import FieldError
from vdi import constants

# determine what fields are requested in graphql request
def get_selections(info, path=''):
    if isinstance(info, Selections):
        return info.get_path(path)

    path = [i for i in path.split('/') if i]

    selections = info.field_asts[0].selection_set.selections

    for item in path:
        for field in selections:
            if field.name.value == item:
                break
        else:
            return
        selections = field.selection_set.selections

    return [
        field.name.value for field in selections
    ]


class Selections(list):

    def _get_item(self, items, key):
        for item in items:
            if isinstance(item, dict) and tuple(item.keys()) == (key,):
                return item[key]
        return ()

    def _is_compound(self, item):
        return isinstance(item, dict) and len(item) == 1

    def get_path(self, path):
        selections = self
        if path:
            path = path.split('/')
            for path_key in path:
                selections = self._get_item(selections, path_key)
        return [
            list(e.keys())[0] if self._is_compound(e) else e
            for e in selections
        ]


def as_list(gen):
    return list(gen())


async def check_and_return_pool_data(pool_id, pool_type=None):
    # check if pool exists
    async with db.connect() as conn:
        qu = 'SELECT * FROM pool WHERE id = $1', pool_id
        pool_data = await conn.fetch(*qu)
        if not pool_data:
            raise FieldError(pool_id=['Не найден пул с указанным id'])
        [pool_data] = pool_data
        pool_data_dict = dict(pool_data.items())

    # if pool_type provided then check if pool has required type
    if pool_type and pool_data_dict['desktop_pool_type'] != pool_type:
        raise FieldError(pool_id=['Не найден пул с указанным id и типом {}'.format(pool_type)])

    return pool_data_dict


def check_pool_initial_size(initial_size):
    if initial_size < constants.MIX_SIZE or initial_size > constants.MAX_SIZE:
        raise FieldError(initial_size=['Начальное количество ВМ должно быть в интервале [{} {}]'.
                         format(constants.MIX_SIZE, constants.MAX_SIZE)])


def check_reserve_size(reserve_size):
    if reserve_size < constants.MIX_SIZE or reserve_size > constants.MAX_SIZE:
        raise FieldError(reserve_size=['Количество создаваемых ВМ должно быть в интервале [{} {}]'.
                         format(constants.MIX_SIZE, constants.MAX_SIZE)])


def check_total_size(total_size, initial_size):
    if total_size < initial_size:
        raise FieldError(total_size=['Максимальное количество создаваемых ВМ не может быть меньше '
                                     'начального количества ВМ'])
    if total_size < constants.MIX_SIZE or total_size > constants.MAX_VM_AMOUNT:
        raise FieldError(total_size=['Максимальное количество создаваемых ВМ должно быть в интервале [{} {}]'.
                         format(constants.MIX_SIZE, constants.MAX_VM_AMOUNT)])


# create resource object (NodeType, ClusterType...)
# fields_map is used to match Vitalya names with veil names
def make_resource_type(type, data, fields_map=None):
    dic = {}
    for k, v in data.items():
        if fields_map:
            k = fields_map.get(k, k)
        if k in type._meta.fields:
            dic[k] = v
    obj = type(**dic)
    obj.veil_info = data
    return obj


# remove vms from db
async def remove_vms_from_pool(vm_ids, pool_id):
    placeholders = ['${}'.format(i + 1) for i in range(0, len(vm_ids))]
    placeholders = ', '.join(placeholders)
    print('placeholders', placeholders)
    async with db.connect() as conn:
        qu = 'DELETE FROM vm WHERE id IN ({}) AND pool_id = {}'.format(placeholders, pool_id), *vm_ids
        await conn.fetch(*qu)