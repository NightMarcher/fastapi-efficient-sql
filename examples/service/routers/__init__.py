from fastapi import APIRouter

from . import account, basic

api_router = APIRouter()

api_router.include_router(basic.router, prefix=f"/basic", tags=["Basic"])
api_router.include_router(account.router, prefix=f"/account", tags=["Account"])
