from unittest import TestCase

from tortoise import fields

from examples.service.models.demo import Account
from fastapi_esql import AppMetaclass, BaseManager, BaseModel


class DemoMetaclass(AppMetaclass):

    def get_ro_conn(self):
        return None


class TestORM(TestCase):

    def test_no_model(self):
        with self.assertRaises(NotImplementedError):
            class AccountMgr(BaseManager, metaclass=DemoMetaclass):
                ...

    def test_model_without_table(self):
        with self.assertRaises(NotImplementedError):
            class MyModel(BaseModel):
                id = fields.IntField(pk=True)

            class AccountMgr(BaseManager, metaclass=DemoMetaclass):
                model = MyModel

    def test_ro_conn(self):
        class AccountMgr(BaseManager, metaclass=DemoMetaclass):
            model = Account
        AccountMgr.ro_conn

    def test_no_rw_conn(self):
        with self.assertRaises(NotImplementedError):
            class AccountMgr(BaseManager, metaclass=DemoMetaclass):
                model = Account
            AccountMgr.rw_conn
