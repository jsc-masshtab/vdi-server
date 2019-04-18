

# The actual resolvers

async def resolve_root(root, _info, id, info):
    return {}

the_rest = {}
for w in 'the rest of it'.split():
    the_rest[w] = ';'

async def resolve_sub1(root, info, **kw):
    return the_rest


sub2 = {}
for l in 'abc':
    sub2[l] = l


async def resolve_sub2(root, info, **kw):
    return sub2


