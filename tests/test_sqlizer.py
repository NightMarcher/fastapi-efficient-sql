from asynctest import TestCase
from datetime import datetime

from tortoise import run_async

from examples.service.models.demo import Account
from examples.service.constants.enums import GenderEnum, LocaleEnum
from fastapi_esql import (
    Cases, RawSQL, SQLizer,
    Q, QsParsingError, WrongParamsError,
)
from . import init_tortoise

run_async(init_tortoise())


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

    model = Account
    table = Account.Meta.table

    def test_resolve_wheres(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.resolve_wheres(object())

        aids = (1, 2, 3)
        assert SQLizer.resolve_wheres(
            f"id IN ({','.join(map(str, aids))}) AND gender=1"
        ) == "id IN (1,2,3) AND gender=1"
        assert SQLizer.resolve_wheres(
            Q(Q(id__in=aids), Q(gender=1), join_type="AND"), self.model
        ) == "`id` IN (1,2,3) AND `gender`=1"
        assert SQLizer.resolve_wheres(
            {"id__in": aids, "gender": 1}, self.model
        ) == "`id` IN (1,2,3) AND `gender`=1"
        assert SQLizer.resolve_wheres(
            [Q(id__in=aids), Q(gender=1)], self.model
        ) == "`id` IN (1,2,3) AND `gender`=1"

        with self.assertRaises(WrongParamsError):
            SQLizer.resolve_wheres(set())

        with self.assertRaises(QsParsingError):
            SQLizer.resolve_wheres({}, self.model)

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

    def test_select_custom_fields(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.select_custom_fields(
                "",
                fields=["locale", "gender"],
                wheres=Q(id__range=[1, 12]),
            )

        with self.assertRaises(WrongParamsError):
            SQLizer.select_custom_fields(
                self.table,
                fields=["locale", "gender"],
                wheres=Q(id__range=[1, 12]),
                having="cnt > 0",
            )

        aids = [1, 2, 3]
        basic_sql = SQLizer.select_custom_fields(
            self.table,
            fields=[
                "id", "extend ->> '$.last_login.ipv4' ipv4",
                "extend ->> '$.last_login.start_datetime' start_datetime",
                "CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec"
            ],
            wheres=f"id IN ({','.join(map(str, aids))}) AND gender=1",
            index="PRIMARY",
            model=self.model,
        )
        assert basic_sql == """
    SELECT
      id, extend ->> '$.last_login.ipv4' ipv4, extend ->> '$.last_login.start_datetime' start_datetime, CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec
    FROM `account` FORCE INDEX (`PRIMARY`)
    WHERE id IN (1,2,3) AND gender=1
"""

        complex_sql = SQLizer.select_custom_fields(
            self.table,
            fields=["locale", "gender", "COUNT(1) cnt"],
            wheres=Q(id__range=[1, 12]),
            groups=["locale", "gender"],
            having="cnt > 0",
            orders=["locale", "-gender"],
            limit=10,
            model=self.model,
        )
        assert complex_sql == """
    SELECT
      locale, gender, COUNT(1) cnt
    FROM `account`
    WHERE `id` BETWEEN 1 AND 12
    GROUP BY locale, gender
    HAVING cnt > 0
    ORDER BY locale ASC, gender DESC
    LIMIT 10"""

        paging_sql = SQLizer.select_custom_fields(
            self.table,
            fields=["locale", "gender"],
            wheres=Q(id__range=[1, 12]),
            offset=100,
            limit=5,
            model=self.model,
        )
        assert paging_sql == """
    SELECT
      locale, gender
    FROM `account`
    WHERE `id` BETWEEN 1 AND 12
    LIMIT 100, 5"""

    def test_update_json_field(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.update_json_field(
                self.table,
                json_field="",
                wheres=Q(id=8),
            )

        with self.assertRaises(WrongParamsError):
            SQLizer.update_json_field(
                self.table,
                json_field="extend",
                wheres=Q(id=8),
            )

        sql = SQLizer.update_json_field(
            self.table,
            json_field="extend",
            wheres=Q(id=8),
            merge_dict={
                "updated_at": "2022-10-30 21:34:15",
                "info": {
                    "online_sec": 636,
                }
            },
            path_value_dict={
                "$.last_login": {
                    "ipv4": "209.182.101.161",
                },
                "$.uuid": "fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f",
            },
            remove_paths=["$.deprecated"],
            json_type=dict,
            model=self.model,
        )
        assert sql == """
    UPDATE `account` SET extend =
    JSON_MERGE_PATCH(JSON_SET(JSON_REMOVE(COALESCE(extend, '{}'), '$.deprecated'), '$.last_login',CAST('{"ipv4": "209.182.101.161"}' AS JSON), '$.uuid','fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f'), '{"updated_at": "2022-10-30 21:34:15", "info": {"online_sec": 636}}')
    WHERE `id`=8
"""

        sql = SQLizer.update_json_field(
            self.table,
            json_field="extend",
            wheres=Q(id=8),
            merge_dict={
                "updated_at": "2022-10-30 21:34:15",
                "info": {
                    "online_sec": 636,
                }
            },
            path_value_dict={
                "$.last_login": {
                    "ipv4": "209.182.101.161",
                },
                "$.uuid": "fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f",
            },
            remove_paths=["$.deprecated"],
            json_type=dict,
            assign_field_dict={
                "active": True,
                "name": "new_name",
            },
            model=self.model,
        )
        assert sql == """
    UPDATE `account` SET extend =
    JSON_MERGE_PATCH(JSON_SET(JSON_REMOVE(COALESCE(extend, '{}'), '$.deprecated'), '$.last_login',CAST('{"ipv4": "209.182.101.161"}' AS JSON), '$.uuid','fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f'), '{"updated_at": "2022-10-30 21:34:15", "info": {"online_sec": 636}}')
    , active=True, name='new_name'
    WHERE `id`=8
"""

    def test_upsert_on_duplicate(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.upsert_on_duplicate(
                self.table,
                [],
                insert_fields=["id", "gender", "name", "locale", "extend"],
                upsert_fields=["name", "locale"],
            )

        old_sql = SQLizer.upsert_on_duplicate(
            self.table,
            [
                {"id": 10, "gender": 2, "name": "佐々木 美加子", "locale": "ja_JP", "extend": {"rdm": 6}},
                {"id": 11, "gender": 0, "name": "Seher Bumb", "locale": "en_IN", "extend": {"rdm": 4}},
                {"id": 12, "gender": 0, "name": "谢冬梅", "locale": "zh_CN", "extend": {"rdm": 6}},
            ],
            insert_fields=["id", "gender", "name", "locale", "extend"],
            upsert_fields=["gender", "name"],
            merge_fields=["extend"],
            using_values=True,
        )
        assert old_sql == """
    INSERT INTO `account`
      (id, gender, name, locale, extend)
    VALUES
      (10, 2, '佐々木 美加子', 'ja_JP', '{"rdm": 6}'),
      (11, 0, 'Seher Bumb', 'en_IN', '{"rdm": 4}'),
      (12, 0, '谢冬梅', 'zh_CN', '{"rdm": 6}')
    ON DUPLICATE KEY UPDATE gender=VALUES(gender), name=VALUES(name), extend=JSON_MERGE_PATCH(COALESCE(`account`.extend, '{}'), VALUES(extend))
"""

        new_sql = SQLizer.upsert_on_duplicate(
            self.table,
            [
                {"id": 10, "gender": 1, "name": "田中 知実", "locale": "ja_JP", "extend": {"rdm": 1}},
                {"id": 11, "gender": 2, "name": "Tara Chadha", "locale": "en_IN", "extend": {"rdm": 10}},
                {"id": 12, "gender": 2, "name": "吴磊", "locale": "zh_CN", "extend": {"rdm": 9}},
            ],
            insert_fields=["id", "gender", "name", "locale", "extend"],
            upsert_fields=["gender", "name"],
            merge_fields=["extend"],
        )
        assert new_sql == """
    INSERT INTO `account`
      (id, gender, name, locale, extend)
    VALUES
      (10, 1, '田中 知実', 'ja_JP', '{"rdm": 1}'),
      (11, 2, 'Tara Chadha', 'en_IN', '{"rdm": 10}'),
      (12, 2, '吴磊', 'zh_CN', '{"rdm": 9}')
    AS `new_account` ON DUPLICATE KEY UPDATE gender=`new_account`.gender, name=`new_account`.name, extend=JSON_MERGE_PATCH(COALESCE(`account`.extend, '{}'), `new_account`.extend)
"""

        only_insert_sql = SQLizer.upsert_on_duplicate(
            self.table,
            [
                {"id": 10, "gender": 2, "name": "池田 幹", "locale": "ja_JP", "extend": {"rdm": 9}},
                {"id": 11, "gender": 0, "name": "Sana Mani", "locale": "en_IN", "extend": {"rdm": 0}},
                {"id": 12, "gender": 0, "name": "刘柳", "locale": "zh_CN", "extend": {"rdm": 9}},
            ],
            insert_fields=["id", "gender", "name", "locale", "extend"],
        )
        assert only_insert_sql == """
    INSERT INTO `account`
      (id, gender, name, locale, extend)
    VALUES
      (10, 2, '池田 幹', 'ja_JP', '{"rdm": 9}'),
      (11, 0, 'Sana Mani', 'en_IN', '{"rdm": 0}'),
      (12, 0, '刘柳', 'zh_CN', '{"rdm": 9}')
"""

    def test_insert_into_select(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.insert_into_select(
                self.table,
                wheres=Q(id__in=[4, 5, 6]),
                remain_fields=[],
                assign_field_dict={},
            )

        archive_sql = SQLizer.insert_into_select(
            self.table,
            wheres=Q(id__in=[4, 5, 6]),
            remain_fields=["gender"],
            assign_field_dict={
                "locale": Cases("id", {3: LocaleEnum.zh_CN, 4: LocaleEnum.en_US, 5: LocaleEnum.fr_FR}, default=""),
                "active": False,
                "name": RawSQL("CONCAT(LEFT(name, 26), ' [NEW]')"),
                "extend": {},
            },
            to_table="account_bak",
            model=self.model,
        )
        assert archive_sql == """
    INSERT INTO `account_bak`
      (gender, locale, active, name, extend)
    SELECT gender, CASE id WHEN 3 THEN 'zh_CN' WHEN 4 THEN 'en_US' WHEN 5 THEN 'fr_FR' ELSE '' END locale, False active, CONCAT(LEFT(name, 26), ' [NEW]') name, '{}' extend
    FROM `account`
    WHERE `id` IN (4,5,6)
"""

        copy_sql = SQLizer.insert_into_select(
            self.table,
            wheres=Q(id__in=[4, 5, 6]),
            remain_fields=["gender"],
            assign_field_dict={
                "locale": Cases("id", {3: LocaleEnum.zh_CN, 4: LocaleEnum.en_US, 5: LocaleEnum.fr_FR}, default=""),
                "active": False,
                "name": RawSQL("CONCAT(LEFT(name, 26), ' [NEW]')"),
                "extend": {},
            },
            model=self.model,
        )
        assert copy_sql == """
    INSERT INTO `account`
      (gender, locale, active, name, extend)
    SELECT gender, CASE id WHEN 3 THEN 'zh_CN' WHEN 4 THEN 'en_US' WHEN 5 THEN 'fr_FR' ELSE '' END locale, False active, CONCAT(LEFT(name, 26), ' [NEW]') name, '{}' extend
    FROM `account`
    WHERE `id` IN (4,5,6)
"""

    def test_build_fly_table(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.build_fly_table(
                [],
                fields=["id", "active", "gender"],
            )

        old_sql = SQLizer.build_fly_table(
            [
                {"id": 7, "active": False, "gender": GenderEnum.male},
                {"id": 15, "active": True, "gender": GenderEnum.unknown}
            ],
            fields=["id", "active", "gender"],
            using_values=False,
        )
        assert old_sql == """
        SELECT * FROM (
          SELECT 7 id, False active, 1 gender
            UNION
          SELECT 15 id, True active, 0 gender
        ) AS fly_table"""

        new_sql = SQLizer.build_fly_table(
            [
                {"id": 7, "active": False, "gender": GenderEnum.male},
                {"id": 15, "active": True, "gender": GenderEnum.unknown}
            ],
            fields=["id", "active", "gender"],
            using_values=True,
        )
        assert new_sql == """
        SELECT * FROM (
          VALUES
          ROW(7, False, 1),
          ROW(15, True, 0)
        ) AS fly_table (id, active, gender)"""

    def test_bulk_update_from_dicts(self):
        with self.assertRaises(WrongParamsError):
            SQLizer.bulk_update_from_dicts(
                self.table,
                [],
                join_fields=["id"],
                update_fields=["active", "gender"],
            )

        sql = SQLizer.bulk_update_from_dicts(
            self.table,
            [
                {"id": 7, "active": False, "deleted": False, "gender": GenderEnum.male, "extend": {"test": 1, "debug": 0}},
                {"id": 15, "active": True, "deleted": False, "gender": GenderEnum.unknown, "extend": {"test": 1, "debug": 0}}
            ],
            join_fields=["id", "deleted"],
            update_fields=["active", "gender"],
            merge_fields=["extend"],
        )
        assert sql == """
    UPDATE `account`
    JOIN (
        SELECT * FROM (
          VALUES
          ROW(7, False, False, 1, '{"test": 1, "debug": 0}'),
          ROW(15, False, True, 0, '{"test": 1, "debug": 0}')
        ) AS fly_table (id, deleted, active, gender, extend)
    ) tmp ON `account`.id=tmp.id AND `account`.deleted=tmp.deleted
    SET `account`.active=tmp.active, `account`.gender=tmp.gender, `account`.extend=JSON_MERGE_PATCH(COALESCE(`account`.extend, '{}'), tmp.extend)
"""

    # def test_(self):
    #     sql = SQLizer()
    #     assert sql == """
    #     """
