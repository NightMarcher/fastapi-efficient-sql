# fastapi-efficient-sql

Installed as package by `pip install fastapi-efficient-sql`

Install developing requirements by `pyenv local 3.7.9`, `poetry env use 3.7.9`, `poetry shell` and `pip install -r requirements-dev.txt`

Run demo service by `python -m examples.service`

Run unittest by `pytest -sv`

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
aids = [1, 2, 3]

await AccountMgr.select_custom_fields(
    fields=[
        "id", "extend ->> '$.last_login.ipv4' ipv4",
        "extend ->> '$.last_login.start_datetime' start_datetime",
        "CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec"
    ],
    wheres=f"id IN ({','.join(map(str, aids))}) AND gender=1",  # These 4 types of `wheres` are equal
    # wheres=Q(Q(id__in=aids), Q(gender=1), join_type="AND"),
    # wheres={"id__in": aids, "gender": 1},
    # wheres=[Q(id__in=aids), Q(gender=1)],
    index="PRIMARY",
)
```
Generate sql and execute
```sql
    SELECT
      id, extend ->> '$.last_login.ipv4' ipv4, extend ->> '$.last_login.start_datetime' start_datetime, CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec
    FROM `account` FORCE INDEX (`PRIMARY`)
    WHERE id IN (1,2,3) AND gender=1
```

**complex example**
```python
await AccountMgr.select_custom_fields(
    fields=[
        "locale", "gender", "COUNT(1) cnt"
    ],
    wheres=Q(id__range=[1, 12]),
    groups=["locale", "gender"],
    having="cnt > 0",
    orders=["locale", "-gender"],
    offset=0,
    limit=10,
)
```
Generate sql and execute
```sql
    SELECT
      locale, gender, COUNT(1) cnt
    FROM `account`
    WHERE `id` BETWEEN 1 AND 12
    GROUP BY locale, gender
    HAVING cnt > 0
    ORDER BY locale ASC, gender DESC
    LIMIT 0, 10
```

### **update_json_field**
```python
await AccountMgr.update_json_field(
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
)
```
Generate sql and execute
```sql
    UPDATE `account` SET extend =
    JSON_MERGE_PATCH(JSON_SET(JSON_REMOVE(COALESCE(extend, '{}'), '$.deprecated'), '$.last_login',CAST('{"ipv4": "209.182.101.161"}' AS JSON), '$.uuid','fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f'), '{"updated_at": "2022-10-30 21:34:15", "info": {"online_sec": 636}}')
    WHERE `id`=8
```

### **upsert_on_duplicate**
```python
await AccountMgr.upsert_on_duplicate(
    [
        {"id": 10, "gender": 1, "name": "田中 知実", "locale": "ja_JP", "extend": {"rdm": 1}},
        {"id": 11, "gender": 2, "name": "Tara Chadha", "locale": "en_IN", "extend": {"rdm": 10}},
        {"id": 12, "gender": 2, "name": "吴磊", "locale": "zh_CN", "extend": {"rdm": 9}},
    ],
    insert_fields=["id", "gender", "name", "locale", "extend"],
    upsert_fields=["gender", "name"],
    merge_fields=["extend"],
)
```
Generate sql and execute
```sql
    INSERT INTO `account`
      (id, gender, name, locale, extend)
    VALUES
      (10, 1, '田中 知実', 'ja_JP', '{"rdm": 1}'),
      (11, 2, 'Tara Chadha', 'en_IN', '{"rdm": 10}'),
      (12, 2, '吴磊', 'zh_CN', '{"rdm": 9}')
    AS `new_account` ON DUPLICATE KEY UPDATE gender=`new_account`.gender, name=`new_account`.name, extend=JSON_MERGE_PATCH(COALESCE(`account`.extend, '{}'), `new_account`.extend)
```

### **insert_into_select**
```python
await AccountMgr.insert_into_select(
    wheres=Q(id__in=[4, 5, 6]),
    remain_fields=["gender"],
    assign_field_dict={
        "locale": Cases("id", {3: LocaleEnum.zh_CN, 4: LocaleEnum.en_US, 5: LocaleEnum.fr_FR}, default=""),
        "active": False,
        "name": RawSQL("CONCAT(LEFT(name, 26), ' [NEW]')"),
        "extend": {},
    },
    to_table="account_bak",
)
```
Generate sql and execute
```sql
    INSERT INTO `account_bak`
      (gender, locale, active, name, extend)
    SELECT gender, CASE id WHEN 3 THEN 'zh_CN' WHEN 4 THEN 'en_US' WHEN 5 THEN 'fr_FR' ELSE '' END locale, False active, CONCAT(LEFT(name, 26), ' [NEW]') name, '{}' extend
    FROM `account`
    WHERE `id` IN (4,5,6)
```

### **bulk_update_from_dicts**
```python
await AccountMgr.bulk_update_from_dicts(
    [
        {"id": 7, "active": False, "gender": GenderEnum.male, "extend": {"test": 1, "debug": 0}},
        {"id": 15, "active": True, "gender": GenderEnum.unknown, "extend": {"test": 1, "debug": 0}}
    ],
    join_fields=["id"],
    update_fields=["active", "gender"],
    merge_fields=["extend"],
)
```
Generate sql and execute
```sql
    UPDATE `account`
    JOIN (
        SELECT * FROM (
          VALUES
          ROW(7, False, 1, '{"test": 1, "debug": 0}'),
          ROW(15, True, 0, '{"test": 1, "debug": 0}')
        ) AS fly_table (id, active, gender, extend)
    ) tmp ON `account`.id=tmp.id
    SET `account`.active=tmp.active, `account`.gender=tmp.gender, `account`.extend=JSON_MERGE_PATCH(COALESCE(`account`.extend, '{}'), tmp.extend)
```
