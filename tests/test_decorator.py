import pytest

from fastapi_esql import timing


@timing
async def afunc():
    """async def afunc()"""
    return True


@timing
def func():
    """def func()"""
    return False


@pytest.mark.asyncio
async def test_async_timing():
    print(afunc, afunc.__doc__, afunc.__name__)
    assert await afunc() == True


def test_sync_timing():
    print(func, func.__doc__, func.__name__)
    assert func() == False
