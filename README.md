# fastapi-efficient-sql


### **select_custom_fields**
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
Generated sql
```sql
    SELECT
        id, extend ->> '$.last_login.ipv4' ipv4, extend ->> '$.last_login.start_datetime' start_datetime, CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec
    FROM account
    WHERE id IN (1, 2, 3)
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
Generated sql
```sql
    UPDATE account
    SET extend = JSON_SET(COALESCE(extend, '{}'), '$.last_login', CAST('{"ipv4": "209.182.101.161", "start_datetime": "2022-10-16 11:11:05", "online_sec": 4209}' AS JSON), '$.uuid', 'fd04f7f2-24fc-4a73-a1d7-b6e99a464c5f')
    WHERE id = 8
```

### **upsert_on_duplicated**
```python
await AccountMgr.upsert_on_duplicated(
    [
        {'id': 7, 'gender': 1, 'name': '松田 陽一', 'locale': 'ja_JP', 'extend': {}},
        {'id': 8, 'gender': 2, 'name': 'Zeeshan Kadakia', 'locale': 'en_IN', 'extend': {}},
        {'id': 9, 'gender': 0, 'name': '姜淑珍', 'locale': 'zh_CN', 'extend': {}}
    ],
    insert_fields=["id", "gender", "name", "locale", "extend"],
    upsert_fields=["name", "locale"],
)
```
Generated sql
```sql
    INSERT INTO account
        (id, gender, name, locale, extend)
    VALUES
        (7, 1, '松田 陽一', 'ja_JP', '{}'), (8, 2, 'Zeeshan Kadakia', 'en_IN', '{}'), (9, 0, '姜淑珍', 'zh_CN', '{}')
    ON DUPLICATE KEY UPDATE name=VALUES(name), locale=VALUES(locale)
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
Generated sql
```sql
    INSERT INTO account
        (gender, locale, active, name, extend)
    SELECT gender, locale, False active, CONCAT(LEFT(name, 26), ' [NEW]') name, '{}' extend
    FROM account
    WHERE id IN (4, 5, 6)
```