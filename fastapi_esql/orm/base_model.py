from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):

    created_at = fields.DatetimeField(auto_now_add=True, null=False, index=True)
    updated_at = fields.DatetimeField(auto_now=True, null=False, index=True)
    extend = fields.JSONField(null=False, default={})

    def __str__(self):
        return self.__repr__()

    def to_dict(self):
        return {
            field: getattr(self, field)
            for field in self._meta.db_fields
            if hasattr(self, field)
        }
