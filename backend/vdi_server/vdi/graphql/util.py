
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