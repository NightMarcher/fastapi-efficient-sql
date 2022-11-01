from logging import getLogger
from typing import Any, Dict, List, Optional, Union

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.models import Model

from .base_app import AppMetaclass
from ..utils.sqlizer import SQLizer
from ..utils.cursor_handler import CursorHandler

logger = getLogger(__name__)


class BaseManager(metaclass=AppMetaclass):

    model = Model

    @classmethod
    async def get_by_pk(
        cls,
        pk: Any,
        conn: Optional[BaseDBAsyncClient] = None,
    ) -> Optional[Model]:
        return await cls.model.get_or_none(pk=pk, using_db=conn)

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
    async def bulk_create_from_dicts(cls, dicts: List[Dict[str, Any]], **kwargs) -> bool:
        try:
            # NOTE Here is a bug in bulk_create. https://github.com/tortoise/tortoise-orm/issues/1281
            await cls.model.bulk_create(
                objects=[cls.model(**d) for d in dicts],
                **kwargs,
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
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        groups: Optional[List[str]] = None,
        having: Optional[str] = None,
        orders: Optional[List[str]] = None,
        limit: int = 0,
        conn: Optional[BaseDBAsyncClient] = None,
    ):
        sql = SQLizer.select_custom_fields(
            cls.table,
            fields,
            wheres,
            groups,
            having,
            orders,
            limit,
            cls.model,
        )
        conn = conn or cls.ro_conn
        return await CursorHandler.fetch_dicts(sql, conn, logger)

    @classmethod
    async def upsert_json_field(
        cls,
        json_field: str,
        path_value_dict: Dict[str, Any],
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
    ):
        sql = SQLizer.upsert_json_field(
            cls.table,
            json_field,
            path_value_dict,
            wheres,
            cls.model,
        )
        return await CursorHandler.sum_row_cnt(sql, cls.rw_conn, logger)

    @classmethod
    async def upsert_on_duplicated(
        cls,
        dicts: List[Dict[str, Any]],
        insert_fields: List[str],
        upsert_fields: List[str],
    ):
        sql = SQLizer.upsert_on_duplicated(
            cls.table,
            dicts,
            insert_fields,
            upsert_fields,
        )
        return await CursorHandler.sum_row_cnt(sql, cls.rw_conn, logger)

    @classmethod
    async def insert_into_select(
        cls,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        remain_fields: List[str],
        assign_field_dict: Dict[str, Any],
    ):
        sql = SQLizer.insert_into_select(
            cls.table,
            wheres,
            remain_fields,
            assign_field_dict,
            cls.model,
        )
        return await CursorHandler.exec_if_ok(sql, cls.rw_conn, logger)

    @classmethod
    async def bulk_update_with_fly_table(
        cls,
        dicts: List[Dict[str, Any]],
        join_fields: List[str],
        update_fields: List[str],
    ):
        sql = SQLizer.bulk_update_with_fly_table(
            cls.table,
            dicts,
            join_fields,
            update_fields,
        )
        return await CursorHandler.sum_row_cnt(sql, cls.rw_conn, logger)
