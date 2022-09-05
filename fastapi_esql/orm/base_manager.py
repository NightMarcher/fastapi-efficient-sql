import traceback
from typing import List

from .base_app import AppMetaclass
from .base_model import BaseModel


class BaseManager(metaclass=AppMetaclass):

    obj = BaseModel

    @classmethod
    async def create_from_dict(cls, params):
        params["using_db"] = cls.rw_conn
        try:
            return await cls.obj.create(**params)
        except Exception as e:
            traceback.print_exc()
            return None

    @classmethod
    async def bulk_create_from_dicts(cls, dicts: List[dict]) -> bool:
        try:
            print(dicts)
            await cls.obj.bulk_create(
                objects=[cls.obj(**d) for d in dicts],
                using_db=cls.rw_conn,
            )
            return True
        except Exception as e:
            return False
