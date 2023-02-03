# fastapi-efficient-sql

Installed as package by `pip install fastapi-efficient-sql`

Install developing requirements by `pipenv install --skip-lock --dev` or `pip install -r requirements-dev.txt`

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
)
```
Generate sql and execute
```sql
    SELECT
      id, extend ->> '$.last_login.ipv4' ipv4, extend ->> '$.last_login.start_datetime' start_datetime, CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec
    FROM account
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
    FROM account
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
    UPDATE account SET extend =
    JSON_MERGE_PATCH(JSON_SET(JSON_REMOVE(COALESCE(extend, '{}'), '$.deprecated'), '$.last_login',CAST('{"ipv4": "209.182.101.161"}' AS JSON), '$.uuid','fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f'), '{"updated_at": "2022-10-30 21:34:15", "info": {"online_sec": 636}}')
    WHERE `id`=8
```

### **upsert_on_duplicate**
```python
await AccountMgr.upsert_on_duplicate(
    [
        {'id': 7, 'gender': 1, 'name': '斉藤 修平', 'locale': 'ja_JP', 'extend': {}},
        {'id': 8, 'gender': 1, 'name': 'Ojas Salvi', 'locale': 'en_IN', 'extend': {}},
        {'id': 9, 'gender': 1, 'name': '羊淑兰', 'locale': 'zh_CN', 'extend': {}}
    ],
    insert_fields=["id", "gender", "name", "locale", "extend"],
    upsert_fields=["name", "locale"],
    using_values=False,
)
```
Generate sql and execute
```sql
    INSERT INTO account
      (id, gender, name, locale, extend)
    VALUES
      (7, 1, '斉藤 修平', 'ja_JP', '{}'),
      (8, 1, 'Ojas Salvi', 'en_IN', '{}'),
      (9, 1, '羊淑兰', 'zh_CN', '{}')
    AS `new_account` ON DUPLICATE KEY UPDATE name=`new_account`.name, locale=`new_account`.locale
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
    INSERT INTO account_bak
      (gender, locale, active, name, extend)
    SELECT gender, CASE id WHEN 3 THEN 'zh_CN' WHEN 4 THEN 'en_US' WHEN 5 THEN 'fr_FR' ELSE '' END locale, False active, CONCAT(LEFT(name, 26), ' [NEW]') name, '{}' extend
    FROM account
    WHERE `id` IN (4,5,6)
```

### **bulk_update_from_dicts**
```python
await AccountMgr.bulk_update_from_dicts(
    [
        {'id': 7, 'active': False, 'gender': GenderEnum.male},
        {'id': 15, 'active': True, 'gender': GenderEnum.unknown}
    ],
    join_fields=["id"],
    update_fields=["active", "gender"],
    using_values=True,
)
```
Generate sql and execute
```sql
    UPDATE account
    JOIN (
        SELECT * FROM (
          VALUES
          ROW(7, False, 1),
          ROW(15, True, 0)
        ) AS fly_table (id, active, gender)
    ) tmp ON account.id=tmp.id
    SET account.active=tmp.active, account.gender=tmp.gender
```
