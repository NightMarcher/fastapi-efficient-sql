from abc import abstractproperty


class AppMetaclass(type):

    @abstractproperty
    def ro_conn(self):
        """
        return Tortoise.get_connection("ro_conn")
        """
        raise NotImplementedError(f"{self.__class__.__name__}`s property method 'ro_conn' was not implemented!")

    @abstractproperty
    def rw_conn(self):
        """
        return Tortoise.get_connection("rw_conn")
        """
        raise NotImplementedError(f"{self.__class__.__name__}`s property method 'rw_conn' was not implemented!")
