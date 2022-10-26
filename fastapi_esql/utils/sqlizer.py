import logging
from json import dumps
from typing import Any, Dict, List, Optional

from ..const.error import WrongParamsError

logger = logging.getLogger(__name__)
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
        elif isinstance(value, (dict, list)):
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
        wheres: List[str],
        groupbys: Optional[List[str]] = None,
    ) -> Optional[str]:
        if not all([table, fields, wheres]):
            raise WrongParamsError("Please check your params")

        group_by = f"GROUP BY {', '.join(groupbys)}" if groupbys else ""
        sql = f"""
    SELECT
        {", ".join(fields)}
    FROM {table}
    WHERE {" AND ".join(wheres)}
    {group_by}"""
        logger.debug(sql)
        return sql

    @classmethod
    def upsert_json_field(
        cls,
        table: str,
        json_field: str,
        path_value_dict: Dict[str, Any],
        wheres: List[str],
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
    WHERE {" AND ".join(wheres)}"""
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

        values = []
        for d in dicts:
            values.append(f"({', '.join(cls._sqlize_value(d.get(f)) for f in insert_fields)})")
        # logger.debug(values)
        upserts = []
        for field in upsert_fields:
            upserts.append(f"{field}=VALUES({field})")

        sql = f"""
    INSERT INTO {table}
        ({", ".join(insert_fields)})
    VALUES
        {", ".join(values)}
    ON DUPLICATE KEY UPDATE {", ".join(upserts)}"""
        logger.debug(sql)
        return sql

    @classmethod
    def insert_into_select(
        cls,
        table: str,
        wheres: List[str],
        remain_fields: List[str],
        assign_field_dict: Dict[str, Any],
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
    WHERE {" AND ".join(wheres)}"""
        logger.debug(sql)
        return sql
