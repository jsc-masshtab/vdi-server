import asyncio

import yaaredis
from yaaredis.cache import IdentityGenerator, Cache

from common import settings


class CustomIdentityGenerator(IdentityGenerator):

    def generate(self, key, content):
        return key


def expensive_work(data):
    """some work that waits for io or occupy cpu"""
    return data


async def example():
    client = yaaredis.StrictRedis(password=settings.REDIS_PASSWORD)
    await client.flushall()  # думаю, можно не чиститься каждый раз
    cache = client.cache("example_cache",
                         identity_generator_class=CustomIdentityGenerator)
    data = {'1': 1}
    await cache.set("example_key", expensive_work(data), data)
    response = await cache.get("example_key", data)
    assert response == expensive_work(data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
