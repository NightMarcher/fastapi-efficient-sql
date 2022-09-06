from typing import List

from faker import Faker
from fastapi import APIRouter, Body, Query

from examples.service.constants.enums import LocaleEnum
from examples.service.managers.demo.account import AccountMgr

router = APIRouter()


@router.post("/bulk_init")
async def bulk_init_view():
    dicts = []
    for (idx, locale) in enumerate(LocaleEnum):
        faker = Faker(locale.value)
        dicts.append({
            "id": idx + 1,
            "gender": faker.random_int(0, 2),
            "name": faker.name(),
            "locale": locale.value,
            "extend": {
                "last_login": {
                    "ipv4": faker.ipv4(),
                    "start_datetime": str(faker.past_datetime()),
                    "online_sec": faker.random_int(),
                }
            }
        })
    ok = await AccountMgr.bulk_create_from_dicts(dicts)
    return {"ok": ok}


@router.post("/last_login/query")
async def query_last_login_view(
    account_ids: List[int] = Body(..., embed=True),
):
    dicts = await AccountMgr.query_custom_fields(
        fields=[
            "id", "extend ->> '$.last_login.ipv4' ipv4",
            "extend ->> '$.last_login.start_datetime' start_datetime",
            "CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec"
        ],
        wheres=[f"id IN ({', '.join(map(str, account_ids))})"],
    )
    return dicts


@router.post("/last_login/update")
async def update_last_login_view(
    account_id: int = Query(...),
):
    faker = Faker()
    row_cnt = await AccountMgr.upsert_json(
        json_field="extend",
        path_value_dict={
            "$.last_login": {
                "ipv4": faker.ipv4(),
                "start_datetime": str(faker.past_datetime()),
                "online_sec": faker.random_int(),
            },
            "$.uuid": faker.uuid4(),
        },
        wheres=[f"id = {account_id}"],
    )
    return row_cnt
