# -*- coding: utf-8 -*-

# import aioredis   # TODO: переехать на aioredis
import redis
import settings


REDIS_POOL = redis.ConnectionPool.from_url(
    getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    socket_connect_timeout=getattr(settings, 'REDIS_TIMEOUT', 5))

REDIS_CLIENT = redis.Redis(connection_pool=REDIS_POOL)

# провряем доступность Redis
REDIS_CLIENT.info()
# except ConnectionError:
#     raise


def get_thin_clients_count():
    numsub = REDIS_CLIENT.pubsub_numsub(settings.REDIS_THIN_CLIENT_CHANNEL)

    if isinstance(numsub, list):
        channel_count = numsub[0]
        if isinstance(channel_count, tuple):
            channel_count = channel_count[1]
        else:
            channel_count = 0
    else:
        channel_count = 0

    return channel_count
