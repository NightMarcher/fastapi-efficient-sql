from logging import Logger
from typing import Any, Dict, List, Optional, Callable

from tortoise import BaseDBAsyncClient

from .converter import convert_dicts


class CursorHandler:

    @classmethod
    async def fetch_dicts(
        cls,
        sql: str,
        conn: BaseDBAsyncClient,
        logger: Logger,
        converters: Dict[str, Callable] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            dicts = await conn.execute_query_dict(sql)
            convert_dicts(dicts, converters)
            return dicts
        except Exception as e:
            logger.exception(f"{e} SQL=>{sql}")
            return None

    @classmethod
    async def fetch_one(
        cls,
        sql: str,
        conn: BaseDBAsyncClient,
        logger: Logger,
        converters: Dict[str, Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            dicts = await conn.execute_query_dict(sql)
            convert_dicts(dicts, converters)
            if dicts:
                return dicts[0]
            return {}
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
