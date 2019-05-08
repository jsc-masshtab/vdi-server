
import asyncio
from functools import wraps


def callback(async_fun):
    '''
    callbacks for futures are synchronous.
    This makes async function usable as a callback too.
    '''
    @wraps(async_fun)
    def wrapper(*args):
        asyncio.create_task(async_fun(*args))

    return wrapper


def import_path(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod