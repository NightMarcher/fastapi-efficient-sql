from fastapi_esql.orm.base_app import AppMetaclass
from tortoise import Tortoise


class DemoMetaclass(AppMetaclass):

    @property
    def ro_conn(self):
        return Tortoise.get_connection("demo_ro")

    @property
    def rw_conn(self):
        return Tortoise.get_connection("demo_rw")
