"""
python -m examples.service.scripts.demo
"""
from asyncio import gather, run, sleep

from fastapi_esql import timing

from .. import app


async def work(sec):
    print(f"starting sleep {sec}")
    await sleep(sec)
    print(f"slept {sec}")


@timing
async def main():
    for func in app.router.on_startup:
        await func()

    await gather(work(1), work(2), work(3))


if __name__ == "__main__":
    run(main())
