from json import dumps
from typing import List, Optional

from fastapi_esql.const.error import WrongParamsError


class SQLizer:

    @classmethod
    def _sqlize_value(cls, value, to_json=False) -> str:
        """
        Works like aiomysql.connection.Connection.escape
        """
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float, bool)):
            return f"{value}"
        elif isinstance(value, (dict, list)):
            dumped = dumps(value, ensure_ascii=False)
            if to_json:
                return f"JSON_EXTRACT('{dumped}', '$')"
                # Same with above line
                # return f"CAST('{dumped}' AS JSON)"
            return f"'{dumped}'"
        else:
            return f"'{value}'"

    @classmethod
    def query_custom_fields(
        cls,
        table: str,
        fields: List[str],
        wheres: List[str],
    ) -> Optional[str]:
        """
        """
        if not all([table, fields, wheres]):
            raise WrongParamsError("Please check your params")

        sql = f"""
SELECT {", ".join(fields)}
FROM {table}
WHERE {" AND ".join(wheres)}
        """
        print(sql)
        return sql

    @classmethod
    def upsert_json(
        cls,
        table: str,
        json_field: str,
        path_value_dict: dict,
        wheres: List[str],
    ) -> Optional[str]:
        """
        """
        if not all([table, json_field, path_value_dict, wheres]):
            raise WrongParamsError("Please check your params")

        params = []
        for (path, value) in path_value_dict.items():
            params.append(f"'{path}'")
            params.append(cls._sqlize_value(value, to_json=True))

        sql = f"""
UPDATE {table}
SET {json_field} = JSON_SET(COALESCE({json_field}, '{{}}'), {", ".join(params)})
WHERE {" AND ".join(wheres)}
            """
        print(sql)
        return sql

    @classmethod
    def insert_into_select(
        cls,
        table: str,
        wheres: List[str],
        remain_fields: List[str],
        assign_field_dict: dict,
    ) -> Optional[str]:
        """
        """
        if not all([table, wheres] or not any([remain_fields, assign_field_dict])):
            raise WrongParamsError("Please check your params")

        fields = [*remain_fields]
        assign_fields = []
        for k, v in assign_field_dict.items():
            fields.append(k)
            assign_fields.append(f"{cls._sqlize_value(v)} {k}")

        sql = f"""
INSERT INTO {table}
    ({", ".join(fields)})
SELECT {", ".join(remain_fields + assign_fields)}
FROM {table}
WHERE {" AND ".join(wheres)}
        """
        return sql

    @classmethod
    def upsert_on_duplicate_key(
        cls,
        table: str,
        dicts: List[dict],
        insert_fields,
        upsert_fields,
    ) -> Optional[str]:
        """
        """
        if not all([table, dicts, insert_fields, upsert_fields]):
            raise WrongParamsError("Please check your params")

        values = []
        for d in dicts:
            values.append(
                f"({', '.join(map(lambda val: cls._sqlize_value(d.get(val)), insert_fields))})")
        upserts = []
        for field in upsert_fields:
            upserts.append(f"{field}=VALUES({field})")

        sql = f"""
INSERT INTO {table}
({", ".join(insert_fields)})
VALUES
{", ".join(values)}
ON DUPLICATE KEY UPDATE {", ".join(upserts)}
            """
        return sql
