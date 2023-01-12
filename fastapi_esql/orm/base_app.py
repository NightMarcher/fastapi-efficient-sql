from abc import ABCMeta


class AppMetaclass(ABCMeta):

    def __new__(cls, name, bases, attrs):
        if name != "BaseManager":
            model = attrs.get("model")
            if not model:
                raise NotImplementedError(f"Class attribute `model` was not defined by {name}!")

            table = getattr(model.Meta, "table", None)
            if not table:
                raise NotImplementedError(f"Meta attribute `table` was not defined by model {model.__name__}!")

            attrs["table"] = model.Meta.table
        return super().__new__(cls, name, bases, attrs)

    @property
    def ro_conn(self):
        """
        return Tortoise.get_connection("ro_conn")
        """
        if not getattr(self, "get_ro_conn", None):
            raise NotImplementedError(f"Method `get_ro_conn()` was not implemented by {self.__class__.__name__}!")
        return self.get_ro_conn()

    @property
    def rw_conn(self):
        """
        return Tortoise.get_connection("rw_conn")
        """
        if not getattr(self, "get_rw_conn", None):
            raise NotImplementedError(f"Method `get_rw_conn()` was not implemented by {self.__class__.__name__}!")
        return self.get_rw_conn()
