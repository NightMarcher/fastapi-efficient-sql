# fastapi-efficient-sql

## Some preparations before using efficient sql
```python
from fastapi_esql import AppMetaclass, BaseManager, BaseModel


class DemoMetaclass(AppMetaclass):

    def get_ro_conn(self):
        return Tortoise.get_connection("demo_ro")

    def get_rw_conn(self):
        return Tortoise.get_connection("demo_rw")


class Account(BaseModel):
    id = fields.IntField(pk=True)
    active = fields.BooleanField(null=False, default=True)
    gender = fields.IntEnumField(GenderEnum, null=False, default=GenderEnum.unknown)
    name = fields.CharField(max_length=32, null=False, default="")
    locale = fields.CharEnumField(LocaleEnum, max_length=5, null=False)


class AccountMgr(BaseManager, metaclass=DemoMetaclass):
    model = Account
```

## Some supported efficient sql
### **select_custom_fields**
**basic example**
```python
await AccountMgr.select_custom_fields(
    fields=[
        "id", "extend ->> '$.last_login.ipv4' ipv4",
        "extend ->> '$.last_login.start_datetime' start_datetime",
        "CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec"
    ],
    wheres=[f"id IN (1, 2, 3)"],
)
```
Generate sql and execute
```sql
    SELECT
        id, extend ->> '$.last_login.ipv4' ipv4, extend ->> '$.last_login.start_datetime' start_datetime, CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec
    FROM account
    WHERE id IN (1, 2, 3)
```

**complex example**
```python
await AccountMgr.select_custom_fields(
    fields=[
        "locale", "gender", "COUNT(1) cnt"
    ],
    wheres=["id BETWEEN 1 AND 12"],
    groups=["locale", "gender"],
    havings=["cnt > 0"],
    orders=["locale", "-gender"],
    limit=10,
)
```
Generate sql and execute
```sql
    SELECT
        locale, gender, COUNT(1) cnt
    FROM account
    WHERE id BETWEEN 1 AND 12
    GROUP BY locale, gender
    HAVING cnt > 0
    ORDER BY locale ASC, gender DESC
    LIMIT 10
```

### **upsert_json_field**
```python
await AccountMgr.upsert_json_field(
    json_field="extend",
    path_value_dict={
        "$.last_login": {
            "ipv4": "209.182.101.161",
            "start_datetime": "2022-10-16 11:11:05",
            "online_sec": 4209,
        },
        "$.uuid": "fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f",
    },
    wheres=[f"id = 8"],
)
```
Generate sql and execute
```sql
    UPDATE account
    SET extend = JSON_SET(COALESCE(extend, '{}'), '$.last_login', CAST('{"ipv4": "209.182.101.161", "start_datetime": "2022-10-16 11:11:05", "online_sec": 4209}' AS JSON), '$.uuid', 'fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f')
    WHERE id = 8
```

### **upsert_on_duplicated**
```python
await AccountMgr.upsert_on_duplicated(
    [
        {'id': 7, 'gender': 1, 'name': '斉藤 修平', 'locale': 'ja_JP', 'extend': {}},
        {'id': 8, 'gender': 1, 'name': 'Ojas Salvi', 'locale': 'en_IN', 'extend': {}},
        {'id': 9, 'gender': 1, 'name': '羊淑兰', 'locale': 'zh_CN', 'extend': {}}
    ],
    insert_fields=["id", "gender", "name", "locale", "extend"],
    upsert_fields=["name", "locale"],
)
```
Generate sql and execute
```sql
    INSERT INTO account
        (id, gender, name, locale, extend)
    VALUES
        (7, 1, '斉藤 修平', 'ja_JP', '{}'), (8, 1, 'Ojas Salvi', 'en_IN', '{}'), (9, 1, '羊淑兰', 'zh_CN', '{}')
    AS `new_account`
    ON DUPLICATE KEY UPDATE name=`new_account`.name, locale=`new_account`.locale
```

### **insert_into_select**
```python
await AccountMgr.insert_into_select(
    wheres=[f"id IN (4, 5, 6)"],
    remain_fields=["gender", "locale"],
    assign_field_dict={
        "active": False,
        "name": RawSQL("CONCAT(LEFT(name, 26), ' [NEW]')"),
        "extend": {},
    },
)
```
Generate sql and execute
```sql
    INSERT INTO account
        (gender, locale, active, name, extend)
    SELECT gender, locale, False active, CONCAT(LEFT(name, 26), ' [NEW]') name, '{}' extend
    FROM account
    WHERE id IN (4, 5, 6)
```

### **bulk_update_with_fly_table**
```python
await AccountMgr.bulk_update_with_fly_table(
    [
        {'id': 7, 'active': False, 'gender': <GenderEnum.male: 1>},
        {'id': 15, 'active': True, 'gender': <GenderEnum.unknown: 0>}
    ],
    join_fields=["id"],
    update_fields=["active", "gender"],
)
```
Generate sql and execute
```sql
    UPDATE account
    JOIN (
        SELECT * FROM (
            VALUES
                ROW(7, False, 1), ROW(15, True, 0)
        ) AS fly_table (id, active, gender)
    ) tmp ON account.id = tmp.id
    SET account.active = tmp.active, account.gender = tmp.gender
```
