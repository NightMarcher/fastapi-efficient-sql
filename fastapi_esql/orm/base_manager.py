import logging
from typing import Any, Dict, List, Optional

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.models import Model

from .base_app import AppMetaclass
from .base_model import BaseModel
from ..utils.sqlizer import SQLizer
from ..utils.cursor_handler import CursorHandler

logger = logging.getLogger(__name__)


class BaseManager(metaclass=AppMetaclass):

    model = BaseModel

    @classmethod
    async def create_from_dict(cls, params: Dict[str, Any]) -> Optional[Model]:
        params["using_db"] = cls.rw_conn
        try:
            return await cls.model.create(**params)
        except Exception as e:
            logger.exception(e)
            return None

    @classmethod
    async def update_from_dict(cls, obj: Model, params: Dict[str, Any]) -> bool:
        try:
            await obj.update_from_dict(params).save(
                update_fields=params.keys(),
                using_db=cls.rw_conn,
            )
            return True
        except Exception as e:
            logger.exception(e)
            return False

    @classmethod
    async def bulk_create_from_dicts(cls, dicts: List[Dict[str, Any]]) -> bool:
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
    ):
        sql = SQLizer.select_custom_fields(
            cls.model._meta.db_table,
            fields,
            wheres,
        )
        conn = conn or cls.ro_conn
        return await CursorHandler.fetch_dicts(sql, conn, logger)

    @classmethod
    async def upsert_json_field(
        cls,
        json_field: str,
        path_value_dict: Dict[str, Any],
        wheres: List[str],
        conn: Optional[BaseDBAsyncClient] = None,
    ):
        sql = SQLizer.upsert_json_field(
            cls.model._meta.db_table,
            json_field,
            path_value_dict,
            wheres,
        )
        conn = conn or cls.rw_conn
        return await CursorHandler.calc_row_cnt(sql, conn, logger)

    @classmethod
    async def upsert_on_duplicated(
        cls,
        dicts: List[Dict[str, Any]],
        insert_fields: List[str],
        upsert_fields: List[str],
        conn: Optional[BaseDBAsyncClient] = None,
    ):
        sql = SQLizer.upsert_on_duplicated(
            cls.model._meta.db_table,
            dicts,
            insert_fields,
            upsert_fields,
        )
        conn = conn or cls.rw_conn
        return await CursorHandler.calc_row_cnt(sql, conn, logger)

    @classmethod
    async def insert_into_select(
        cls,
        wheres: List[str],
        remain_fields: List[str],
        assign_field_dict: Dict[str, Any],
        conn: Optional[BaseDBAsyncClient] = None,
    ):
        sql = SQLizer.insert_into_select(
            cls.model._meta.db_table,
            wheres,
            remain_fields,
            assign_field_dict,
        )
        conn = conn or cls.rw_conn
        return await CursorHandler.exec_if_ok(sql, conn, logger)
