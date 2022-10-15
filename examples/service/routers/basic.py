from asyncio import sleep
import logging
from time import perf_counter

from fastapi import APIRouter, BackgroundTasks

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ping")
async def ping():
    return {"ping": "pong"}


@router.get("/background/sleep")
async def bg_sleep(
    bg_tasks: BackgroundTasks,
):
    t0 = perf_counter()
    # This sleep represents time-consuming procedure
    await sleep(1)

    t1 = perf_counter()
    async def my_sleep(sec):
        await sleep(sec)
        logger.debug(f"slept {sec} sec")
    bg_tasks.add_task(my_sleep, 1)
    bg_tasks.add_task(my_sleep, 1.5)
    bg_tasks.add_task(my_sleep, 2)

    t2 = perf_counter()
    logger.debug(f"{1000 * (t1 - t0):.3f} ms, {1000 * (t2 - t0):.3f} ms")
    return "done"
