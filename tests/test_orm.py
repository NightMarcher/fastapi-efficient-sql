from unittest import TestCase

from tortoise import fields

from examples.service.models.demo import Account
from fastapi_esql import AppMetaclass, BaseManager, BaseModel


class DemoMetaclass(AppMetaclass):

    def get_ro_conn(self):
        return None


class TestOrm(TestCase):
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

    def test_no_conn(self):
        with self.assertRaises(NotImplementedError):
            class AccountMgr(BaseManager, metaclass=DemoMetaclass):
                model = Account
            AccountMgr.rw_conn
