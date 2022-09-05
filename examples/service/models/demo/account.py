from fastapi_esql.orm.base_model import BaseModel, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from examples.service.constants.enums import GenderEnum, LocaleEnum


class Account(BaseModel):
    """
    CREATE TABLE `account` (
        `id` int unsigned NOT NULL AUTO_INCREMENT,
        `active` bool NOT NULL DEFAULT true,
        `gender` tinyint unsigned NOT NULL DEFAULT 0 COMMENT '0:unknown, 1:male, 2:female',
        `name` varchar(32) NOT NULL DEFAULT '',
        `locale` varchar(5) NOT NULL,
        `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `extend` json NOT NULL,
        PRIMARY KEY (`id`),
        KEY `created_at-idx` (`created_at`),
        KEY `updated_at-idx` (`updated_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    id = fields.IntField(pk=True)
    active = fields.BooleanField(null=False, default=True)
    gender = fields.IntEnumField(GenderEnum, null=False, default=GenderEnum.unknown)
    name = fields.CharField(max_length=32, null=False, default="")
    locale = fields.CharEnumField(LocaleEnum, max_length=5, null=False)

    class Meta:
        app = "demo"
        table = "account"


AccountIn = pydantic_model_creator(Account, name="AccountIn", exclude=("active"), exclude_readonly=True)
