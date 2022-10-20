from fastapi_esql import BaseManager

from examples.service.models.demo.account import Account
from examples.service.models.demo.demo_meta import DemoMetaclass


class AccountMgr(BaseManager, metaclass=DemoMetaclass):
    model = Account
