from logging import getLogger
from json import dumps
from typing import Any, Dict, List, Optional, Union

from tortoise import Model
from tortoise.queryset import Q
from tortoise.query_utils import QueryModifier

from ..const.error import QsParsingError, WrongParamsError

logger = getLogger(__name__)
# ensure the functionality of the RawSQL
try:
    from tortoise.expressions import RawSQL
except ImportError:
    from tortoise.expressions import Term
    class RawSQL(Term):
        def __init__(self, sql: str):
            super().__init__()
            self.sql = sql


class SQLizer:

    @classmethod
    def resolve_wheres(
        cls,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        model: Optional[Model] = None,
    ) -> str:
        if not model and not isinstance(wheres, str):
            raise WrongParamsError("Parameter `wheres` only support str type if no model passed")

        if isinstance(wheres, str):
            return wheres
        elif isinstance(wheres, Q):
            qs = [wheres]
        elif isinstance(wheres, dict):
            qs = [Q(**{key: value}) for (key, value) in wheres.items()]
        elif isinstance(wheres, list):
            qs = [q for q in wheres if isinstance(q, Q)]
        else:
            raise WrongParamsError("Parameter `wheres` only supports str, dict and list type")

        if not qs:
            raise QsParsingError("Parsing `wheres` for qs failed!")

        modifier = QueryModifier()
        for q in qs:
            modifier &= q.resolve(model, model._meta.basetable)
        return modifier.where_criterion.get_sql(quote_char="`")

    @classmethod
    def resolve_orders(cls, orders: List[str]) -> str:
        orders_ = []
        for o in orders:
            if o.startswith("-"):
                order = "DESC"
            else:
                order = "ASC"
            orders_.append(f"{o.strip('-')} {order}")
        return ", ".join(orders_)

    @classmethod
    def _sqlize_value(cls, value, to_json=False) -> str:
        """
        Works like aiomysql.connection.Connection.escape
        """
        if value is None:
            return "NULL"
        elif isinstance(value, RawSQL):
            return value.sql
        elif isinstance(value, (int, float, bool)):
            return f"{value}"
        elif isinstance(value, (dict, list, tuple)):
            dumped = dumps(value, ensure_ascii=False)
            if to_json:
                return f"CAST('{dumped}' AS JSON)"
                # Same with above line
                # return f"JSON_EXTRACT('{dumped}', '$')"
            return f"'{dumped}'"
        else:
            return f"'{value}'"

    @classmethod
    def select_custom_fields(
        cls,
        table: str,
        fields: List[str],
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        groups: Optional[List[str]] = None,
        having: Optional[str] = None,
        orders: Optional[List[str]] = None,
        limit: int = 0,
        model: Optional[Model] = None,
    ) -> Optional[str]:
        if not all([table, fields, wheres]):
            raise WrongParamsError("Please check your params")
        if having and not groups:
            raise WrongParamsError("Parameter `groups` shoud be no empty when `having` isn't")

        group_by = f"    GROUP BY {', '.join(groups)}" if groups else ""
        having_ = f"    HAVING {having}" if having else ""
        order_by = f"    ORDER BY {cls.resolve_orders(orders)}" if orders else ""
        limit_ = f"    LIMIT {limit}" if limit else ""
        # NOTE Doesn't support `offset` parameter due to it's bad performance
        extras = [group_by, having_, order_by, limit_]

        sql = """
    SELECT
        {}
    FROM {}
    WHERE {}
{}""".format(
        ", ".join(fields),
        table,
        cls.resolve_wheres(wheres, model),
        "\n".join(i for i in extras if i),
    )
        logger.debug(sql)
        return sql

    @classmethod
    def upsert_json_field(
        cls,
        table: str,
        json_field: str,
        path_value_dict: Dict[str, Any],
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        model: Optional[Model] = None,
    ) -> Optional[str]:
        if not all([table, json_field, path_value_dict, wheres]):
            raise WrongParamsError("Please check your params")

        params = []
        for (path, value) in path_value_dict.items():
            params.append(f"'{path}'")
            params.append(cls._sqlize_value(value, to_json=True))

        sql = f"""
    UPDATE {table}
    SET {json_field} = JSON_SET(COALESCE({json_field}, '{{}}'), {", ".join(params)})
    WHERE {cls.resolve_wheres(wheres, model)}"""
        logger.debug(sql)
        return sql

    @classmethod
    def upsert_on_duplicated(
        cls,
        table: str,
        dicts: List[Dict[str, Any]],
        insert_fields: List[str],
        upsert_fields: List[str],
    ) -> Optional[str]:
        if not all([table, dicts, insert_fields, upsert_fields]):
            raise WrongParamsError("Please check your params")

        values = [
            f"({', '.join(cls._sqlize_value(d.get(f)) for f in insert_fields)})"
            for d in dicts
        ]
        # logger.debug(values)
        new_table = f"`new_{table}`"
        upserts = [f"{field}={new_table}.{field}" for field in upsert_fields]

        sql = f"""
    INSERT INTO {table}
        ({", ".join(insert_fields)})
    VALUES
        {", ".join(values)}
    AS {new_table}
    ON DUPLICATE KEY UPDATE {", ".join(upserts)}"""
        logger.debug(sql)
        return sql

    @classmethod
    def insert_into_select(
        cls,
        table: str,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        remain_fields: List[str],
        assign_field_dict: Dict[str, Any],
        model: Optional[Model] = None,
    ) -> Optional[str]:
        if not all([table, wheres] or not any([remain_fields, assign_field_dict])):
            raise WrongParamsError("Please check your params")

        fields = [*remain_fields]
        assign_fields = []
        for k, v in assign_field_dict.items():
            fields.append(k)
            assign_fields.append(f"{cls._sqlize_value(v)} {k}")
        # logger.debug(assign_fields)

        sql = f"""
    INSERT INTO {table}
        ({", ".join(fields)})
    SELECT {", ".join(remain_fields + assign_fields)}
    FROM {table}
    WHERE {cls.resolve_wheres(wheres, model)}"""
        logger.debug(sql)
        return sql

    @classmethod
    def build_fly_table(
        cls,
        dicts: List[Dict[str, Any]],
        fields: List[str],
    ) -> Optional[str]:
        if not all([dicts, fields]):
            raise WrongParamsError("Please check your params")

        rows = [
            f"ROW({', '.join(cls._sqlize_value(d.get(f)) for f in fields)})"
            for d in dicts
        ]

        sql = f"""
        SELECT * FROM (
            VALUES
                {", ".join(rows)}
        ) AS fly_table ({", ".join(fields)})"""
        logger.debug(sql)
        return sql

    @classmethod
    def bulk_update_with_fly_table(
        cls,
        table: str,
        dicts: List[Dict[str, Any]],
        join_fields: List[str],
        update_fields: List[str],
    ) -> Optional[str]:
        if not all([table, dicts, join_fields, update_fields]):
            raise WrongParamsError("Please check your params")

        joins = [f"{table}.{jf}=tmp.{jf}" for jf in join_fields]
        updates = [f"{table}.{uf}=tmp.{uf}" for uf in update_fields]

        sql = f"""
    UPDATE {table}
    JOIN ({SQLizer.build_fly_table(dicts, join_fields + update_fields)}
    ) tmp ON {", ".join(joins)}
    SET {", ".join(updates)}"""
        logger.debug(sql)
        return sql
