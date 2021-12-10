import asyncio
import functools

import yaaredis

from common import settings


def cached(cache):
    def decorator(func):
        @functools.wraps(func)
        async def _inner(*args, **kwargs):
            key = func.__name__
            response = await cache.get(key, (args, kwargs))
            if response:
                print("using cache: {}".format(response))
            else:
                print("cache miss")
                response = func(*args, **kwargs)
                await cache.set(key, response, (args, kwargs))
            return response
        return _inner
    return decorator


CACHE = yaaredis.StrictRedis(password=settings.REDIS_PASSWORD).cache("example_cache")


@cached(cache=CACHE)
def job(*args, **kwargs):
    return "example_results for job({}, {})".format(args, kwargs)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(job(111))
