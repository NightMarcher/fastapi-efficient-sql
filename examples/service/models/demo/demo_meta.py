from fastapi_esql import AppMetaclass
from tortoise import Tortoise


class DemoMetaclass(AppMetaclass):

    def get_ro_conn(self):
        return Tortoise.get_connection("demo_ro")

    def get_rw_conn(self):
        return Tortoise.get_connection("demo_rw")
