
def get_selections(info, path=''):
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
