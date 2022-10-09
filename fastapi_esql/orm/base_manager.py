import logging
from typing import List, Optional

from tortoise.backends.base.client import BaseDBAsyncClient

from .base_app import AppMetaclass
from .base_model import BaseModel
from ..utils.sqlizer import SQLizer

logger = logging.getLogger(__name__)


class BaseManager(metaclass=AppMetaclass):

    model = BaseModel

    @classmethod
    async def create_from_dict(cls, params):
        params["using_db"] = cls.rw_conn
        try:
            return await cls.model.create(**params)
        except Exception as e:
            logger.exception(e)
            return None

    @classmethod
    async def bulk_create_from_dicts(cls, dicts: List[dict]) -> bool:
        try:
            await cls.model.bulk_create(
                objects=[cls.model(**d) for d in dicts],
                using_db=cls.rw_conn,
            )
            return True
        except Exception as e:
            logger.exception(e)
            return False

    @classmethod
    async def select_custom_fields(
        cls,
        fields: List[str],
        wheres: List[str],
        conn: Optional[BaseDBAsyncClient] = None,
    ) -> Optional[List[dict]]:
        sql = SQLizer.select_custom_fields(
            cls.model._meta.db_table,
            fields,
            wheres,
        )
        conn = conn or cls.ro_conn
        try:
            return await conn.execute_query_dict(sql)
        except Exception as e:
            logger.exception(e)
            return None

    @classmethod
    async def upsert_json(
        cls,
        json_field: str,
        path_value_dict: dict,
        wheres: List[str],
        conn: Optional[BaseDBAsyncClient] = None,
    ) -> Optional[int]:
        sql = SQLizer.upsert_json(
            cls.model._meta.db_table,
            json_field,
            path_value_dict,
            wheres,
        )
        conn = conn or cls.rw_conn
        try:
            row_cnt, _ = await conn.execute_query(sql)
            return row_cnt
        except Exception as e:
            logger.exception(e)
            return None

    @classmethod
    async def upsert_on_duplicate_key(
        cls,
        dicts: List[dict],
        insert_fields: List[str],
        upsert_fields: List[str],
        conn: Optional[BaseDBAsyncClient] = None,
    ) -> Optional[int]:
        sql = SQLizer.upsert_on_duplicate_key(
            cls.model._meta.db_table,
            dicts,
            insert_fields,
            upsert_fields,
        )
        conn = conn or cls.rw_conn
        try:
            row_cnt, _ = await conn.execute_query(sql)
            return row_cnt
        except Exception as e:
            logger.exception(e)
            return None

    @classmethod
    async def insert_into_select(
        cls,
        wheres: List[str],
        remain_fields: List[str],
        assign_field_dict: dict,
        conn: Optional[BaseDBAsyncClient] = None,
    ) -> bool:
        sql = SQLizer.insert_into_select(
            cls.model._meta.db_table,
            wheres,
            remain_fields,
            assign_field_dict,
        )
        conn = conn or cls.rw_conn
        try:
            await conn.execute_query(sql)
            return True
        except Exception as e:
            logger.exception(e)
            return False
