from fastapi_esql.orm.base_manager import BaseManager

from examples.service.models.demo.account import Account
from examples.service.models.demo.demo_meta import DemoMetaclass


class AccountMgr(BaseManager, metaclass=DemoMetaclass):
    obj = Account
