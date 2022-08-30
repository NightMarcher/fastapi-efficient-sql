from fastapi_esql.orm.base_model import BaseModel, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from examples.service.constants.enums import GenderEnum, LocaleEnum


class Account(BaseModel):
    id = fields.IntField(pk=True)
    active = fields.BooleanField(null=False, default=True)
    gender = fields.IntEnumField(GenderEnum, null=False, default=GenderEnum.unknown)
    name = fields.CharField(max_length=10, null=False, default="")
    locale = fields.CharEnumField(LocaleEnum, max_length=5, null=False)


AccountIn = pydantic_model_creator(Account, name="AccountIn", exclude=("active"), exclude_readonly=True)