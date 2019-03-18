
def get_selections(info):
    return [
        f.name.value
        for f in info.field_asts[0].selection_set.selections
    ]
