import logging
from typing import List

from faker import Faker
from fastapi import APIRouter, Body, Query
from fastapi_esql.utils.sqlizer import RawSQL

from examples.service.constants.enums import LocaleEnum
from examples.service.managers.demo.account import AccountMgr

router = APIRouter()
logger = logging.getLogger(__name__)


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
    logger.debug(dicts)
    ok = await AccountMgr.bulk_create_from_dicts(dicts)
    return {"ok": ok}


@router.post("/last_login/query")
async def query_last_login_view(
    account_ids: List[int] = Body(..., embed=True),
):
    dicts = await AccountMgr.select_custom_fields(
        fields=[
            "id", "extend ->> '$.last_login.ipv4' ipv4",
            "extend ->> '$.last_login.start_datetime' start_datetime",
            "CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec"
        ],
        wheres=[f"id IN ({', '.join(map(str, account_ids))})"],
    )
    return {"dicts": dicts}


@router.post("/last_login/update")
async def update_last_login_view(
    account_id: int = Query(...),
):
    faker = Faker()
    row_cnt = await AccountMgr.upsert_json_field(
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
    return {"row_cnt": row_cnt}


@router.post("/bulk_upsert")
async def bulk_upsert_view():
    dicts = []
    for (idx, locale) in enumerate([LocaleEnum.ja_JP, LocaleEnum.en_IN, LocaleEnum.zh_CN], 7):
        faker = Faker(locale)
        dicts.append({
            "id": idx,
            "gender": faker.random_int(0, 2),
            "name": faker.name(),
            "locale": locale.value,
            "extend": {},
        })
    logger.debug(dicts)
    row_cnt = await AccountMgr.upsert_on_duplicated(
        dicts,
        insert_fields=["id", "gender", "name", "locale", "extend"],
        upsert_fields=["name", "locale"],
    )
    return {"row_cnt": row_cnt}


@router.post("/bulk_clone")
async def clone_account_view(
    account_ids: List[int] = Body(..., embed=True),
):
    ok = await AccountMgr.insert_into_select(
        wheres=[f"id IN ({', '.join(map(str, account_ids))})"],
        remain_fields=["gender", "locale"],
        assign_field_dict={
            "active": False,
            "name": RawSQL("CONCAT(LEFT(name, 26), ' [NEW]')"),
            "extend": {},
        },
    )
    return {"ok": ok}
