from random import randrange

from faker import Faker
from fastapi import APIRouter

from examples.service.constants.enums import LocaleEnum
from examples.service.managers.demo.account import AccountMgr

router = APIRouter()


@router.post("/bulk_init")
async def bulk_init_view(
):
    dicts = []
    for (idx, locale) in enumerate(LocaleEnum):
        faker = Faker(locale.value)
        dicts.append({
            "id": idx + 1,
            "gender": randrange(0, 3),
            "name": faker.name(),
            "locale": locale.value,
            "extend": {
                "last_ipv4": faker.ipv4()
            }
        })
    ok = await AccountMgr.bulk_create_from_dicts(dicts)
    return {"ok": ok}

