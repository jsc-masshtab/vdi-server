import pytest

from common.utils import Cache

from web_app.tests.fixtures import (  # noqa: F401
    fixt_db,  # noqa: F401
    fixt_redis_client,  # noqa: F401
)  # noqa: F401


pytestmark = [pytest.mark.asyncio, pytest.mark.cache]


async def test_set_get_cache(fixt_db):  # noqa
    data_to_cache = [
        {"status": "ACTIVE",
         "datacenter": {
             "id": "90385bd8-1d4a-45c9-bffa-b100db5d6a57",
             "verbose_name": "Veil default location"
         },
         "description": None,
         "cpu_count": 32,
         "hints": 1,
         "nodes_count": 1,
         "tags": [],
         "id": "c24455f8-3b47-4ded-830c-458b4c5ddb7d",
         "verbose_name": "Veil default cluster",
         "controller": {
             "address": "192.168.11.102",
             "id": "95743e59-13d9-44a2-842f-fd72260dd923",
             "verbose_name": "102"
         },
         "memory_count": 64306,
         "built_in": True}
    ]

    cache_client = await Cache.get_client()
    cache_key = "test_cache"
    cache = cache_client.cache(cache_key)

    await cache.set(
        key=cache_key, value=data_to_cache, expire_time=60
    )
    data_from_cache = await cache.get(cache_key)

    assert data_to_cache == data_from_cache
