from datetime import datetime
from unittest import TestCase

from fastapi_esql import (
    Cases, RawSQL, SQLizer,
    Q, QsParsingError, WrongParamsError,
)

from . import init_test_orm
from examples.service.models.demo import Account


class TestRawSQL(TestCase):

    def test_init(self):
        s = "sql statement"
        raw_sql = RawSQL(s)
        assert raw_sql.sql == s


class TestCases(TestCase):

    mapping = {0: "No", 1: "Yes"}

    def test_default(self):
        cases = Cases("is_ok", self.mapping, "Unknown")
        assert cases.sql == "CASE is_ok WHEN 0 THEN 'No' WHEN 1 THEN 'Yes' ELSE 'Unknown' END"

    def test_no_default(self):
        cases = Cases("is_ok", self.mapping)
        assert cases.sql == "CASE is_ok WHEN 0 THEN 'No' WHEN 1 THEN 'Yes' END"


class TestSQLizer(TestCase):

    def test_resolve_wheres(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.resolve_wheres(object())

        aids = (1, 2, 3)
        assert SQLizer.resolve_wheres(
            f"id IN ({','.join(map(str, aids))}) AND gender=1"
        ) == "id IN (1,2,3) AND gender=1"
        init_test_orm()
        assert SQLizer.resolve_wheres(
            Q(Q(id__in=aids), Q(gender=1), join_type="AND"), Account
        ) == "`id` IN (1,2,3) AND `gender`=1"
        assert SQLizer.resolve_wheres(
            {"id__in": aids, "gender": 1}, Account
        ) == "`id` IN (1,2,3) AND `gender`=1"
        assert SQLizer.resolve_wheres(
            [Q(id__in=aids), Q(gender=1)], Account
        ) == "`id` IN (1,2,3) AND `gender`=1"

        with self.assertRaises(WrongParamsError):
            SQLizer.resolve_wheres(set())

        with self.assertRaises(QsParsingError):
            SQLizer.resolve_wheres({}, Account)

    def test_resolve_orders(self):
        orders = SQLizer.resolve_orders(["-created_at", "name"])
        assert orders == "created_at DESC, name ASC"

    def test_sqlize_value(self):
        assert SQLizer.sqlize_value(None) == "NULL"

        raw_sql = RawSQL("statement")
        assert SQLizer.sqlize_value(raw_sql) == raw_sql.sql
        cases = Cases("is_ok", {0: "No", 1: "Yes"})
        assert SQLizer.sqlize_value(cases) == cases.sql

        assert SQLizer.sqlize_value(1024) == "1024"
        assert SQLizer.sqlize_value(0.125) == "0.125"
        assert SQLizer.sqlize_value(True) == "True"

        assert (
            SQLizer.sqlize_value({"gender": 0, "name": "羊淑兰"}, to_json=True)
            == """CAST('{"gender": 0, "name": "羊淑兰"}' AS JSON)"""
        )
        assert SQLizer.sqlize_value([1, 2, 4]) == "'[1, 2, 4]'"
        assert SQLizer.sqlize_value(("a", "b", "c")) == """'["a", "b", "c"]'"""

        assert SQLizer.sqlize_value(datetime(2023, 1, 1, 12, 30)) == "'2023-01-01 12:30:00'"
