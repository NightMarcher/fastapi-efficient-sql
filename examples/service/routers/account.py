from logging import getLogger
from typing import List

from faker import Faker
from fastapi import APIRouter, Body, Query
from fastapi_esql.utils.sqlizer import RawSQL
from pydantic import BaseModel, Field

from examples.service.constants.enums import GenderEnum, LocaleEnum
from examples.service.managers.demo.account import AccountMgr

router = APIRouter()
logger = getLogger(__name__)


@router.post("/create")
async def create_view():
    faker = Faker(LocaleEnum.zh_CN.value)
    account = await AccountMgr.create_from_dict({
        "gender": faker.random_int(0, 2),
        "name": faker.name(),
        "locale": LocaleEnum.zh_CN.value,
    })
    return {"account": account}


@router.post("/update")
async def update_view(
    aid: int = Query(...),
):
    account = await AccountMgr.get_by_pk(aid)
    if not account:
        return {"found": False, "ok": False}

    faker = Faker(account.locale)
    ok = await AccountMgr.update_from_dict(account, {
        "gender": faker.random_int(0, 2),
        "name": faker.name(),
    })
    return {"found": True, "ok": ok}


@router.get("/query/by_id")
async def query_by_id_view(
    aid: int = Query(...),
):
    account = await AccountMgr.get_by_pk(aid)
    return {"account": account}


@router.post("/query/group_by_locale")
async def query_group_by_locale_view(
):
    dicts = await AccountMgr.select_custom_fields(
        fields=[
            "locale", "gender", "COUNT(1) cnt"
        ],
        wheres=["id BETWEEN 1 AND 12"],
        groups=["locale", "gender"],
        orders=["locale", "-gender"],
        limit=10,
    )
    return {"dicts": dicts}


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
    # logger.debug(dicts)
    ok = await AccountMgr.bulk_create_from_dicts(
        dicts,
        batch_size=5,
        # ignore_conflicts=True,
        update_fields=["gender", "name", "locale"],
        on_conflict=["id"],
    )
    return {"ok": ok}


@router.post("/last_login/query")
async def query_last_login_view(
    aids: List[int] = Body(..., embed=True),
):
    dicts = await AccountMgr.select_custom_fields(
        fields=[
            "id", "extend ->> '$.last_login.ipv4' ipv4",
            "extend ->> '$.last_login.start_datetime' start_datetime",
            "CAST(extend ->> '$.last_login.online_sec' AS SIGNED) online_sec"
        ],
        wheres=[f"id IN ({', '.join(map(str, aids))})"],
    )
    return {"dicts": dicts}


@router.post("/last_login/update")
async def update_last_login_view(
    aid: int = Query(...),
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
        wheres=[f"id = {aid}"],
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
async def bulk_clone_view(
    aids: List[int] = Body(..., embed=True),
):
    ok = await AccountMgr.insert_into_select(
        wheres=[f"id IN ({', '.join(map(str, aids))})"],
        remain_fields=["gender", "locale"],
        assign_field_dict={
            "active": False,
            "name": RawSQL("CONCAT(LEFT(name, 26), ' [NEW]')"),
            "extend": {},
        },
    )
    return {"ok": ok}


class UpdateIn(BaseModel):
    id: int = Field(...)
    active: bool = Field(...)
    gender: GenderEnum = Field(...)

@router.post("/bulk_update")
async def bulk_update_view(
    dicts: List[UpdateIn] = Body(..., embed=True),
):
    row_cnt = await AccountMgr.bulk_update_with_fly_table(
        [d.dict() for d in dicts],
        join_fields=["id"],
        update_fields=["active", "gender"],
    )
    return {"row_cnt": row_cnt}
