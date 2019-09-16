import asyncio


from db.db import fetch
from vdi.utils import into_words, bulk_insert

async def main():
    qu = 'select * from dynamic_pool',
    data = await fetch(*qu)
    traits_keys = into_words('initial_size reserve_size total_size '
                             'datapool_id cluster_id node_id vm_name_template')
    traits = [
        {k: pool[k] for k in traits_keys}
        for pool in data
    ]
    ids = await bulk_insert('dynamic_traits', traits, returning='id')
    ids = [id for [id] in ids]
    pool_keys = into_words("id name controller_ip desktop_pool_type deleted")
    items = []
    for id, pool in zip(ids, data):
        items.append({
            'dynamic_traits': id,
            **{k: pool[k] for k in pool_keys}
        })
    await bulk_insert('pool', items)

#asyncio.run(main())
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()