from fastapi import APIRouter

from examples.service.managers.demo.account import AccountMgr
from examples.service.models.demo.account import AccountIn

router = APIRouter()


@router.post("/one")
async def create_account_view(
    account: AccountIn
):
    params = account.dict()
    print(params)
    obj = await AccountMgr.create_from_dict(params)
    print(obj)
    if not obj:
        return
    return obj.to_dict()
