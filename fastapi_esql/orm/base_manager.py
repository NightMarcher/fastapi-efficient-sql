from logging import getLogger
from typing import Any, Dict, List, Optional, Union

from tortoise import BaseDBAsyncClient, Model
from tortoise.queryset import Q

from .base_app import AppMetaclass
from ..utils.cursor_handler import CursorHandler
from ..utils.sqlizer import SQLizer

logger = getLogger(__name__)


class BaseManager(metaclass=AppMetaclass):

    model: Model = Model

    @classmethod
    async def get_by_pk(
        cls,
        pk: Any,
        conn: Optional[BaseDBAsyncClient] = None,
    ) -> Optional[Model]:
        return await cls.model.get_or_none(pk=pk).using_db(conn)

    @classmethod
    async def create_from_dict(cls, params: Dict[str, Any]) -> Optional[Model]:
        try:
            return await cls.model.create(**params, using_db=cls.rw_conn)
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
        *,
        index: Optional[str] = None,
        groups: Optional[List[str]] = None,
        having: Optional[str] = None,
        orders: Optional[List[str]] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        convert_fields: Optional[List[str]] = None,
        conn: Optional[BaseDBAsyncClient] = None,
    ):
        sql = SQLizer.select_custom_fields(
            cls.table,
            fields,
            wheres,
            index=index,
            groups=groups,
            having=having,
            orders=orders,
            offset=offset,
            limit=limit,
            model=cls.model,
        )
        conn = conn or cls.ro_conn
        converters = {
            f: cls.model._meta.fields_map[f].to_python_value
            for f in convert_fields if f in cls.model._meta.db_fields
        } if convert_fields else None
        return await CursorHandler.fetch_dicts(sql, conn, logger, converters)

    @classmethod
    async def select_one_record(
        cls,
        fields: List[str],
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        *,
        index: Optional[str] = None,
        groups: Optional[List[str]] = None,
        having: Optional[str] = None,
        orders: Optional[List[str]] = None,
        convert_fields: Optional[List[str]] = None,
        conn: Optional[BaseDBAsyncClient] = None,
    ):
        sql = SQLizer.select_custom_fields(
            cls.table,
            fields,
            wheres,
            index=index,
            groups=groups,
            having=having,
            orders=orders,
            offset=0,
            limit=1,
            model=cls.model,
        )
        conn = conn or cls.ro_conn
        converters = {
            f: cls.model._meta.fields_map[f].to_python_value
            for f in convert_fields if f in cls.model._meta.db_fields
        } if convert_fields else None
        return await CursorHandler.fetch_one(sql, conn, logger, converters)

    @classmethod
    async def update_json_field(
        cls,
        json_field: str,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        *,
        merge_dict: Optional[Dict[str, Any]] = None,
        path_value_dict: Optional[Dict[str, Any]] = None,
        remove_paths: Optional[List[str]] = None,
        json_type: type = dict,
    ):
        sql = SQLizer.update_json_field(
            cls.table,
            json_field,
            wheres,
            merge_dict=merge_dict,
            path_value_dict=path_value_dict,
            remove_paths=remove_paths,
            json_type=json_type,
            model=cls.model,
        )
        return await CursorHandler.sum_row_cnt(sql, cls.rw_conn, logger)

    @classmethod
    async def upsert_on_duplicate(
        cls,
        dicts: List[Dict[str, Any]],
        insert_fields: List[str],
        *,
        upsert_fields: Optional[List[str]] = None,
        merge_fields: Optional[List[str]] = None,
        using_values: bool = False,
    ):
        sql = SQLizer.upsert_on_duplicate(
            cls.table,
            dicts,
            insert_fields,
            upsert_fields=upsert_fields,
            merge_fields=merge_fields,
            using_values=using_values,
        )
        return await CursorHandler.sum_row_cnt(sql, cls.rw_conn, logger)

    @classmethod
    async def insert_into_select(
        cls,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        *,
        remain_fields: List[str] = None,
        assign_field_dict: Dict[str, Any] = None,
        to_table: Optional[str] = None,
    ):
        sql = SQLizer.insert_into_select(
            cls.table,
            wheres,
            remain_fields=remain_fields,
            assign_field_dict=assign_field_dict,
            to_table=to_table,
            model=cls.model,
        )
        return await CursorHandler.exec_if_ok(sql, cls.rw_conn, logger)

    @classmethod
    async def bulk_update_from_dicts(
        cls,
        dicts: List[Dict[str, Any]],
        join_fields: List[str],
        update_fields: List[str],
        *,
        merge_fields: Optional[List[str]] = None,
        using_values: bool = True,
    ):
        sql = SQLizer.bulk_update_from_dicts(
            cls.table,
            dicts,
            join_fields,
            update_fields,
            merge_fields=merge_fields,
            using_values=using_values,
        )
        return await CursorHandler.sum_row_cnt(sql, cls.rw_conn, logger)
