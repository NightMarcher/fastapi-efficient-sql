from logging import getLogger
from json import dumps
from typing import Any, Dict, List, Optional, Union

from tortoise import Model, __version__ as tortoise_version
from tortoise.queryset import Q
from tortoise.query_utils import QueryModifier

from ..const.error import QsParsingError, WrongParamsError

logger = getLogger(__name__)
# To ensure the functionality of the RawSQL
try:
    from tortoise.expressions import RawSQL
except ImportError:
    from tortoise.expressions import Term
    class RawSQL(Term):
        def __init__(self, sql: str):
            super().__init__()
            self.sql = sql


class Cases:
    """
    Simple case statement, like:
    'CASE `feild` WHEN ... THEN ... ELSE <default> END'.
    If your statement is more complex, please use RawSQL directly.
    """
    def __init__(self, field: str, whens: dict, default=None):
        self.field = field
        self.whens = whens
        self.default = default

    @property
    def sql(self):
        whens = " ".join(
            f"WHEN {k} THEN {SQLizer.sqlize_value(v)}"
            for k, v in self.whens.items()
        )
        else_ = " ELSE " + SQLizer.sqlize_value(self.default) if self.default is not None else ""
        return f"CASE {self.field} {whens}{else_} END"


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
            # NOTE Method `Q.resolve` changed since version 0.18.0
            # https://github.com/tortoise/tortoise-orm/commit/37178e175bc12bc4767b93142dab0209f9240c55
            if tortoise_version >= "0.18.0":
                modifier &= q.resolve(model, model._meta.basetable)
            else:
                modifier &= q.resolve(model, {}, {}, model._meta.basetable)
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
    def sqlize_value(cls, value, to_json=False) -> str:
        """
        Works like aiomysql.connection.Connection.escape
        """
        if value is None:
            return "NULL"
        elif isinstance(value, (Cases, RawSQL)):
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
        offset: Optional[int] = None,
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
        offset_ = "" if offset is None else f"{offset}, "
        limit_ = f"    LIMIT {offset_}{limit}" if limit else ""
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
    def update_json_field(
        cls,
        table: str,
        json_field: str,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        merge_dict: Optional[Dict[str, Any]] = None,
        path_value_dict: Optional[Dict[str, Any]] = None,
        remove_paths: Optional[List[str]] = None,
        json_type: type = dict,
        model: Optional[Model] = None,
    ) -> Optional[str]:
        if not all([table, json_field, wheres]):
            raise WrongParamsError("Please check your params")
        if not any([merge_dict, path_value_dict, remove_paths]):
            raise WrongParamsError("Please check your params")

        json_obj = f"COALESCE({json_field}, '{json_type()}')"
        if remove_paths:
            rps = ", ".join(f"'{p}'" for p in remove_paths)
            json_obj = f"JSON_REMOVE({json_obj}, {rps})"
        if path_value_dict:
            pvs = [
                f"'{path}',{cls.sqlize_value(value, to_json=True)}"
                for (path, value) in path_value_dict.items()
            ]
            json_obj = f"JSON_SET({json_obj}, {', '.join(pvs)})"
        if merge_dict:
            json_obj = f"JSON_MERGE_PATCH({json_obj}, {cls.sqlize_value(merge_dict)})"

        sql = f"""
    UPDATE {table} SET {json_field} =
    {json_obj}
    WHERE {cls.resolve_wheres(wheres, model)}
"""
        logger.debug(sql)
        return sql

    @classmethod
    def upsert_on_duplicate(
        cls,
        table: str,
        dicts: List[Dict[str, Any]],
        insert_fields: List[str],
        upsert_fields: List[str],
        using_values: bool = False,
    ) -> Optional[str]:
        if not all([table, dicts, insert_fields, upsert_fields]):
            raise WrongParamsError("Please check your params")

        values = [
            f"      ({', '.join(cls.sqlize_value(d.get(f)) for f in insert_fields)})"
            for d in dicts
        ]
        # NOTE Beginning with MySQL 8.0.19, it is possible to use an alias for the row
        # https://dev.mysql.com/doc/refman/8.0/en/insert-on-duplicate.html
        if using_values:
            upserts = [f"{field}=VALUES({field})" for field in upsert_fields]
            on_duplicate = f"ON DUPLICATE KEY UPDATE {', '.join(upserts)}"
        else:
            new_table = f"`new_{table}`"
            upserts = [f"{field}={new_table}.{field}" for field in upsert_fields]
            on_duplicate = f"AS {new_table} ON DUPLICATE KEY UPDATE {', '.join(upserts)}"

        sql = """
    INSERT INTO {}
      ({})
    VALUES
{}
    {}
""".format(
        table,
        ", ".join(insert_fields),
        ",\n".join(values),
        on_duplicate,
    )
        logger.debug(sql)
        return sql

    @classmethod
    def insert_into_select(
        cls,
        table: str,
        wheres: Union[str, Q, Dict[str, Any], List[Q]],
        remain_fields: List[str],
        assign_field_dict: Dict[str, Any],
        to_table: Optional[str] = None,
        model: Optional[Model] = None,
    ) -> Optional[str]:
        if not all([table, wheres] or not any([remain_fields, assign_field_dict])):
            raise WrongParamsError("Please check your params")

        fields = [*remain_fields]
        assign_fields = []
        for k, v in assign_field_dict.items():
            fields.append(k)
            assign_fields.append(f"{cls.sqlize_value(v)} {k}")

        sql = f"""
    INSERT INTO {to_table or table}
      ({", ".join(fields)})
    SELECT {", ".join(remain_fields + assign_fields)}
    FROM {table}
    WHERE {cls.resolve_wheres(wheres, model)}
"""
        logger.debug(sql)
        return sql

    @classmethod
    def build_fly_table(
        cls,
        dicts: List[Dict[str, Any]],
        fields: List[str],
        using_values: bool = True,
    ) -> Optional[str]:
        if not all([dicts, fields]):
            raise WrongParamsError("Please check your params")

        if using_values:
            rows = [
                f"          ROW({', '.join(cls.sqlize_value(d.get(f)) for f in fields)})"
                for d in dicts
            ]
            values = "VALUES\n" + ",\n".join(rows)
            table = f"fly_table ({', '.join(fields)})"
        else:
            rows = [
                f"SELECT {', '.join(f'{cls.sqlize_value(d.get(f))} {f}' for f in fields)}"
                for d in dicts
            ]
            values = "\n            UNION\n          ".join(rows)
            table = "fly_table"

        sql = f"""
        SELECT * FROM (
          {values}
        ) AS {table}"""
        logger.debug(sql)
        return sql

    @classmethod
    def bulk_update_from_dicts(
        cls,
        table: str,
        dicts: List[Dict[str, Any]],
        join_fields: List[str],
        update_fields: List[str],
        using_values: bool = True,
    ) -> Optional[str]:
        if not all([table, dicts, join_fields, update_fields]):
            raise WrongParamsError("Please check your params")

        joins = [f"{table}.{jf}=tmp.{jf}" for jf in join_fields]
        updates = [f"{table}.{uf}=tmp.{uf}" for uf in update_fields]

        sql = f"""
    UPDATE {table}
    JOIN ({SQLizer.build_fly_table(dicts, join_fields + update_fields, using_values)}
    ) tmp ON {", ".join(joins)}
    SET {", ".join(updates)}
"""
        logger.debug(sql)
        return sql
