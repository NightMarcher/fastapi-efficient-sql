from logging import Logger
from typing import Any, Dict, List, Optional

from tortoise import BaseDBAsyncClient


class CursorHandler:

    @classmethod
    async def fetch_dicts(
        cls,
        sql: str,
        conn: BaseDBAsyncClient,
        logger: Logger,
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            return await conn.execute_query_dict(sql)
        except Exception as e:
            logger.exception(f"{e} SQL=>{sql}")
            return None

    @classmethod
    async def sum_row_cnt(
        cls,
        sql: str,
        conn: BaseDBAsyncClient,
        logger: Logger,
    ) -> Optional[int]:
        try:
            row_cnt, _ = await conn.execute_query(sql)
            return row_cnt
        except Exception as e:
            logger.exception(f"{e} SQL=>{sql}")
            return None

    @classmethod
    async def exec_if_ok(
        cls,
        sql: str,
        conn: BaseDBAsyncClient,
        logger: Logger,
    ) -> bool:
        try:
            await conn.execute_script(sql)
            return True
        except Exception as e:
            logger.exception(f"{e} SQL=>{sql}")
            return False
