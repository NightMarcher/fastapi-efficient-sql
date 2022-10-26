from functools import wraps
from logging import getLogger
from time import perf_counter

logger = getLogger(__name__)


def timing(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        st = perf_counter()
        result = await func(*args, **kwargs)
        et = perf_counter()
        logger.info(f"{func.__module__}/{func.__name__} Cost {1000 * (et - st):.2f} ms")
        return result
    return wrapper
