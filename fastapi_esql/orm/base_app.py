from abc import ABCMeta


class AppMetaclass(ABCMeta):

    @property
    def ro_conn(self):
        """
        return Tortoise.get_connection("ro_conn")
        """
        if not getattr(self, "get_ro_conn", None):
            raise NotImplementedError(f"Method get_ro_conn() was not implemented by {self.__class__.__name__}!")
        return self.get_ro_conn()

    @property
    def rw_conn(self):
        """
        return Tortoise.get_connection("rw_conn")
        """
        if not getattr(self, "get_rw_conn", None):
            raise NotImplementedError(f"Method get_rw_conn() was not implemented by {self.__class__.__name__}!")
        return self.get_rw_conn()
